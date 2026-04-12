from fastapi.exceptions import RequestValidationError

# 字段中文映射（可扩展）
FIELD_ALIAS = {
    "username": "用户名",
    "password": "密码",
}


# 错误信息映射（可扩展）
MSG_MAP = {
    "Field required": "不能为空",
    "Input should be a valid string": "必须是字符串",
    "Input should be a valid integer": "必须是整数",
}


def format_validation_errors(exc: RequestValidationError):
    errors = []

    for err in exc.errors():
        loc = err.get("loc", [])

        # 去掉 body，只保留字段路径
        field_path = [str(i) for i in loc if i != "body"]
        field = ".".join(field_path)

        # 取最后一个字段名用于展示
        field_key = field_path[-1] if field_path else field
        field_name = FIELD_ALIAS.get(field_key, field_key)

        raw_msg = err.get("msg", "")
        message = MSG_MAP.get(raw_msg, raw_msg)

        errors.append({
            "field": field,                 # 原字段（用于前端定位）
            "message": f"{field_name}{message}"  # 用户友好提示
        })

    return errors