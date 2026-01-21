"""
审批业务编排层（Service）

职责：
1. 接收回调 payload（至少 instance_code）
2. 调用飞书审批 API 获取完整审批实例
3. 解析 form 字段
4. 写入数据库（raw / instance / tasks / form_fields）
"""

import json
from typing import Dict, Any, List

from app.services.lark_approval_api import get_approval_instance
from app.repository.approval_repo import ApprovalRepository


class ApprovalService:
    """
    审批业务服务：拉取 → 解析 → 入库
    """

    def __init__(self):
        self.repo = ApprovalRepository()

    def process_callback(self, callback_payload: Dict[str, Any]) -> None:
        """
        处理飞书审批回调
        """
        instance_code = callback_payload.get("instance_code")
        if not instance_code:
            raise ValueError("回调数据缺少 instance_code")

        # 1. 拉取完整审批实例
        approval_instance = get_approval_instance(instance_code)

        # 2. 保存 raw（兜底，完整 JSON）
        self.repo.save_raw_data(instance_code, approval_instance)

        # 3. 保存审批实例主表
        instance_row = self._build_instance_row(approval_instance)
        self.repo.save_instance(instance_row)

        # 4. 保存任务节点
        task_list = approval_instance.get("task_list") or []
        self.repo.save_tasks(instance_code, task_list)

        # 5. 保存表单字段
        form_fields = self._normalize_form(approval_instance.get("form"))
        self.repo.save_form_fields(instance_code, form_fields)

    def process_instance_code(self, instance_code: str) -> None:
        """
        只传 instance_code 的简化入口
        """
        self.process_callback({"instance_code": instance_code})

    @staticmethod
    def _build_instance_row(approval_instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        构建 lark_approval_instance 表字段
        """
        return {
            "instance_code": approval_instance.get("instance_code"),
            "approval_code": approval_instance.get("approval_code"),
            "approval_name": approval_instance.get("approval_name"),
            "status": approval_instance.get("status"),

            # ✅ 关键修正：这两个字段之前根本没传
            "applicant_user_id": approval_instance.get("user_id"),
            "department_id": approval_instance.get("department_id"),

            "start_time": approval_instance.get("start_time"),
            "end_time": approval_instance.get("end_time"),

            "create_time": approval_instance.get("start_time"),
            "update_time": approval_instance.get("end_time")
            or approval_instance.get("start_time"),
        }

    @staticmethod
    def _normalize_form(form_raw) -> List[Dict[str, Any]]:
        """
        把飞书 form 字段解析为数据库需要的结构
        """
        if not form_raw:
            return []

        # 1. form 反序列化
        if isinstance(form_raw, str):
            try:
                form_list = json.loads(form_raw)
            except json.JSONDecodeError:
                return []
        elif isinstance(form_raw, list):
            form_list = form_raw
        else:
            return []

        # 2. 转换为表字段结构
        result: List[Dict[str, Any]] = []

        for f in form_list:
            result.append({
                "field_id": f.get("id"),
                "field_name": f.get("name"),
                "field_type": f.get("type"),
                # value 统一存 JSON，避免结构不一致
                "field_value": json.dumps(f.get("value"), ensure_ascii=False),
            })

        return result
