import os
# 示例代码仅供参考，请勿在生产环境中直接使用
import sys
from this import d
import traceback
from pathlib import Path

from Tea import request, response
from alibabacloud_bailian20231229 import models as bailian_20231229_models
from alibabacloud_bailian20231229.client import Client as bailian20231229Client
from alibabacloud_tea_openapi import models as open_api_models
from alibabacloud_tea_util import models as util_models
from alibabacloud_tea_util.client import Client as UtilClient
from langchain_core.callbacks import file
from mcp.server.fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.logger import get_project_logger

acess_key = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID")
acess_key_secret = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET")
workspace_id = os.getenv("WORKSPACE_ID")
rag_id = "o0mbnxv9x0"
category_id = "cate_8908e1f6a2904249a968cd2454a379fb_12188330"


mcp = FastMCP()
logger = get_project_logger("rag_mcp", "rag_mcp.log")


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

from alibabacloud_bailian20231229 import models as bailian_20231229_models

# 申请文件上传租约
def apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id):
    """
    从阿里云百炼服务申请文件上传租约。

    参数:
        client (bailian20231229Client): 阿里云百炼客户端。
        category_id (str): 类别 ID。
        file_name (str): 文件名称。
        file_md5 (str): 文件的 MD5 哈希值。
        file_size (int): 文件大小（以字节为单位）。
        workspace_id (str): 业务空间 ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.ApplyFileUploadLeaseRequest(
        file_name=file_name,
        md_5=file_md5,
        size_in_bytes=file_size,
    )
    runtime = util_models.RuntimeOptions()
    return client.apply_file_upload_lease_with_options(category_id, workspace_id, request, headers, runtime)

import hashlib

def calculate_md5(file_path: str) -> str:
    """
    计算文件的 MD5 哈希值。

    参数:
        file_path (str): 文件路径。

    返回:
        str: 文件的 MD5 哈希值。
    """
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def get_file_info(file_path):
    """
    获取指定文件的名称、MD5哈希值和大小。

    参数:
        file_path (str): 文件的完整路径。

    返回:
        tuple: (file_name, file_md5, file_size)
    """

    # 获取文件名
    file_name = os.path.basename(file_path)

    # 获取文件大小（字节）
    file_size = os.path.getsize(file_path)

    # 计算MD5哈希值
    file_md5 = calculate_md5(file_path)

    return file_name, file_md5, file_size

def apply_lease_by_file_path(client, category_id, workspace_id, file_path):
    file_name, file_md5, file_size = get_file_info(file_path)
    #print(file_name, file_md5, file_size)
    
    return apply_lease(client, category_id, file_name, file_md5, file_size, workspace_id)

import requests
def upload_file_to_bailian(upload_url, headers, file_path):
    """
    将文件上传到阿里云百炼服务。

    参数:
        lease_id (str): 租约 ID。
        upload_url (str): 上传 URL。
        headers (dict): 上传请求的头部。
        file_path (str): 文件路径。
    """
    with open(file_path, 'rb') as f:
        file_content = f.read()
    upload_headers = {
        "X-bailian-extra": headers["X-bailian-extra"],
        "Content-Type": headers["Content-Type"]
    }
    response = requests.put(upload_url, data=file_content, headers=upload_headers)
    print(response.status_code)
    response.raise_for_status()




def add_file_to_bailian_category(client, lease_id: str, parser: str, category_id: str, workspace_id: str):
    """
    将文件添加到阿里云百炼指定类目。

    参数:
        client: 阿里云百炼客户端。
        lease_id (str): 租约 ID。
        parser (str): 用于文件的解析器。
        category_id (str): 类别 ID。
        workspace_id (str): 业务空间 ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.AddFileRequest(
        lease_id=lease_id,
        parser=parser,
        category_id=category_id,
    )
    runtime = util_models.RuntimeOptions()
    return client.add_file_with_options(workspace_id, request, headers, runtime)


from alibabacloud_tea_util import models as util_models


