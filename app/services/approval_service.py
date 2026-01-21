"""
审批业务编排层（Service）

职责：
1. 接收回调 payload（至少 instance_code）
2. 调用飞书审批 API 获取完整审批实例
3. 解析 form 字段
4. 写入数据库（raw / instance / tasks / form_fields / field_kv）
"""

import json
from typing import Dict, Any, List, Optional

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

        # 5. 保存表单字段（原始 form）
        form_fields = self._normalize_form(approval_instance.get("form"))
        self.repo.save_form_fields(instance_code, form_fields)

        # 6. ✅ 保存 KV 拆解字段
        kv_rows = self._build_field_kv_rows(
            instance_code=instance_code,
            form_raw=approval_instance.get("form"),
        )
        if kv_rows:
            self.repo.save_field_kv(kv_rows)

    def process_instance_code(self, instance_code: str) -> None:
        """
        只传 instance_code 的简化入口
        """
        self.process_callback({"instance_code": instance_code})

    # ------------------------------------------------------------------
    # instance 表
    # ------------------------------------------------------------------

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

            "applicant_user_id": approval_instance.get("user_id"),
            "department_id": approval_instance.get("department_id"),

            "start_time": approval_instance.get("start_time"),
            "end_time": approval_instance.get("end_time"),

            "create_time": approval_instance.get("start_time"),
            "update_time": approval_instance.get("end_time")
            or approval_instance.get("start_time"),
        }

    # ------------------------------------------------------------------
    # form 原表
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_form(form_raw) -> List[Dict[str, Any]]:
        """
        把飞书 form 字段解析为 lark_approval_form_field
        """
        if not form_raw:
            return []

        if isinstance(form_raw, str):
            try:
                form_list = json.loads(form_raw)
            except json.JSONDecodeError:
                return []
        elif isinstance(form_raw, list):
            form_list = form_raw
        else:
            return []

        result: List[Dict[str, Any]] = []

        for f in form_list:
            result.append({
                "field_id": f.get("id"),
                "field_name": f.get("name"),
                "field_type": f.get("type"),
                "field_value": json.dumps(f.get("value"), ensure_ascii=False),
            })

        return result

    # ------------------------------------------------------------------
    # KV 拆解表（lark_approval_field_kv）
    # ------------------------------------------------------------------

    def _build_field_kv_rows(
        self,
        instance_code: str,
        form_raw,
    ) -> List[Dict[str, Any]]:
        """
        把飞书 form 拆解成 KV 行
        """
        form_list = self._parse_form(form_raw)
        if not form_list:
            return []

        rows: List[Dict[str, Any]] = []

        for field in form_list:
            widget_id = field.get("id")
            field_name = field.get("name")
            field_type = field.get("type")
            value = field.get("value")

            # 明细行（如表格控件）
            row_id = field.get("row_id")

            text_value, num_value, currency = self._extract_value(value)

            rows.append({
                "approval_id": instance_code,
                "row_id": row_id,
                "widget_id": widget_id,

                "field_name": field_name,
                "field_type": field_type,

                "field_value_text": text_value,
                "field_value_num": num_value,
                "currency": currency,

                "extra_json": json.dumps(value, ensure_ascii=False),
            })

        return rows

    @staticmethod
    def _parse_form(form_raw) -> List[Dict[str, Any]]:
        if not form_raw:
            return []

        if isinstance(form_raw, str):
            try:
                return json.loads(form_raw)
            except json.JSONDecodeError:
                return []

        if isinstance(form_raw, list):
            return form_raw

        return []

    @staticmethod
    def _extract_value(value) -> tuple[Optional[str], Optional[float], Optional[str]]:
        """
        根据 value 类型拆解 text / number / currency
        """
        if value is None:
            return None, None, None

        # 金额
        if isinstance(value, dict):
            if "amount" in value:
                return (
                    str(value.get("amount")),
                    float(value.get("amount")),
                    value.get("currency"),
                )
            # 其它结构 → 直接转字符串
            return json.dumps(value, ensure_ascii=False), None, None

        # 数值
        if isinstance(value, (int, float)):
            return str(value), float(value), None

        # 字符串
        if isinstance(value, str):
            return value, None, None

        # 数组 / 其它
        return json.dumps(value, ensure_ascii=False), None, None
