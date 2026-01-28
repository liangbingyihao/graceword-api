from marshmallow import Schema, fields

class SessionSchema(Schema):
    id = fields.Int(dump_only=True)
    owner_id = fields.Int(dump_only=True)
    robt_id = fields.Int(dump_only=True)
    session_name = fields.Str()
    tags = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
    created_ts = fields.Int(dump_only=True)
    updated_ts = fields.Int(dump_only=True)