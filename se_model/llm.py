from langchain_openai import ChatOpenAI
import os
from  .llm_config import creat_config

def creat_llm(llm_config):
    if llm_config.validate():
        raise ValueError("LLMConfig is invalid")
    llm = ChatOpenAI(
        api_key=llm_config.api_key,
        base_url=llm_config.base_url,
        model=llm_config.model_name
    )
    return llm



if __name__ == "__main__":
    api_key = os.getenv("DASHSCOPE_API_KEY")
    base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    model_name = "qwen3.5-plus"
    llm_config = creat_config(api_key=api_key, base_url=base_url, model_name=model_name)
    qwen_llm = creat_llm(llm_config)
    print(qwen_llm.invoke("你好").content)


