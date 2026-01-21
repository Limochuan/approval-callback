from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback

from app.services.approval_service import get_approval_instance

router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    try:
        #读取回调原始数据
        data = await request.json()

        print("\n==== 收到审批回调（原始） ====")
        print(data)
        print("================================\n")

        #===== 审批事件基础字段 =====
        approval_code = data.get("approval_code")
        instance_code = data.get("instance_code")
        status = data.get("status")          # APPROVED / REJECTED
        operate_time = data.get("operate_time")
        tenant_key = data.get("tenant_key")
        event_type = data.get("type")
        uuid = data.get("uuid")

        print("approval_code:", approval_code)
        print("instance_code:", instance_code)
        print("status:", status)
        print("event_type:", event_type)
        print("uuid:", uuid)

        #===== 关键：用 instance_code 再拉一次完整审批实例 =====
        if not instance_code:
            raise ValueError("instance_code is missing in callback data")

        approval_instance = get_approval_instance(instance_code)

        print("\n==== 审批实例完整数据（API 拉取） ====")
        print(approval_instance)
        print("====================================\n")

        #===== 审批表单数据（你真正要的）=====
        form = approval_instance.get("form", [])

        print("\n==== 审批表单 form 字段 ====")
        for item in form:
            print(item)
        print("================================\n")

        #现在先不做任何业务处理
        # 后续：
        # - 解析 form → dict
        # - 写数据库
        # - 推送 Teams / ERP / OA / Dynamics

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
