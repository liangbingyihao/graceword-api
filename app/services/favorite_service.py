import json
import logging

from flask_sqlalchemy import Pagination
from sqlalchemy import desc

from models.favorites import Favorites
from models.message import Message
from extensions import db
from models.session import Session
from services.coze_service import CozeService
from services.message_service import MessageService
from services.session_service import SessionService
from utils.exceptions import AuthError


class FavoriteService:

    @staticmethod
    def new_favorite(owner_id, message_id, content_type):
        '''
        :param owner_id:
        :param message_id:
        :param content_type:
        :return:
        '''
        # session_owner, session_name, conversation_id = MessageService.check_permission(session_id, owner_id)
        # logging.debug(f"session:{session_owner, session_name}")
        message = Message.query.filter_by(public_id=message_id, owner_id=owner_id).one()
        if message:
            if content_type == MessageService.content_type_ai:
                content = message.feedback_text
            else:
                content_type = MessageService.content_type_user
                content = message.content

            favorite = Favorites(owner_id, message_id, content_type, content)
            db.session.add(favorite)
            db.session.commit()
            return True

    @staticmethod
    def toggle_favorite(owner_id, message_id, content_type):
        """
        调转收藏状态
        :param content_type:
        :param owner_id: 用户ID（用于权限验证）
        :param message_id: 要调转的信息ID
        :return: 0表示不再收藏，1表示已收藏，其他表示失败
        """
        try:
            # 查询并验证收藏记录归属
            favorite = Favorites.query.filter_by(owner_id=owner_id, message_id=message_id,
                                                 content_type=content_type).first()

            if favorite:
                # 执行删除
                db.session.delete(favorite)
                db.session.commit()
                return 0
            else:
                message = Message.query.filter_by(public_id=message_id, owner_id=owner_id).one()
                if message:
                    session_name = ""
                    if content_type == MessageService.content_type_ai:
                        if message.action == MessageService.action_search_hymns:
                            content = message.feedback
                        else:
                            content = message.feedback_text
                    else:
                        content_type = MessageService.content_type_user
                        content = message.content
                        session = Session.query.filter_by(id=message.session_id).first()
                        if session:
                            session_name = session.session_name

                    favorite = Favorites(owner_id, message_id, content_type, content, session_name)
                    db.session.add(favorite)
                    db.session.commit()
                    return 1
            return -1
        except Exception as e:
            db.session.rollback()
            logging.error(f"Failed to delete favorite {message_id}: {str(e)}", exc_info=True)
            return -1

    # @staticmethod
    # def get_session_by_id(session_id):
    #     return Session.query.get(session_id)

    @staticmethod
    def get_favorite_by_owner(owner_id, page, limit, search):
        query = Favorites.query.filter_by(owner_id=owner_id)
        if search and search.strip():
            query = query.filter(Favorites.content.ilike(f'%{search}%'))

        items = query.order_by(desc(Favorites.id)) \
            .offset((page - 1) * limit) \
            .limit(limit) \
            .all()
        return items
        # return Pagination(query=None, page=page, per_page=limit, items=items, total=None)
        # return Favorites.query.filter_by(owner_id=owner_id).order_by(desc(Favorites.id)).paginate(page=page, per_page=limit, error_out=False)
