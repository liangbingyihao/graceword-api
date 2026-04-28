from datetime import datetime
from time import time
import logging
from sqlalchemy import desc, update, and_

from models.message import Message
from models.session import Session
from extensions import db
from services import constants


class SessionService:
    system_sessions = []


    @staticmethod
    def new_session(session_name, owner_id, robot_id):
        session = Session.query.filter_by(owner_id=owner_id, session_name=session_name).first()
        if session:
            return session
        session = Session(session_name=session_name, owner_id=owner_id, robot_id=robot_id)
        db.session.add(session)
        db.session.commit()

        return session

    @staticmethod
    def get_session_by_id(session_id):
        return Session.query.get(session_id)


    @staticmethod
    def get_system_sessions():
        if not SessionService.system_sessions:
            SessionService.system_sessions = Session.query.filter_by(owner_id=0).order_by(desc(Session.id)).all()
        return SessionService.system_sessions

    @staticmethod
    def get_session_by_owner(owner_id, page, limit):
        return Session.query.filter_by(owner_id=owner_id, robot_id=0).order_by(desc(Session.updated_ts)).paginate(
            page=page, per_page=limit, error_out=False)

    @staticmethod
    def reset_updated_at(session_id):
        if not session_id or session_id <= 0:
            return
        last_msg = Message.query.filter_by(session_id=session_id).order_by(desc(Message.id)).first()
        updated_ts = last_msg.created_ts if last_msg else 0
        logging.warning(f"reset_updated_at:{session_id},{updated_ts}")
        Session.query.filter_by(id=session_id).update({
            "updated_ts": updated_ts
        })
        db.session.commit()

    @staticmethod
    def del_session(owner_id, session_id):
        exits_session = Session.query.filter_by(id=session_id, owner_id=owner_id).first()

        if exits_session:
            if exits_session.session_name == constants.session_qa[0]:
                return
            # 执行删除
            db.session.delete(exits_session)
            db.session.commit()

        update_stmt = (
            update(Message)
            .where(
                and_(Message.owner_id == owner_id) &
                (Message.session_id == session_id)
            )
            .values(session_id=-1)
        )
        db.session.execute(update_stmt)
        db.session.commit()

    @staticmethod
    def set_session_name(owner_id, session_id, session_name):
        if not session_id or session_id <= 0:
            return
        session = Session.query.filter_by(id=session_id, owner_id=owner_id).first()
        if session:
            if session.session_name == constants.session_qa[0]:
                return
            session.session_name = session_name
            db.session.commit()
            return True

    @staticmethod
    def get_session(owner_id, session_id):
        if not session_id or session_id <= 0:
            return
        session = Session.query.filter_by(id=session_id, owner_id=owner_id).one_or_none()
        if not session:
            session = Session.query.filter_by(id=session_id, owner_id=0).one()
        return session
