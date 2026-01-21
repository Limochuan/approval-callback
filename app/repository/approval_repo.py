"""
审批数据写入数据库的仓储层（Repository）

职责说明：
1. 只负责 MySQL 数据写入 / 更新
2. 不关心 FastAPI / HTTP / 飞书校验
3. 不做业务判断，不解析 JSON 结构
4. 所有方法由 service 层调用
"""

import json
from typing import Dict, List, Any

from app.db.mysql import get_conn


class ApprovalRepository:
    """
    审批数据仓储类
    """

    def __init__(self):
        """
        初始化数据库连接
        """
        self.conn = get_conn()

    # =========================
    # 1. 原始审批数据（兜底）
    # =========================
    def save_raw_data(self, instance_code: str, raw_data: Dict[str, Any]):
        sql = """
        INSERT INTO lark_approval_raw (
            instance_code,
            raw_json
        )
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            raw_json = VALUES(raw_json)
        """

        with self.conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    instance_code,
                    json.dumps(raw_data, ensure_ascii=False),
                ),
            )

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
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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

    # =========================
    # 3. 审批任务 / 节点
    # =========================
    def save_tasks(self, instance_code: str, tasks: List[Dict[str, Any]]):
        if not tasks:
            return

        sql = """
        INSERT INTO lark_approval_task (
            instance_code,
            task_id,
            node_name,
            node_type,
            status,
            user_id,
            start_time,
            end_time
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),
            end_time = VALUES(end_time)
        """

        with self.conn.cursor() as cursor:
            for task in tasks:
                cursor.execute(
                    sql,
                    (
                        instance_code,
                        task.get("task_id"),
                        task.get("node_name"),
                        task.get("node_type"),
                        task.get("status"),
                        task.get("user_id"),
                        task.get("start_time"),
                        task.get("end_time"),
                    ),
                )

    # =========================
    # 4. 表单字段数据
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
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            field_value = VALUES(field_value)
        """

        with self.conn.cursor() as cursor:
            for field in fields:
                cursor.execute(
                    sql,
                    (
                        instance_code,
                        field.get("field_id"),
                        field.get("field_name"),
                        field.get("field_type"),
                        field.get("field_value"),
                    ),
                )
