from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import os
import uvicorn
import datetime

app = FastAPI(title="Approval Callback Service")

@app.get("/")
def health_check():
    return {"status": "ok"}

@app.post("/approval/callback")
async def approval_callback(request: Request):
    try:
        data = await request.json()

        # 打印日志（第一次一定要有）
        print("==== 收到审批回调 ====")
        print(data)
        print("=====================")

        # 示例：你最常用的字段
        approval_id = data.get("approval_id")
        instance_code = data.get("instance_code")
        status = data.get("status")
        approved_at = data.get("approved_at")
        operator = data.get("operator")
        form_data = data.get("form_data")

        # TODO（以后你要干的事）
        # 1. 写数据库
        # 2. 调 ERP / OA / Dynamics
        # 3. 更新订单 / 采购 / 合同状态

        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("❌ 回调处理异常：", str(e))
        return JSONResponse(
            status_code=500,
            content={"code": 500, "msg": str(e)}
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

