"""
审批数据写入数据库的仓储层（Repository）

职责：
1. 只负责 MySQL 数据写入 / 更新
2. 不做业务判断
3. 不解析 JSON 结构
"""

import json
from typing import Dict, List, Any
from app.db.mysql import get_conn


class ApprovalRepository:

    def __init__(self):
        self.conn = get_conn()

    # =========================
    # 1. 原始审批数据
    # =========================
    def save_raw_data(self, instance_code: str, raw_data: Dict[str, Any]):
        sql = """
        INSERT INTO lark_approval_raw (
            instance_code,
            approval_code,
            status,
            event_type,
            raw_json
        )
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            event_type = VALUES(event_type),
            raw_json = VALUES(raw_json)
        """

        with self.conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    instance_code,
                    raw_data.get("approval_code"),
                    raw_data.get("status"),
                    "approval_instance",
                    json.dumps(raw_data, ensure_ascii=False),
                ),
            )
        self.conn.commit()

    # =========================
    # 2. 审批实例主表
    # =========================
    def save_instance(self, instance: Dict[str, Any]):
        sql = """
        INSERT INTO lark_approval_instance (
            instance_code,
            approval_code,
            approval_name,
            status,
            applicant_user_id,
            department_id,
            start_time,
            end_time,
            create_time,
            update_time
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            end_time = VALUES(end_time),
            update_time = VALUES(update_time)
        """

        with self.conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    instance.get("instance_code"),
                    instance.get("approval_code"),
                    instance.get("approval_name"),
                    instance.get("status"),
                    instance.get("applicant_user_id"),
                    instance.get("department_id"),
                    instance.get("start_time"),
                    instance.get("end_time"),
                    instance.get("create_time"),
                    instance.get("update_time"),
                ),
            )
        self.conn.commit()

    # =========================
    # 3. 审批任务节点
    # =========================
    def save_tasks(self, instance_code: str, tasks: List[Dict[str, Any]]):
        if not tasks:
            return

        sql = """
        INSERT INTO lark_approval_task (
            task_id,
            instance_code,
            node_id,
            node_name,
            node_type,
            user_id,
            open_id,
            status,
            start_time,
            end_time
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            end_time = VALUES(end_time)
        """

        with self.conn.cursor() as cursor:
            for task in tasks:
                cursor.execute(
                    sql,
                    (
                        task.get("id"),
                        instance_code,
                        task.get("node_id"),
                        task.get("node_name"),
                        task.get("type"),
                        task.get("user_id"),
                        task.get("open_id"),
                        task.get("status"),
                        task.get("start_time"),
                        task.get("end_time"),
                    ),
                )
        self.conn.commit()

    # =========================
    # 4. 表单字段
    # =========================
    def save_form_fields(self, instance_code: str, fields: List[Dict[str, Any]]):
        if not fields:
            return

        sql = """
        INSERT INTO lark_approval_form_field (
            instance_code,
            field_id,
            field_name,
            field_type,
            field_value
        )
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            field_value = VALUES(field_value)
        """

        with self.conn.cursor() as cursor:
            for field in fields:
                cursor.execute(
                    sql,
                    (
                        instance_code,
                        field["field_id"],
                        field["field_name"],
                        field["field_type"],
                        field["field_value"],
                    ),
                )
        self.conn.commit()
