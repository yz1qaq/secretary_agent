import os
# 示例代码仅供参考，请勿在生产环境中直接使用

from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from mcp.server.fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

acess_key = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
acess_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
workspace_id = os.getenv("WORKSPACE_ID")
rag_id = "0v4nc7kund"


mcp = FastMCP()


def check_environment_variables():
    """检查并提示设置必要的环境变量"""
    required_vars = {
        "ALIBABA_CLOUD_ACCESS_KEY_ID": acess_key,
        "ALIBABA_CLOUD_ACCESS_KEY_SECRET": acess_key_secret,
        "WORKSPACE_ID": workspace_id,
    }
    missing_vars = []
    for var, description in required_vars.items():
        if not os.environ.get(var):
            missing_vars.append(var)
            print(f"错误：请设置 {var} 环境变量 ({description})")

    return len(missing_vars) == 0


def create_client(access_key_id, access_key_secret) -> bailian20231229Client:
    """
    创建并配置客户端（Client）。

    返回:
        bailian20231229Client: 配置好的客户端（Client）。
    """
    config = open_api_models.Config(
        access_key_id=access_key_id, access_key_secret=access_key_secret
    )
    # 下方接入地址以公有云的公网接入地址为例，可按需更换接入地址。
    config.endpoint = "bailian.cn-beijing.aliyuncs.com"
    return bailian20231229Client(config)


def retrieve_index(client, workspace_id, index_id, query):
    """
    在指定的知识库中检索信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        query (str): 检索query。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    retrieve_request = bailian_20231229_models.RetrieveRequest(
        index_id=index_id, query=query
    )
    runtime = util_models.RuntimeOptions()
    return client.retrieve_with_options(
        workspace_id, retrieve_request, headers, runtime
    )


@mcp.tool(name="retrieve_rag", description="使用阿里云百炼服务检索知识库")
def retrieve_rag(
    question: Annotated[str, Field(description="要检索的问题或查询")],
) -> str:
    """
    使用阿里云百炼服务检索知识库。

    参数:
        question (str): 要检索的问题或查询。

    返回:
        str or None: 如果成功，返回检索召回的文本切片；否则返回 None。
    """
    if not check_environment_variables():
        print("环境变量校验未通过。")
        return None
    try:
        # print("步骤1：创建Client")
        client = create_client(acess_key, acess_key_secret)
        # print("步骤2：检索知识库")
        index_id = rag_id  # 即 CreateIndex 接口返回的 Data.Id，您也可以在阿里云百炼控制台的知识库页面获取。
        query = question
        resp = retrieve_index(client, workspace_id, index_id, query)
        # result = UtilClient.to_jsonstring(resp.body)
        if resp.body.data.nodes[0].text:
            return resp.body.data.nodes[0].text
        else:
            return None
    except Exception as e:
        print(f"发生错误：{e}")
        return None


if __name__ == "__main__":
    mcp.run(transport="stdio")
