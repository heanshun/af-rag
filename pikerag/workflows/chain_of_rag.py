from typing import Dict, List, Tuple

from pikerag.workflows.qa import QaWorkflow
from pikerag.workflows.common import BaseQaData
from pikerag.utils.config_loader import load_protocol
from pikerag.utils.logger import Logger
from pikerag.prompts.deepsearcher.chain_of_rag import intermediate_api_answer_template


def process_reference_chunks(reference_chunks):
    apis = []
    documents = []
    for chunk in reference_chunks:
        try:
            chunk_dict = eval(chunk) if isinstance(chunk, str) else chunk
            if chunk_dict['node_type'] == 'api':
                # 解析matched_content中的API信息
                api_info = eval(chunk_dict['matched_content'])
                apis.append(api_info)
            else:
                # 对于文档，直接使用matched_content
                documents.append(chunk_dict['matched_content'])
        except Exception as e:
            print(f"处理chunk时出错: {e}")
            continue
        
    return apis, documents


class ChainOfRAGWorkflow(QaWorkflow):
    def __init__(self, yaml_config: Dict) -> None:
        super().__init__(yaml_config)
        
        workflow_configs: dict = self._yaml_config["workflow"].get("args", {})
        self._max_iter: int = workflow_configs.get("max_iter", 4)
        self._init_protocol()

    def _init_protocol(self) -> None:
        # 初始化三个主要的协议
        self._followup_protocol = load_protocol(
            module_path=self._yaml_config["followup_protocol"]["module_path"],
            protocol_name=self._yaml_config["followup_protocol"]["protocol_name"],
            partial_values=self._yaml_config["followup_protocol"].get("template_partial", {}),
        )
        
        self._intermediate_api_protocol = load_protocol(
            module_path=self._yaml_config["intermediate_api_protocol"]["module_path"],
            protocol_name=self._yaml_config["intermediate_api_protocol"]["protocol_name"],
            partial_values=self._yaml_config["intermediate_api_protocol"].get("template_partial", {}),
        )
        
        self._intermediate_protocol = load_protocol(
            module_path=self._yaml_config["intermediate_protocol"]["module_path"],
            protocol_name=self._yaml_config["intermediate_protocol"]["protocol_name"],
            partial_values=self._yaml_config["intermediate_protocol"].get("template_partial", {}),
        )
        
        self._final_protocol = load_protocol(
            module_path=self._yaml_config["final_protocol"]["module_path"],
            protocol_name=self._yaml_config["final_protocol"]["protocol_name"],
            partial_values=self._yaml_config["final_protocol"].get("template_partial", {}),
        )

    def _reflect_get_subquery(self, query: str, intermediate_context: List[str]) -> Tuple[str, int]:
        """生成下一个子查询"""
        messages = self._followup_protocol.process_input(query, intermediate_context=intermediate_context)
        response = self._client.generate_content_with_messages(messages, **self.llm_config)
        result = self._followup_protocol.parse_output(response)
        return result, 0

    def get_node_types(self, reference_chunks):
        types = []
        for chunk in reference_chunks:
            try:
                # 因为chunk是字符串形式的字典，需要先转换成字典
                chunk_dict = eval(chunk)
                types.append(chunk_dict['node_type'])
            except Exception as e:
                print(f"处理chunk时出错: {e}")
                continue
        return types

    def _retrieve_and_answer(self, query: str, retrieve_id: str) -> Tuple[str, List[str], int]:
        """检索并回答子查询"""
        # 检索相关文档
        qa = BaseQaData(question=query)
        reference_chunks = self._retriever.retrieve_contents(qa, retrieve_id=retrieve_id)
        apis, documents = process_reference_chunks(reference_chunks)

        # 使用intermediate_api_protocol处理
        messages = self._intermediate_api_protocol.process_input(
            query, 
            retrieved_documents=documents,
            available_apis=apis
        )
        response = self._client.generate_content_with_messages(messages, **self.llm_config)
        result = self._intermediate_api_protocol.parse_output(response)
        
        # 如果决定使用API
        if result.get("use_api", False):
            api_index = result.get("selected_api_index", -1)
            parameters = result.get("parameters", {})
            # TODO: 实现API调用逻辑
            return "获取数据失败", reference_chunks, 0
        
        # 如果不使用API
        return result["intermediate_answer"], reference_chunks, 0

    def answer(self, qa: BaseQaData, question_idx: int) -> Dict:
        """实现chain-of-thought RAG策略的问答过程"""
        intermediate_contexts = []
        all_retrieved_chunks = []
        token_usage = 0
        
        # 迭代进行子查询和回答
        for iter_idx in range(self._max_iter):
            # 生成子查询
            followup_query, n_token0 = self._reflect_get_subquery(qa.question, intermediate_contexts)
            
            # 检索并回答子查询
            intermediate_answer, chunks, n_token1 = self._retrieve_and_answer(
                followup_query, 
                retrieve_id=f"Q{question_idx}-Sub{iter_idx}"
            )
            
            # 更新上下文和统计信息
            all_retrieved_chunks.extend(chunks)
            intermediate_idx = len(intermediate_contexts) + 1
            intermediate_contexts.append(
                f"Intermediate query{intermediate_idx}: {followup_query}\n"
                f"Intermediate answer{intermediate_idx}: {intermediate_answer}"
            )
            token_usage += n_token0 + n_token1
            
            # 如果没有找到相关信息，继续下一轮
            if "No relevant information found" in intermediate_answer:
                continue
        
        # 生成最终答案
        messages = self._final_protocol.process_input(
            qa.question,
            retrieved_documents=all_retrieved_chunks,
            intermediate_context=intermediate_contexts
        )
        response = self._client.generate_content_with_messages(messages, **self.llm_config)
        result = self._final_protocol.parse_output(response)
        final_answer = result
        token_usage += 0
        
        return {
            "answer": final_answer,
            "intermediate_contexts": intermediate_contexts,
            "retrieved_chunks": all_retrieved_chunks,
            "token_usage": token_usage
        } 