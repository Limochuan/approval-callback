import requests

from app.services.lark_client import get_app_access_token


# 飞书开放平台基础地址
LARK_BASE_URL = "https://open.larksuite.com"


def get_approval_instance(instance_code: str) -> dict:
    """
    根据 instance_code 调用飞书审批 v4 接口，获取完整的审批实例数据

    :param instance_code: 审批实例 ID（由回调事件提供）
    :return: 审批实例完整数据（dict）
    """

    # 基础参数校验，防止无意义调用
    if not instance_code:
        raise ValueError("instance_code 不能为空")

    # 获取 app_access_token
    # 这里依赖 lark_client.py 中已经实现并验证通过的逻辑
    token = get_app_access_token()

    # 飞书审批实例查询接口（v4）
    url = f"{LARK_BASE_URL}/open-apis/approval/v4/instances/{instance_code}"

    # 请求头，必须携带 Authorization
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # 发送 GET 请求
    resp = requests.get(url, headers=headers, timeout=10)

    # ===== 调试日志（建议在开发阶段保留） =====
    # 这里的目的是：
    # 1. 明确是否真的请求到了飞书
    # 2. 确认返回状态码
    # 3. 确认返回内容是否为标准 JSON
    print("\n==== 飞书审批实例接口返回 ====")
    print("请求 URL:", url)
    print("HTTP 状态码:", resp.status_code)
    print("响应 Header:", resp.headers)
    print("原始响应内容:", repr(resp.text))
    print("================================\n")

    # ===== HTTP 状态码校验 =====
    # 飞书接口正常情况下应返回 200
    if resp.status_code != 200:
        raise RuntimeError(
            f"审批实例接口请求失败，HTTP 状态码={resp.status_code}，返回内容={resp.text}"
        )

    # ===== Content-Type 校验 =====
    # 防止飞书返回 HTML / 文本错误页面，却被误当成 JSON 解析
    content_type = resp.headers.get("Content-Type", "")
    if not content_type.startswith("application/json"):
        raise RuntimeError(
            f"飞书接口返回非 JSON 内容，Content-Type={content_type}，内容={resp.text}"
        )

    # ===== JSON 解析 =====
    # 这里必须使用 try-except，防止 JSONDecodeError 直接炸服务
    try:
        payload = resp.json()
    except Exception as e:
        raise RuntimeError(
            f"审批实例接口 JSON 解析失败，错误={e}，原始内容={resp.text}"
        )

    # ===== 飞书业务返回结构校验 =====
    # 飞书 OpenAPI 统一返回结构：
    # {
    #   "code": 0,
    #   "msg": "success",
    #   "data": {...}
    # }
    if payload.get("code") != 0:
        raise RuntimeError(
            f"飞书接口业务错误，code={payload.get('code')}，msg={payload.get('msg')}"
        )

    # v4 接口的真实业务数据在 payload["data"] 中
    return payload.get("data", {})
