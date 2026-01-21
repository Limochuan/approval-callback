"""
审批数据写入数据库的仓储层（Repository）

职责：
- 只负责 MySQL 的 INSERT / UPDATE
- 不做任何业务判断
- 不解析、不重组 JSON
- 上层给什么，这里就存什么
"""

import json  # 用于将 dict 序列化为 JSON 字符串
from typing import Dict, List, Any  # 类型注解，仅用于可读性和 IDE 提示
from app.db.mysql import get_conn  # 获取 MySQL 数据库连接


class ApprovalRepository:
    """审批数据仓储类，专职负责数据库写入"""

    def __init__(self):
        # 初始化时获取一个数据库连接
        # 所有方法共用该连接
        self.conn = get_conn()

    # =========================
    # 1. 原始审批数据表
    # =========================
    def save_raw_data(self, instance_code: str, raw_data: Dict[str, Any]):
        """
        保存审批实例的原始 JSON 数据
        - instance_code：审批实例唯一标识
        - raw_data：Lark 返回的完整审批数据
        """

        sql = """
        INSERT INTO lark_approval_raw (
            instance_code,      -- 审批实例 code（唯一键）
            approval_code,      -- 审批定义 code
            status,             -- 审批状态
            event_type,         -- 事件类型（固定值）
            raw_json            -- 原始 JSON 数据
        )
        VALUES (%s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),          -- 实例状态更新
            event_type = VALUES(event_type),  -- 事件类型更新
            raw_json = VALUES(raw_json)       -- 原始 JSON 覆盖更新
        """

        # 使用游标执行 SQL
        with self.conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    instance_code,                         # 审批实例 code
                    raw_data.get("approval_code"),         # 审批定义 code
                    raw_data.get("status"),                # 审批状态
                    "approval_instance",                   # 固定事件类型
                    json.dumps(raw_data, ensure_ascii=False),  # JSON 序列化
                ),
            )

        # 提交事务
        self.conn.commit()

    # =========================
    # 2. 审批实例主表
    # =========================
    def save_instance(self, instance: Dict[str, Any]):
        """
        保存审批实例基础信息
        - instance：已经解析好的实例字段字典
        """

        sql = """
        INSERT INTO lark_approval_instance (
            instance_code,       -- 审批实例 code
            approval_code,       -- 审批定义 code
            approval_name,       -- 审批名称
            status,              -- 当前状态
            applicant_user_id,   -- 申请人用户 ID
            department_id,       -- 申请人部门 ID
            start_time,          -- 审批开始时间
            end_time,            -- 审批结束时间
            create_time,         -- 创建时间
            update_time          -- 更新时间
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),          -- 状态更新
            end_time = VALUES(end_time),      -- 结束时间更新
            update_time = VALUES(update_time) -- 更新时间更新
        """

        with self.conn.cursor() as cursor:
            cursor.execute(
                sql,
                (
                    instance.get("instance_code"),       # 实例 code
                    instance.get("approval_code"),       # 审批 code
                    instance.get("approval_name"),       # 审批名称
                    instance.get("status"),              # 状态
                    instance.get("applicant_user_id"),   # 申请人
                    instance.get("department_id"),       # 部门
                    instance.get("start_time"),          # 开始时间
                    instance.get("end_time"),            # 结束时间
                    instance.get("create_time"),         # 创建时间
                    instance.get("update_time"),         # 更新时间
                ),
            )

        self.conn.commit()

    # =========================
    # 3. 审批任务节点表
    # =========================
    def save_tasks(self, instance_code: str, tasks: List[Dict[str, Any]]):
        """
        保存审批流程中的任务节点
        - instance_code：所属审批实例
        - tasks：任务节点列表
        """

        # 没有任务直接返回
        if not tasks:
            return

        sql = """
        INSERT INTO lark_approval_task (
            task_id,         -- 任务 ID（唯一）
            instance_code,   -- 审批实例 code
            node_id,         -- 流程节点 ID
            node_name,       -- 节点名称
            node_type,       -- 节点类型
            user_id,         -- 处理人 user_id
            open_id,         -- 处理人 open_id
            status,          -- 任务状态
            start_time,      -- 任务开始时间
            end_time         -- 任务结束时间
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            status = VALUES(status),     -- 状态更新
            end_time = VALUES(end_time)  -- 结束时间更新
        """

        with self.conn.cursor() as cursor:
            for task in tasks:
                cursor.execute(
                    sql,
                    (
                        task.get("id"),           # 任务 ID
                        instance_code,             # 实例 code
                        task.get("node_id"),       # 节点 ID
                        task.get("node_name"),     # 节点名
                        task.get("type"),          # 节点类型
                        task.get("user_id"),       # 用户 ID
                        task.get("open_id"),       # open_id
                        task.get("status"),        # 状态
                        task.get("start_time"),    # 开始时间
                        task.get("end_time"),      # 结束时间
                    ),
                )

        self.conn.commit()

    # =========================
    # 4. 表单字段原始表
    # =========================
    def save_form_fields(self, instance_code: str, fields: List[Dict[str, Any]]):
        """
        保存审批表单的原始字段数据
        - instance_code：审批实例
        - fields：表单字段列表
        """

        if not fields:
            return

        sql = """
        INSERT INTO lark_approval_form_field (
            instance_code,  -- 审批实例 code
            field_id,       -- 字段 ID
            field_name,     -- 字段名称
            field_type,     -- 字段类型
            field_value     -- 原始字段值
        )
        VALUES (%s,%s,%s,%s,%s)
        ON DUPLICATE KEY UPDATE
            field_value = VALUES(field_value) -- 字段值更新
        """

        with self.conn.cursor() as cursor:
            for field in fields:
                cursor.execute(
                    sql,
                    (
                        instance_code,             # 实例 code
                        field["field_id"],         # 字段 ID
                        field["field_name"],       # 字段名
                        field["field_type"],       # 字段类型
                        field["field_value"],      # 字段值
                    ),
                )

        self.conn.commit()

    # =========================
    # 5. 表单字段 KV 拆解表
    # =========================
    def save_field_kv(self, rows: List[Dict[str, Any]]):
        """
        保存表单字段拆解后的 KV 数据
        - rows：已经拆好的 KV 行数据
        """

        if not rows:
            return

        sql = """
        INSERT INTO lark_approval_field_kv (
            approval_id,        -- 审批实例 ID
            row_id,             -- 明细行 ID
            widget_id,          -- 控件 ID
            field_name,         -- 字段名称
            field_type,         -- 字段类型
            field_value_text,   -- 文本值
            field_value_num,    -- 数值
            currency,           -- 币种
            extra_json          -- 额外 JSON 数据
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """

        with self.conn.cursor() as cursor:
            for r in rows:
                cursor.execute(
                    sql,
                    (
                        r.get("approval_id"),        # 审批 ID
                        r.get("row_id"),             # 行 ID
                        r.get("widget_id"),          # 控件 ID
                        r.get("field_name"),         # 字段名
                        r.get("field_type"),         # 类型
                        r.get("field_value_text"),   # 文本值
                        r.get("field_value_num"),    # 数值
                        r.get("currency"),           # 币种
                        r.get("extra_json"),          # 扩展 JSON
                    ),
                )

        self.conn.commit()
