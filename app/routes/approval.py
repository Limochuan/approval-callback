from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback

router = APIRouter()

@router.post("/approval/callback")
async def approval_callback(request: Request):
    try:
        data = await request.json()

        print("==== 收到审批回调 ====")
        print(data)
        print("=====================")

        # ===== 基础字段（审批实例级）=====
        approval_code = data.get("approval_code")
        instance_code = data.get("instance_code")
        status = data.get("status")          # APPROVED / REJECTED
        operate_time = data.get("operate_time")
        tenant_key = data.get("tenant_key")
        event_type = data.get("type")
        uuid = data.get("uuid")

        # ===== 这里先兜底打印，防止结构不一致 =====
        print("approval_code:", approval_code)
        print("instance_code:", instance_code)
        print("status:", status)

        # 注意：Lark 审批字段不一定在第一层
        # 后面我们会通过接口再拉一次完整表单数据

        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("==== 回调处理异常 ====")
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
