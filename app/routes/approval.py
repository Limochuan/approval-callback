from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
import datetime
import traceback
import json

from app.services.approval_service import get_approval_instance

router = APIRouter()


@router.post("/approval/callback")
async def approval_callback(request: Request):
    """
    飞书审批回调入口
    - 接收飞书推送的审批事件
    - 根据 instance_code 再次调用飞书接口，拉取完整审批实例
    - 当前阶段仅做日志打印和链路验证，不做业务处理
    """
    try:
        # 读取飞书回调的原始 JSON 数据
        data = await request.json()

        print("\n==== 收到审批回调（原始数据） ====")
        print(json.dumps(data, ensure_ascii=False, indent=2))
        print("=================================\n")

        # 回调中携带的基础字段
        approval_code = data.get("approval_code")
        instance_code = data.get("instance_code")
        status = data.get("status")          # APPROVED / REJECTED
        event_type = data.get("type")
        uuid = data.get("uuid")

        print("approval_code:", approval_code)
        print("instance_code:", instance_code)
        print("status:", status)
        print("event_type:", event_type)
        print("uuid:", uuid)

        # instance_code 是后续查询审批详情的关键字段
        if not instance_code:
            raise ValueError("回调数据中缺少 instance_code")

        # 根据 instance_code 调用飞书接口，获取完整审批实例
        approval_instance = get_approval_instance(instance_code)

        print("\n==== 审批实例完整数据（飞书 API 返回） ====")
        print(json.dumps(approval_instance, ensure_ascii=False, indent=2))
        print("==========================================\n")

        # 审批表单数据（真正业务会用到的部分）
        form = approval_instance.get("form", [])

        print("\n==== 审批表单字段（结构化打印） ====")
        for item in form:
            field_name = item.get("name")
            field_type = item.get("type")
            field_value = item.get("value")

            print(f"字段名: {field_name}")
            print(f"字段类型: {field_type}")
            print(f"字段值: {field_value}")
            print("------")
        print("====================================\n")

        # 当前阶段不做任何业务处理，只返回成功给飞书
        return JSONResponse(
            status_code=200,
            content={
                "code": 0,
                "msg": "received",
                "timestamp": datetime.datetime.now().isoformat()
            }
        )

    except Exception as e:
        print("\n==== 审批回调处理异常 ====")
        print(str(e))
        traceback.print_exc()

        return JSONResponse(
            status_code=500,
            content={
                "code": -1,
                "msg": "callback error",
                "error": str(e)
            }
        )
