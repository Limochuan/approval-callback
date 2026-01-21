import json
from typing import Dict, Any, List


def parse_approval_form(form_raw) -> Dict[str, Any]:
    """
    将飞书审批实例中的 form 字段解析为业务可用的 dict 结构
    """

    # form 在接口中是字符串，需要先反序列化
    if isinstance(form_raw, str):
        form_items = json.loads(form_raw)
    else:
        form_items = form_raw

    result: Dict[str, Any] = {}
    items_list: List[Dict[str, Any]] = []

    for item in form_items:
        field_name = item.get("name")
        field_type = item.get("type")
        field_value = item.get("value")

        # 普通字段（日期、文本、编号等）
        if field_type not in ("fieldList",):
            # 统一中文字段名（可按你实际需要再映射）
            if "日期" in field_name:
                result["申请日期"] = field_value
            elif "编号" in field_name:
                result["表单编号"] = field_value
            elif "申请人" in field_name:
                result["申请人"] = field_value
            elif "部门" in field_name:
                result["部门"] = field_value
            elif "总计" in field_name or "总额" in field_name:
                result["总金额"] = field_value
            else:
                # 兜底：直接原名存储
                result[field_name] = field_value

        # 物品明细（fieldList，二维结构）
        else:
            rows = field_value or []
            for row in rows:
                row_data: Dict[str, Any] = {}

                for col in row:
                    col_name = col.get("name")
                    col_type = col.get("type")
                    col_value = col.get("value")

                    if "物品名称" in col_name:
                        row_data["物品名称"] = col_value
                    elif "规格" in col_name:
                        row_data["规格"] = col_value
                    elif "类别" in col_name:
                        row_data["类别"] = col_value
                    elif "数量" in col_name:
                        row_data["数量"] = col_value
                    elif "单位" in col_name:
                        row_data["单位"] = col_value
                    elif "单价" in col_name:
                        row_data["单价"] = col_value
                    elif "图片" in col_name:
                        row_data["图片"] = col_value
                    elif "链接" in col_name:
                        row_data["购买链接"] = col_value
                    else:
                        row_data[col_name] = col_value

                items_list.append(row_data)

    if items_list:
        result["物品明细"] = items_list

    return result
