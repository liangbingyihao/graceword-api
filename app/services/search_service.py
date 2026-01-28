import re
from typing import List

from sqlalchemy import desc, or_, and_
from sqlalchemy.orm import load_only

from models.message import Message
from models.session import Session
from services.favorite_service import FavoriteService


class SearchService:

    @staticmethod
    def highlight_keyword_sentences(text: str, search: str) -> str:
        """
        查找文本中包含关键词的所有句子，并将关键词标记为红色

        :param text: 原始文本
        :param search: 要搜索的关键词
        :return: 包含高亮关键词的句子列表
        """
        if not text or not search:
            return []

        # 转义正则特殊字符
        escaped_search = re.escape(search)

        # 分割句子（简单按句号、问号、感叹号分割）
        sentences = re.split(r'(?<=[.!?。，])\s+', text)

        # 筛选并高亮包含关键词的句子
        highlighted_sentences = []
        for sentence in sentences:
            if re.search(escaped_search, sentence, re.IGNORECASE):
                # 高亮关键词（保留原大小写）
                highlighted = re.sub(
                    f'({escaped_search})',
                    r"<span style='color:red'>\1</span>",
                    sentence,
                    flags=re.IGNORECASE
                )
                highlighted_sentences.append(highlighted)

        return "...".join(highlighted_sentences)+"..."

    @staticmethod
    def handle_snippet(messages, search):
        res = []
        for row in messages:
            content = ""
            if search and search in row.content:
                content = SearchService.highlight_keyword_sentences(row.content, search)
            if search and hasattr(row, 'feedback_text') and search in row.feedback_text:
                content += SearchService.highlight_keyword_sentences(row.feedback_text, search)
            msg = {
                'message_id': row.message_id,
                'content': content,
                'created_at': row.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                'created_ts': row.created_ts
            }
            res.append(msg)
        return res

    @staticmethod
    def filter_message(owner_id, session_id, session_type, search, page, limit):
        '''
        :param owner_id:
        :param session_id:
        :param session_type: #"topic", "question"
        :param search:
        :param page:
        :param limit:
        :return:
        '''
        if not search or not search.strip():
            return []

        if session_type == "favorite":
            return SearchService.handle_snippet(FavoriteService.get_favorite_by_owner(owner_id, page=page,
                                                                                      limit=limit, search=search),
                                                search)
        conditions = [Message.owner_id == owner_id]
        if session_id and isinstance(session_id, int):
            conditions.append(Message.session_id == session_id)
        elif session_type:
            if session_type == "topic":
                conditions.append(Message.session_id > 0)
            elif session_type == "question":
                session = Session.query.filter_by(owner_id=owner_id, session_name="信仰问答").first()
                if session:
                    conditions.append(Message.session_id == session.id)
                else:
                    return []

        message_id = Message.public_id.label('message_id')
        if session_type == "topic":
            conditions.append(Message.content.contains(search))
            query = (Message.query.options(load_only(Message.public_id, Message.content, Message.created_at))
            .add_columns(
                message_id,
                Message.content,
                Message.created_at,
                Message.created_ts
            )
            .filter(
                and_(*conditions)
            ))
        else:
            conditions.append(or_(
                Message.content.contains(search),
                Message.feedback_text.contains(search)
            ))
            query = (Message.query.options(
                load_only(Message.public_id, Message.content, Message.feedback_text, Message.created_at))
            .add_columns(
                message_id,
                Message.content,
                Message.feedback_text,
                Message.created_at,
                Message.created_ts
            )
            .filter(
                and_(*conditions)
            ))
        return SearchService.handle_snippet(query.order_by(desc(Message.id)) \
                                            .offset((page - 1) * limit) \
                                            .limit(limit) \
                                            .all(), search)
