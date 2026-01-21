from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback

from app.services.approval_service import get_approval_instance
from app.utils.approval_parser import parse_approval_form

# FastAPI 路由对象，main.py 就是 import 的这个
router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    """
    飞书审批回调入口
    """
    try:
        # 读取回调原始 JSON
        data = await request.json()

        print("\n==== 收到审批回调（原始） ====")
        print(data)
        print("=================================\n")

        approval_code = data.get("approval_code")
        instance_code = data.get("instance_code")
        status = data.get("status")
        event_type = data.get("type")
        uuid = data.get("uuid")

        print("event_type:", event_type)
        print("status:", status)
        print("approval_code:", approval_code)
        print("instance_code:", instance_code)
        print("uuid:", uuid)
        print("=================================\n")

        if not instance_code:
            raise ValueError("instance_code 为空，无法拉取审批实例")

        # 二次拉取完整审批实例
        approval_instance = get_approval_instance(instance_code)

        print("\n==== 审批实例完整数据（飞书 API 返回） ====")
        print(approval_instance)
        print("==========================================\n")

        # 解析 form 字段为 dict
        form_raw = approval_instance.get("form")
        form_data = parse_approval_form(form_raw)

        print("\n==== 审批表单字段（解析后） ====")
        print(form_data)
        print("================================\n")

        # 这里以后可以：
        # - 写数据库
        # - 对接 ERP / Dynamics
        # - 推送 Teams / 飞书消息

        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("\n==== 回调处理异常 ====")
        print(e)
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "msg": "callback error",
                "error": str(e)
            }
        )
