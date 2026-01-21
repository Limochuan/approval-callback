from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime

router = APIRouter()

@router.post("/approval/callback")
async def approval_callback(request: Request):
    try:
        data = await request.json()

        print("==== 收到审批回调 ====")
        print(data)
        print("=====================")

        approval_id = data.get("approval_id")
        instance_code = data.get("instance_code")
        status = data.get("status")
        approved_at = data.get("approved_at")
        operator = data.get("operator")
        form_data = data.get("form_data")

        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("回调处理异常:", e)
        return JSONResponse(
            status_code=500,
            content={"code": -1, "msg": str(e)}
        )
