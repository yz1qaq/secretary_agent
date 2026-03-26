from dataclasses import dataclass

'''
这个类用于存在LLM的配置信息，包括api_key, base_url, model_name
'''

@dataclass
class LLMConfig:
    api_key: str 
    base_url: str
    model_name: str 

    def validate(self):
        if not self.api_key:
            raise ValueError("api_key is required")
        if not self.base_url:
            raise ValueError("base_url is required")
        if not self.model_name:
            raise ValueError("model_name is required")

    def to_dict(self) -> dict:
        """转成字典，便于传给客户端"""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "model_name": self.model_name
        }

def creat_config(api_key:str,base_url:str,model_name:str) -> LLMConfig:
    return LLMConfig(api_key=api_key, base_url=base_url, model_name=model_name)


