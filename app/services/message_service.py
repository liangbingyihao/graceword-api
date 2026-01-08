import json
import logging

from sqlalchemy import desc, or_, and_

from models.message import Message
from extensions import db
from models.session import Session
from services.coze_service import CozeService
from services.session_service import SessionService
from utils.exceptions import AuthError


class MessageService:
    action_daily_talk = 0
    action_bible_pic = 1
    action_daily_gw = 2
    action_direct_msg = 3
    action_daily_pray = 4
    action_input_prompt = 5
    action_daily_gw_pray = 6
    action_search_hymns = 7
    action_guest_talk = 9

    content_type_user = 1
    content_type_ai = 2

    status_init = 0
    status_pending = 1
    status_success = 2
    status_del = 3
    status_err = 4
    status_timeout = 5
    status_cancel = 6

    explore = [["我想看今天的【每日恩语】", action_daily_gw],
               ["我想把上面的经文做成“经文图”，分享给身边的弟兄姊妹，一起思想神的话语！", action_bible_pic],
               ["我记录当下心情或事件后，你会如何帮我整理", action_direct_msg, "对应的答案"]]
    welcome_msg = {
        "action": 0,
        "content": "",
        "context_id": "0",
        "created_at": "2025-05-28T03:40:49",
        "feedback": {
            "bible": "我的心你要称颂耶和华，不可忘记他的恩惠。（诗篇 103:2）",
            "function": [
                [
                    "最近发生的事情现在未必能明白上帝的心意是什么，现在有了恩语，正好快速把它记下来:",
                    action_input_prompt,
                    "今天觉得好感恩"
                ],
                [
                    "我想看今天的【每日恩语】",
                    action_daily_gw
                ],
                [
                    "怎样从日常小事中发现上帝的作为？",
                    action_daily_talk
                ],
            ],
        },
        "feedback_text": '''✨嗨，你好🙌欢迎来到恩语~！
正如《诗篇》103篇2节所说：“我的心你要称颂耶和华，不可忘记他的恩惠。“
每一件感恩小事💝、圣灵感动🔥、真实感受，甚至讲道亮光🌟都是天父跟我们互动的印记💌，坚持记录，你会发现，上帝如何奇妙地与我们同行👣哦！
快来开始你的恩语之旅吧~🎉  
''',
        "id": "welcome",
        "session_id": 0,
        "status": 2,
        "summary": ""
    }
    default_rsp = {
        "view": "你的这个观点很值得探讨。恩语是一个能帮你持续记录每一件感恩小事，圣灵感动，亮光发现等信息的信仰助手，并且我也努力学习圣经，期待能借助上帝的话语来鼓励你，帮助你在信仰之路上，不断看到上帝持续的工作和恩典哦。"
                "你以上的内容我暂时无法直接找到对应的信仰相关参考，但我已经帮你记录下来了。"
                "我想用这句圣经的话语来共勉： **“但那等候耶和华的，必从新得力，他们必如鹰展翅上腾，他们奔跑却不困倦，行走却不疲乏。”（以赛亚书 40:31）** "
                "如果这个事情对你来说重要，请持续把这个事情在恩语中记录吧，每天打开恩语来回顾，说不定很快就能看到上帝给到你新的发现，以及上帝每一步的保守与恩典哦。",
        "bible": "“但那等候耶和华的，必从新得力，他们必如鹰展翅上腾，他们奔跑却不困倦，行走却不疲乏。”（以赛亚书 40:31）",
        "topic": "其他话题"}

    @staticmethod
    def init_welcome_msg():
        messages = Message.query.filter_by(owner_id=2).filter(Message.id < 1117).order_by(desc(Message.id)).limit(5)
        for m in messages:
            print(m)

    @staticmethod
    def check_permission(session_id, owner_id):
        session = Session.query.filter_by(id=session_id).with_entities(Session.owner_id, Session.session_name,
                                                                       Session.conversation_id).one()
        # session_owner,session_name = session[0],session[1]
        if session[0] != owner_id:
            raise AuthError('session no permission', 404)
        return session

    @staticmethod
    def renew(owner_id, msg_id, prompt):
        '''
        :param msg_id:
        :param prompt:
        :param owner_id:
        :return:
        '''
        # session_owner, session_name, conversation_id = MessageService.check_permission(session_id, owner_id)
        # logging.debug(f"session:{session_owner, session_name}")
        message = Message.query.filter_by(public_id=msg_id, owner_id=owner_id).one()
        if message:
            message.status = MessageService.status_init
            message.feedback_text = prompt or ""
            db.session.commit()
            CozeService.chat_with_coze_async(owner_id, message.id)
            return message.public_id

    @staticmethod
    def del_msg(owner_id, msg_id, content_type):
        '''
        :param msg_id:
        :param content_type:
        :param owner_id:
        :return:
        '''
        message = Message.query.filter_by(public_id=msg_id, owner_id=owner_id).one()
        if message:
            if content_type == MessageService.content_type_user:
                SessionService.reset_updated_at(message.session_id)
                message.content = ""
                message.session_id = -1
            elif content_type == MessageService.content_type_ai:
                message.feedback_text = ""
            else:
                return None

            if not message.content and not message.feedback_text:
                message.status = MessageService.status_del
            db.session.commit()
            return message.public_id

    @staticmethod
    def stop_ai(owner_id, msg_id):
        '''
        :param msg_id:
        :param content_type:
        :param owner_id:
        :return:
        '''
        message = Message.query.filter_by(public_id=msg_id, owner_id=owner_id).one()
        if message and message.status != MessageService.status_success:
            message.status = MessageService.status_cancel
            db.session.commit()
            return message.public_id

    @staticmethod
    def new_message(owner_id, content, context_id, action, prompt, reply, lang):
        '''
        :param lang:
        :param reply:
        :param action:
        :param prompt:
        :param context_id:用户探索的原信息id
        :param owner_id:
        :param content:
        :return:
        '''
        # session_owner, session_name, conversation_id = MessageService.check_permission(session_id, owner_id)
        # logging.debug(f"session:{session_owner, session_name}")
        message = None
        if content:
            if prompt:
                logging.warning(f"prompt:{owner_id, content, action, prompt}")
            try:
                action = int(action)
            except Exception as e:
                pass
            message = Message(0, owner_id, content, context_id, action=action, reply=reply, lang=lang)
            message.feedback_text = prompt or ""
            if action == MessageService.action_guest_talk:
                message.status = MessageService.status_success
            db.session.add(message)
            db.session.commit()
            logging.warning(f"message.id:{message.id},action:{action}")
            if action != MessageService.action_guest_talk:
                CozeService.chat_with_coze_async(owner_id, message.id)

        return message.public_id

    # @staticmethod
    # def get_session_by_id(session_id):
    #     return Session.query.get(session_id)

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

        if search and search.strip():
            if session_type == "topic":
                conditions.append(Message.content.contains(search))
            else:
                conditions.append(or_(
                    Message.content.contains(search),
                    Message.feedback.contains(search)
                ))
        query = Message.query.filter(
            and_(*conditions)
        )
        data = query.order_by(desc(Message.id)) \
            .offset((page - 1) * limit) \
            .limit(limit) \
            .all()

        for msg in data:
            msg.created_at = msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
        return data

    @staticmethod
    def search_message(owner_id, source, search, page, limit):
        # 1:会话，2：时间轴，3：信仰问答，4：收藏
        conditions = [Message.owner_id == owner_id]
        if source == 2:
            conditions.append(Message.session_id > 0)
        elif source == 3:
            session = Session.query.filter_by(owner_id=owner_id, session_name="信仰问答").first()
            if session:
                conditions.append(Message.session_id == session.id)
            else:
                return []
        elif source == 4:
            pass
        conditions.append(or_(
            Message.content.contains(search),
            Message.feedback.contains(search)
        ))
        query = Message.query.filter(
            and_(*conditions)
        )

        return query.order_by(desc(Message.id)) \
            .offset((page - 1) * limit) \
            .limit(limit) \
            .all()
        # messages = query.paginate(page=page, per_page=limit, error_out=False)

    @staticmethod
    def get_message(owner_id, msg_id, retry, stop, lang):
        if msg_id == "welcome":
            return MessageService.welcome_msg
        else:
            message = Message.query.filter_by(public_id=msg_id, owner_id=owner_id).one()
            if retry == 1 and message.status not in (MessageService.status_pending, MessageService.status_success):
                CozeService.chat_with_coze_async(owner_id, message.id)
                message.status = MessageService.status_pending

            if stop and message.status != MessageService.status_success:
                message.status = MessageService.status_cancel
                db.session.commit()
            return message

    @staticmethod
    def filter_msg_by_context_id(owner_id, session_id, context_id):
        session = MessageService.check_permission(session_id, owner_id)
        return Message.query.filter_by(context_id=context_id)

    @staticmethod
    def set_summary(owner_id, msg_id, summary, session_id, session_name):
        if session_id and session_id > 0:
            session = Session.query.filter_by(owner_id=owner_id, id=session_id).one()
            if not session:
                raise Exception("no session")
        if session_name:
            session = SessionService.new_session(session_name, owner_id, 0)
            session_id = session.id
        message = Message.query.filter_by(public_id=msg_id, owner_id=owner_id).first()
        if message:
            if summary:
                message.summary = summary
            if session_id:
                last_session_id = message.session_id
                message.session_id = session_id
                SessionService.reset_updated_at(last_session_id)
            db.session.commit()
            return message.session_id

    @staticmethod
    def set_session_id(owner_id, msg_id, session_id):
        if session_id > 0:
            cnt_session = Session.query.filter_by(owner_id=owner_id, session_id=session_id).count()
            if cnt_session <= 0:
                return False
        message = Message.query.filter_by(public_id=msg_id, owner_id=owner_id).one()
        if message:
            last_session_id = message.session_id
            message.session_id = session_id
            db.session.commit()
            SessionService.reset_updated_at(last_session_id)
            return True
