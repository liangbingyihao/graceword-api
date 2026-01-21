import json

from marshmallow import Schema, fields, ValidationError


class FilteredJSONStringField(fields.Field):
    """只返回JSON字符串中指定的key"""

    def __init__(self, allowed_keys=None, **kwargs):
        super().__init__(**kwargs)
        self.allowed_keys = allowed_keys or []  # 允许保留的key列表

    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return None

        try:
            # 解析JSON字符串或保持字典不变
            data = json.loads(value) if isinstance(value, str) else value

            # 过滤出指定key
            if isinstance(data, dict) and self.allowed_keys:
                return {
                    k: v for k, v in data.items()
                    if k in self.allowed_keys
                }
            return data

        except json.JSONDecodeError:
            return None

    def _deserialize(self, value, attr, data, **kwargs):
        return value  # 反序列化保持不变

class SessionMsgSchema(Schema):
    public_id = fields.Str(dump_only=True,data_key="id")
    session_id = fields.Int(dump_only=True)
    summary = fields.Str(dump_only=True)
    status = fields.Int(dump_only=True)
    action = fields.Int(dump_only=True)
    feedback = FilteredJSONStringField(
        allowed_keys=["color_tag", "tag","topic","hymns","response"],
        dump_only=True
    )
    content = fields.Str()
    feedback_text = fields.Str()
    created_at = fields.Str()
    created_ts = fields.Int(dump_only=True)
    updated_ts = fields.Int(dump_only=True)