# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import warnings
import logging
import json
import requests
import os
from typing import Dict, List, Optional, Tuple
from pikerag.workflows.common import BaseQaData
from pikerag.workflows.deepsearcher.configuration import Configuration, init_config
from pikerag.workflows.deepsearcher.offline_loading import load_from_local_files
from pikerag.workflows.deepsearcher.online_query import query
from pikerag.workflows.qa import QaWorkflow
from requests.exceptions import Timeout

# 忽略一些警告
warnings.filterwarnings("ignore", r".*TypedStorage is deprecated.*")
warnings.filterwarnings("ignore", r".*Relevance scores must be between 0 and 1.*")
warnings.filterwarnings("ignore", r".*No relevant docs were retrieved using the relevance score threshold 0.5.*")

def get_embeddings_m3(message):
    if "HTTP_PROXY" in os.environ and "HTTPS_PROXY" in os.environ:
        os.environ.pop("HTTP_PROXY", None)
        os.environ.pop("HTTPS_PROXY", None)

    data = {
        "message": message
    }
    data = json.dumps(data)
    headers = {
        "Content-Type": "application/json",
    }
    parsed_data = requests.post('http://192.168.50.179:4005/gpt', data=data, headers=headers)
    print(f'get_embeddings_m3返回 ===================== {parsed_data}')

    json_data = json.loads(parsed_data.text)
    num_list = json_data['encoded_input']
    return num_list

class DeepResearchWorkflow(QaWorkflow):
    def __init__(self, config: Dict):
        """初始化DeepResearch工作流程
        
        Args:
            config: 配置字典，包含所有必要的设置
        """
        super().__init__(config)
        
        # 初始化DeepResearch配置
        self.deep_config = Configuration()
        
        # 设置embedding模型 - 直接硬编码配置
        self.deep_config.set_provider_config(
            feature="embedding",
            provider="CustomEmbedding",
            provider_configs={
                "embedding_function": get_embeddings_m3,
                "dimension": 1024,
                "batch_size": 1
            }
        )
            
        # 设置LLM模型

        # import importlib
        # llm_module = importlib.import_module(config["llm_client"]["module_path"])
        # llm_class = getattr(llm_module, config["llm_client"]["class_name"])
        #
        # # 创建LLM客户端实例
        # llm_instance = llm_class(**config["llm_client"].get("args", {}))

        # 设置为CustomLLM，使用CompanyLLMClient的generate_content_with_messages方法作为llm_function
        def llm_wrapper(prompt, history=None,):
            messages = [{"role": "user", "content": prompt}]
            if history:
                messages = history + messages
            return self._client.generate_content_with_messages(messages, **self.llm_config)

        self.deep_config.set_provider_config(
            feature="llm",
            provider="CustomLLM",  # 这里使用CustomLLM作为provider
            provider_configs={
                "llm_function": llm_wrapper,  # 使用包装后的方法
                "max_tokens": config["llm_client"]["llm_config"].get("max_tokens", 3000),
                "temperature": config["llm_client"]["llm_config"].get("temperature", 0.2)
            }
        )
            
        # 设置向量数据库 - 直接硬编码配置
        self.deep_config.set_provider_config(
            feature="vector_db",
            provider="Milvus",
            provider_configs={
                "uri": "http://192.168.50.179:19530",
            }
        )
            
        # 设置查询参数 - 直接硬编码配置
        self.deep_config.query_settings.update({
            "max_iter": 3,
            "chunk_size": 500,
            "chunk_overlap": 50,
            "language": "zh"
        })
            
        # 初始化配置
        init_config(config=self.deep_config)

        
    def load_knowledge(self, paths_or_directory: List[str], collection_name: Optional[str] = None, 
                      collection_description: Optional[str] = None, force_new_collection: bool = False) -> None:
        """加载知识到向量数据库"""
        load_from_local_files(
            paths_or_directory=paths_or_directory,
            collection_name=collection_name,
            collection_description=collection_description,
            force_new_collection=force_new_collection
        )

    def answer(self, qa_data: BaseQaData, round_idx: int = 0) -> str:
        """回答单个问题
        
        Args:
            qa_data: 问答数据对象
            round_idx: 轮次索引
            
        Returns:
            答案字符串
        """
        answer, _, _ = self.run_query(qa_data.question)
        return answer
        
    def run_query(self, question: str) -> Tuple[str, List, int]:
        """运行查询"""
        return query(question)
        
    def run(self) -> None:
        """运行工作流程"""
        # 加载知识库
        if "knowledge_base" in self.config:
            kb_config = self.config["knowledge_base"]
            self.load_knowledge(
                paths_or_directory=kb_config["paths"],
                collection_name=kb_config.get("collection_name"),
                collection_description=kb_config.get("collection_description"),
                force_new_collection=kb_config.get("force_new_collection", False)
            )