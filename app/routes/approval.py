import json


def parse_approval_form(form_raw):
    """
    将飞书审批 form 字段解析为干净、可用的 dict 结构
    """

    if not form_raw:
        return {}

    # 飞书这里给的是字符串 JSON，必须先反序列化
    if isinstance(form_raw, str):
        form_items = json.loads(form_raw)
    else:
        form_items = form_raw

    result = {}
    items = []
    total_amount = None

    for field in form_items:
        field_name = field.get("name", "").strip()
        field_type = field.get("type")
        value = field.get("value")

        # 申请日期 / 编号 / 普通输入
        if field_type in ("date", "serialNumber", "input", "text"):
            result[normalize_name(field_name)] = value

        # 申请人
        elif field_type == "contact":
            result["申请人"] = {
                "user_id": value[0] if value else None,
                "open_id": field.get("open_ids", [None])[0]
            }

        # 部门
        elif field_type == "department":
            dept = value[0] if value else {}
            result["部门"] = {
                "name": dept.get("name"),
                "open_id": dept.get("open_id")
            }

        # 物品明细（fieldList）
        elif field_type == "fieldList":
            for row in value:
                item = {}
                for cell in row:
                    name = normalize_name(cell.get("name", ""))
                    ctype = cell.get("type")
                    cvalue = cell.get("value")

                    if ctype == "number":
                        item[name] = int(cvalue)
                    elif ctype == "amount":
                        item[name] = int(cvalue)
                    elif ctype == "image":
                        item[name] = cvalue or []
                    else:
                        item[name] = cvalue

                items.append(item)

        # 总金额
        elif field_type == "formula":
            total_amount = value

    if items:
        result["物品明细"] = items

    if total_amount is not None:
        result["总金额"] = total_amount

    return result


def normalize_name(name: str) -> str:
    """
    统一字段名，去掉中英文混杂说明
    """
    name = name.replace("申请日期", "").replace("编号", "")
    name = name.replace("物品名称", "物品名称")
    name = name.replace("详细规格", "规格")
    name = name.replace("购买数量", "数量")
    name = name.replace("单价", "单价")
    name = name.replace("总计金额", "总金额")
    return name.strip()
