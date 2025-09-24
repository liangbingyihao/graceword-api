from sqlalchemy import text, TIMESTAMP, Index, UniqueConstraint

from extensions import db


class Session(db.Model):
    __tablename__ = 'sessions'

    id = db.Column(db.Integer, primary_key=True)
    session_name = db.Column(db.String(50), nullable=False)
    owner_id = db.Column(db.Integer, index=True, nullable=False)
    robot_id = db.Column(db.Integer, nullable=False)
    tags = db.Column(db.String(255))
    conversation_id = db.Column(db.String(255))
    # 创建时间（自动设置）
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

    __table_args__ = (
        UniqueConstraint('owner_id', 'session_name', name='uq_user_session'),
        # 可以添加多个唯一约束
        # UniqueConstraint('email', name='uq_email')
    )

    # # 更新时间（自动更新）
    # updated_at = db.Column(
    #     TIMESTAMP,
    #     server_default=text('CURRENT_TIMESTAMP'),
    #     server_onupdate=text('CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'),
    #     nullable=False
    # )
    # created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    # updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc))

    def __init__(self, session_name, owner_id, robot_id):
        self.session_name = session_name or ""
        self.owner_id = owner_id
        self.robot_id = robot_id

    def __repr__(self):
        return f'<session {self.owner_id} {self.session_name}>'