import requests
from app.services.lark_client import get_app_access_token

LARK_APPROVAL_INSTANCE_URL = (
    "https://open.larksuite.com/open-apis/approval/v4/instances/get"
)

def get_approval_instance(instance_code: str) -> dict:
    token = get_app_access_token()

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    resp = requests.post(
        LARK_APPROVAL_INSTANCE_URL,
        headers=headers,
        json={"instance_code": instance_code}
    )

    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"Get approval instance failed: {data}")

    return data["data"]
