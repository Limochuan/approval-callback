import requests
from app.services.lark_client import get_app_access_token


# 飞书开放平台基础地址
LARK_BASE_URL = "https://open.larksuite.com"


def get_approval_instance(instance_code: str) -> dict:
    """
    根据 instance_code 调用飞书审批 v4 接口，获取完整审批实例数据
    """

    if not instance_code:
        raise ValueError("instance_code 不能为空")

    token = get_app_access_token()

    url = f"{LARK_BASE_URL}/open-apis/approval/v4/instances/{instance_code}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    resp = requests.get(url, headers=headers, timeout=10)

    # 打印完整响应，方便定位问题
    print("\n==== 飞书审批实例接口返回 ====")
    print("请求 URL:", url)
    print("HTTP 状态码:", resp.status_code)
    print("响应 Header:", resp.headers)
    print("原始响应内容:", repr(resp.text))
    print("================================\n")

    # HTTP 状态码校验
    if resp.status_code != 200:
        raise RuntimeError(
            f"审批实例接口请求失败，HTTP 状态码={resp.status_code}，返回内容={resp.text}"
        )

    # Content-Type 校验
    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("application/json"):
        raise RuntimeError(
            f"飞书接口返回非 JSON 内容，Content-Type={content_type}，内容={resp.text}"
        )

    # JSON 解析
    try:
        payload = resp.json()
    except Exception as e:
        raise RuntimeError(
            f"审批实例接口 JSON 解析失败，错误={e}，原始内容={resp.text}"
        )

    # 飞书业务 code 校验
    if payload.get("code") != 0:
        raise RuntimeError(
            f"飞书接口业务错误，code={payload.get('code')}，msg={payload.get('msg')}"
        )

    # v4 接口真实数据在 data 字段中
    return payload.get("data", {})
