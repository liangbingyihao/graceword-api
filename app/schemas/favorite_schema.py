import datetime

from marshmallow import Schema, fields, post_dump

class FavoriteSchema(Schema):
    message_id = fields.Str(dump_only=True)
    content_type = fields.Int(dump_only=True)
    content = fields.Str()
    session_name = fields.Str(dump_only=True)
    created_at = fields.DateTime()
    created_ts = fields.Int(dump_only=True)

    @post_dump
    def handle_timestamps(self, data, **kwargs):
        """将时间戳转换为日期时间字符串"""
        # 如果存在时间戳，转换为日期时间格式
        if 'created_ts' in data and data['created_ts']:
            timestamp = data['created_ts'] / 1000  # 假设是毫秒级时间戳
            data['created_at'] = datetime.datetime.fromtimestamp(timestamp).isoformat()

        return data