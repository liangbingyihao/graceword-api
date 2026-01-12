import uuid
from datetime import datetime, timezone

from sqlalchemy import TIMESTAMP, text

from extensions import db


class Message(db.Model):
    __tablename__ = 'message'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    session_id = db.Column(db.Integer, index=True, nullable=False)
    context_id = db.Column(db.String(36), index=True, nullable=False)
    summary = db.Column(db.String(32))
    lang = db.Column(db.String(10))
    owner_id = db.Column(db.Integer, index=True, nullable=False)
    status = db.Column(db.Integer, nullable=False, default=0)  # 0 默认状态 1 AI回应中 2 AI回应完毕 3 已删除
    action = db.Column(db.Integer, nullable=False, default=0)  # 0 用户输入的 1 探索问题 2 生成图片
    content = db.Column(db.UnicodeText, nullable=False)
    reply = db.Column(db.UnicodeText)
    feedback = db.Column(db.UnicodeText, nullable=False)
    feedback_text = db.Column(db.UnicodeText, nullable=False)
    created_at = db.Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        nullable=False
    )
    updated_at = db.Column(
        TIMESTAMP,
        server_default=text('CURRENT_TIMESTAMP'),
        server_onupdate=text('CURRENT_TIMESTAMP'),
        nullable=False
    )

    # updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __init__(self, session_id, owner_id, content, context_id=0, status=0, action=0, reply="", lang=""):
        self.session_id = session_id
        self.owner_id = owner_id
        self.content = content
        self.context_id = context_id
        self.status = status
        self.action = action
        self.feedback = ""
        self.feedback_text = ""
        self.reply = reply
        self.lang = lang

    def __repr__(self):
        return f'<message {self.id}>'
