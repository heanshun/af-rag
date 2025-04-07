import os
from typing import List, Dict
import jsonlines
from tqdm import tqdm

from pikerag.workflows.qa import QaWorkflow
from pikerag.workflows.common import BaseQaData
from pikerag.utils.logger import Logger

class DeepResearchWorkflow(QaWorkflow):
    def __init__(self, yaml_config: dict) -> None:
        super().__init__(yaml_config)
        # 初始化深度研究相关的配置
        self._init_research_components()
    
    def _init_research_components(self) -> None:
        """初始化深度研究所需的额外组件"""
        # 创建研究过程记录器
        self._research_logger = Logger(
            name="research_process",
            dump_folder=os.path.join(self._yaml_config["log_dir"], "research"),
        )
        # 设置深度研究的参数
        self._research_config = self._yaml_config.get("research_config", {})
        self._max_research_depth = self._research_config.get("max_depth", 3)
        self._min_confidence_threshold = self._research_config.get("min_confidence", 0.8)
    
    def _conduct_deep_research(self, qa: BaseQaData, question_idx: int) -> Dict:
        """执行深度研究过程"""
        research_findings = []
        current_depth = 0
        
        # 初始问题分析
        initial_analysis = self._analyze_question(qa.question)
        research_findings.append({"depth": current_depth, "type": "initial_analysis", "content": initial_analysis})
        
        while current_depth < self._max_research_depth:
            # 获取当前深度的参考资料
            reference_chunks = self._retriever.retrieve_contents(
                qa, 
                retrieve_id=f"Q{question_idx:03}_D{current_depth}"
            )
            
            # 生成深入研究问题
            research_questions = self._generate_research_questions(
                qa.question, 
                research_findings,
                reference_chunks
            )
            
            # 对每个研究问题进行探索
            for sub_q in research_questions:
                sub_answer = self._explore_sub_question(sub_q, reference_chunks)
                research_findings.append({
                    "depth": current_depth + 1,
                    "type": "sub_research",
                    "question": sub_q,
                    "answer": sub_answer
                })
            
            # 评估是否需要继续深入研究
            confidence_score = self._evaluate_research_confidence(research_findings)
            if confidence_score >= self._min_confidence_threshold:
                break
                
            current_depth += 1
        
        # 整合研究发现
        final_answer = self._synthesize_findings(research_findings)
        
        # 记录研究过程
        self._research_logger.info({
            "question_idx": question_idx,
            "original_question": qa.question,
            "research_process": research_findings,
            "final_answer": final_answer
        })
        
        return {
            "answer": final_answer,
            "research_findings": research_findings,
            "research_depth": current_depth
        }
    
    def _analyze_question(self, question: str) -> Dict:
        """分析初始问题，识别关键概念和研究方向"""
        messages = self._qa_protocol.process_input(
            content=f"请用中文分析以下问题，识别关键概念和需要研究的方向：\n{question}",
            references=[],
        )
        response = self._client.generate_content_with_messages(messages)
        try:
            return self._qa_protocol.parse_output(response)
        except Exception as e:
            return {
                "answer": "无法完成分析",
                "rationale": f"处理过程出现错误: {str(e)}"
            }
    
    def _generate_research_questions(self, original_question: str, findings: List, references: List[str]) -> List[str]:
        """基于当前发现生成深入研究问题"""
        context = {
            "original_question": original_question,
            "current_findings": findings,
        }
        messages = self._qa_protocol.process_input(
            content="请用中文生成需要深入探索的子问题",
            references=references,
            **context
        )
        response = self._client.generate_content_with_messages(messages)
        try:
            output = self._qa_protocol.parse_output(response)
            return [output.get("answer", "需要进一步研究")]
        except Exception:
            return ["需要进一步研究"]
    
    def _explore_sub_question(self, question: str, references: List[str]) -> Dict:
        """探索子问题"""
        messages = self._qa_protocol.process_input(
            content=question,
            references=references
        )
        response = self._client.generate_content_with_messages(messages)
        return self._qa_protocol.parse_output(response)
    
    def _evaluate_research_confidence(self, findings: List) -> float:
        """评估当前研究的置信度"""
        messages = self._qa_protocol.process_input(
            content="评估当前研究发现的完整性和置信度",
            references=[str(findings)]
        )
        response = self._client.generate_content_with_messages(messages)
        output = self._qa_protocol.parse_output(response)
        return float(output.get("confidence", 0.0))
    
    def _synthesize_findings(self, findings: List) -> str:
        """整合所有研究发现，生成最终答案"""
        valid_findings = [f for f in findings if f.get("content") and not isinstance(f["content"], str)]
        
        messages = self._qa_protocol.process_input(
            content="请用中文总结所有研究发现，生成最终答案",
            references=[str(valid_findings)]
        )
        response = self._client.generate_content_with_messages(messages)
        try:
            output = self._qa_protocol.parse_output(response)
            return output.get("answer", "无法生成有效答案")
        except Exception:
            return "处理答案时发生错误"
    
    def answer(self, qa: BaseQaData, question_idx: int) -> dict:
        """重写answer方法，使用深度研究流程"""
        return self._conduct_deep_research(qa, question_idx)
    
class simpledeepResearchWorkflow(DeepResearchWorkflow):
    def run(self) -> None:
        """深度研究的QA测试流程，调用answer方法并打印详细的研究结果。"""
        for question_idx, qa in enumerate(self._testing_suite):
            output_dict = self.answer(qa, question_idx)
            print(f"问题 {question_idx + 1}:")
            print(f"问题内容: {qa.question}")
            print(f"研究深度: {output_dict['research_depth']}")
            print(f"最终答案: {output_dict['answer']}")
            print("\n研究过程:")
            for finding in output_dict['research_findings']:
                print(f"- 深度 {finding['depth']}: {finding['type']}")
                if finding['type'] == 'initial_analysis':
                    print(f"  分析结果: {finding['content']}")
                elif finding['type'] == 'sub_research':
                    print(f"  子问题: {finding['question']}")
                    print(f"  发现: {finding['answer']}")
            print("-" * 50) 