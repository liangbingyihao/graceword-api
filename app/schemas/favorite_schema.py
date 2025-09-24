from marshmallow import Schema, fields

class FavoriteSchema(Schema):
    message_id = fields.Str(dump_only=True)
    content_type = fields.Int(dump_only=True)
    content = fields.Str()
    session_name = fields.Str(dump_only=True)
    created_at = fields.DateTime()