import datetime

from marshmallow import Schema, fields, post_dump

class SessionSchema(Schema):
    id = fields.Int(dump_only=True)
    # owner_id = fields.Int(dump_only=True)
    # robt_id = fields.Int(dump_only=True)
    # tags = fields.Str()
    session_name = fields.Str()
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    created_ts = fields.Int(dump_only=True)
    updated_ts = fields.Int(dump_only=True)

    @post_dump
    def handle_timestamps(self, data, **kwargs):
        """将时间戳转换为日期时间字符串"""
        # 如果存在时间戳，转换为日期时间格式
        if 'created_ts' in data and data['created_ts']:
            timestamp = data['created_ts'] / 1000  # 假设是毫秒级时间戳
            data['created_at'] = datetime.datetime.fromtimestamp(timestamp).isoformat()

        if 'updated_ts' in data and data['updated_ts']:
            timestamp = data['updated_ts'] / 1000  # 假设是毫秒级时间戳
            data['updated_at'] = datetime.datetime.fromtimestamp(timestamp).isoformat()
        return data