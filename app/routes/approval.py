from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback

from app.services.approval_service import get_approval_instance

router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    try:
        # 读取飞书回调原始数据
        data = await request.json()

        print("\n==== 收到审批回调（原始） ====")
        print(data)
        print("================================\n")

        # 回调中的关键字段
        approval_code = data.get("approval_code")
        instance_code = data.get("instance_code")
        status = data.get("status")          # APPROVED / REJECTED
        tenant_key = data.get("tenant_key")
        event_type = data.get("type")
        uuid = data.get("uuid")

        print("approval_code:", approval_code)
        print("instance_code:", instance_code)
        print("status:", status)
        print("event_type:", event_type)
        print("uuid:", uuid)

        # instance_code 是后续查询审批详情的关键
        if not instance_code:
            raise ValueError("回调数据中缺少 instance_code")

        # 调用飞书接口，拉取完整审批实例
        approval_instance = get_approval_instance(instance_code)

        print("\n==== 审批实例完整数据（API 拉取） ====")
        print(approval_instance)
        print("====================================\n")

        # 审批表单数据（后续业务真正要用的）
        form = approval_instance.get("form", [])

        print("\n==== 审批表单 form 字段 ====")
        for item in form:
            print(item)
        print("================================\n")

        # 当前阶段不做业务处理，只确认链路完整
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