def describe_file(client, workspace_id, file_id):
    """
    获取文档的基本信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        file_id (str): 文档ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    runtime = util_models.RuntimeOptions()
    return client.describe_file_with_options(workspace_id, file_id, headers, runtime)

def upload_rag_file_to_bailian(client,workspace_id,category_id,file_path):
    lease = apply_lease_by_file_path(client,category_id,workspace_id,file_path)
    headers=lease.body.data.param.headers
    lease_id = lease.body.data.file_upload_lease_id
    upload_url = lease.body.data.param.url

    add_file_res = add_file_to_bailian_category(client,lease_id,"DASHSCOPE_DOCMIND",category_id,workspace_id)
    file_id = add_file_res.body.data.file_id

    des_file_res = describe_file(client,workspace_id,file_id)

    print("添加文件状态")
    print("body",des_file_res.body)
    print("-"*50)

    return des_file_res

    

def create_index(client, workspace_id, file_id, name, structure_type, source_type, sink_type):
    """
    在阿里云百炼服务中创建知识库（初始化）。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        file_id (str): 文档ID。
        name (str): 知识库名称。
        structure_type (str): 知识库的数据类型。
        source_type (str): 应用数据的数据类型，支持类目类型和文档类型。
        sink_type (str): 知识库的向量存储类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    request = bailian_20231229_models.CreateIndexRequest(
        structure_type=structure_type,
        name=name,
        source_type=source_type,
        sink_type=sink_type,
        document_ids=[file_id]
    )
    runtime = util_models.RuntimeOptions()
    return client.create_index_with_options(workspace_id, request, headers, runtime)

def submit_index(client, workspace_id, index_id):
    """
    向阿里云百炼服务提交索引任务。

    参数:
        client (bailian20231229Client): 阿里云百炼客户端。
        workspace_id (str): 业务空间 ID。
        index_id (str): 索引 ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    submit_index_job_request = bailian_20231229_models.SubmitIndexJobRequest(
        index_id=index_id
    )
    runtime = util_models.RuntimeOptions()
    return client.submit_index_job_with_options(workspace_id, submit_index_job_request, headers, runtime)

def get_index_job_status(client, workspace_id, index_id, job_id):
    """
    查询索引任务状态。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        job_id (str): 任务ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    get_index_job_status_request = bailian_20231229_models.GetIndexJobStatusRequest(
        index_id=index_id,
        job_id=job_id
    )
    runtime = util_models.RuntimeOptions()
    return client.get_index_job_status_with_options(workspace_id, get_index_job_status_request, headers, runtime)


def list_indices(client, workspace_id):
    """
    获取指定业务空间下一个或多个知识库的详细信息。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    list_indices_request = bailian_20231229_models.ListIndicesRequest()
    runtime = util_models.RuntimeOptions()
    return client.list_indices_with_options(workspace_id, list_indices_request, headers, runtime)

def submit_index_add_documents_job(client, workspace_id, index_id, file_id, source_type):
    """
    向一个非结构化知识库追加导入已解析的文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。
        source_type(str): 数据类型。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    submit_index_add_documents_job_request = bailian_20231229_models.SubmitIndexAddDocumentsJobRequest(
        index_id=index_id,
        document_ids=[file_id],
        source_type=source_type
    )
    runtime = util_models.RuntimeOptions()
    return client.submit_index_add_documents_job_with_options(workspace_id, submit_index_add_documents_job_request, headers, runtime)


def delete_index_document(client, workspace_id, index_id, file_id):
    """
    从指定的非结构化知识库中永久删除一个或多个文档。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。
        file_id (str): 文档ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    delete_index_document_request = bailian_20231229_models.DeleteIndexDocumentRequest(
        index_id=index_id,
        document_ids=[file_id]
    )
    runtime = util_models.RuntimeOptions()
    return client.delete_index_document_with_options(workspace_id, delete_index_document_request, headers, runtime)

def delete_index(client, workspace_id, index_id):
    """
    永久性删除指定的知识库。

    参数:
        client (bailian20231229Client): 客户端（Client）。
        workspace_id (str): 业务空间ID。
        index_id (str): 知识库ID。

    返回:
        阿里云百炼服务的响应。
    """
    headers = {}
    delete_index_request = bailian_20231229_models.DeleteIndexRequest(
        index_id=index_id
    )
    runtime = util_models.RuntimeOptions()
    return client.delete_index_with_options(workspace_id, delete_index_request, headers, runtime)




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
        logger.error("retrieve_rag failed: missing required environment variables")
        return ""
    try:
        # print("步骤1：创建Client")
        client = create_client(acess_key, acess_key_secret)
        # print("步骤2：检索知识库")
        index_id = rag_id  # 即 CreateIndex 接口返回的 Data.Id，您也可以在阿里云百炼控制台的知识库页面获取。
        query = question
        logger.info("retrieve_rag request: query=%s", query)
        resp = retrieve_index(client, workspace_id, index_id, query)
        # result = UtilClient.to_jsonstring(resp.body)
        if resp.body.data.nodes[0].text:
            result = resp.body.data.nodes[0].text
            logger.info("retrieve_rag success: query=%s result=%s", query, result[:160])
            return result
        else:
            logger.warning("retrieve_rag empty result: query=%s", query)
            return ""
    except Exception as e:
        logger.error(
            "retrieve_rag exception: query=%s error=%s\n%s",
            question,
            str(e),
            traceback.format_exc(),
        )
        return ""
 



if __name__ == "__main__":
    mcp.run(transport="stdio")
