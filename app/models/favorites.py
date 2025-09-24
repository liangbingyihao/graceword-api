from sqlalchemy import text, TIMESTAMP, Index, UniqueConstraint

from extensions import db


class Favorites(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, index=True, nullable=False)
    message_id = db.Column(db.String(36), index=True, nullable=False)
    content_type = db.Column(db.Integer, index=True, nullable=False)
    session_name = db.Column(db.String(50))
    content = db.Column(db.UnicodeText, nullable=False)
    # 创建时间（自动设置）
    created_at = db.Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    __table_args__ = (
        UniqueConstraint('message_id', 'content_type', name='uq_msg'),
        # 可以添加多个唯一约束
        # UniqueConstraint('email', name='uq_email')
    )

    def __init__(self,owner_id, message_id,  content_type,content,session_name=""):
        self.owner_id = owner_id
        self.message_id = message_id
        self.content_type = content_type
        self.content = content
        self.session_name = session_name

    def __repr__(self):
        return f'<favorites {self.message_id} {self.content_type}>'