# PIKE-RAG 项目扩展

## 项目简介

本项目是基于[PIKE-RAG](https://github.com/PIKE-RAG)的开源项目进行的二次开发。我们在原有框架的基础上，整合了自定义的工作流程，以提升检索增强生成(RAG)系统的性能和实用性。

## 主要特点

- 基于PIKE-RAG的核心功能
- 自定义工作流程优化
- [更多特点待补充]

## 工作流程

我们对原有的PIKE-RAG系统进行了以下改进：

系统支持以下三种工作模式：

### 1. 批量测试模式

通过运行`test_answer.py`，结合`question.txt`中的问题进行批量测试：

```bash
python -m tests.pikerag.workflows.test_answer tests\pikerag\workflows\qa\mongodb_qa_retriever.yml 0
```
### 2. 交互式问答模式

启动交互式问答界面，支持实时对话：

```bash
python -m tests.pikerag.workflows.test_answer_interactive
```

### 3. Web应用模式

启动Web界面，提供可视化的问答窗口和配置管理：

```bash
python -m tests.pikerag.workflows.web_app
```
## 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

## 许可证

[待补充许可证信息]
