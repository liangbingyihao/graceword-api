import json
import os
import re
from ast import literal_eval

import time
from utils.time_utils import get_utc_timestamp_millis
import cozepy
from sqlalchemy import create_engine, exc, desc, func, not_
from sqlalchemy.orm import sessionmaker
from concurrent.futures import ThreadPoolExecutor
from models.session import Session

coze_api_token = os.getenv("COZE_API_TOKEN")
main_bot_id = os.getenv("COZE_MAIN_BOT_ID")
gw_coze_host = "https://api-test.grace-word.com"
from cozepy import Coze, TokenAuth, Message, ChatEventType, COZE_CN_BASE_URL, COZE_COM_BASE_URL, MessageType  # noqa

import logging

# 创建日志记录器
logger = logging.getLogger('my_app')
logger.propagate = False
logger.setLevel(logging.DEBUG)  # 设置日志级别

# 创建文件处理器
file_handler = logging.FileHandler('coze.log')
file_handler.setLevel(logging.INFO)

# 创建日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# logger.handlers.clear()
logging.getLogger().handlers.clear()
# 添加处理器到日志记录器
logger.addHandler(file_handler)

# Init the Coze client through the access_token.
coze = Coze(auth=TokenAuth(token=coze_api_token), base_url=COZE_CN_BASE_URL)

# 第一步：生成engine对象
engine = create_engine(
    os.getenv("DATABASE_URL"),
    max_overflow=0,  # 超过连接池大小外最多创建的连接
    pool_size=5,  # 连接池大小
    pool_timeout=30,  # 池中没有线程最多等待的时间，否则报错
    pool_recycle=3600  # 多久之后对线程池中的线程进行一次连接的回收（重置）
)
# 第二步：拿到一个Session类,传入engine
DBSession = sessionmaker(bind=engine)


# 黄色：信靠，盼望，刚强，光明 #FFFBE8
# 红色：慈爱，喜乐 #FFEEEB
# 蓝色：安慰，永恒 #EDF8FF
# 绿色：平安，恩典 #E8FFFF

color_map = {"#FFFBE8": ("信靠", "盼望", "刚强", "光明"),
             "#FFEEEB": ("慈爱", "喜乐"),
             "#EDF8FF": ("安慰", "永恒"),
             "#E8FFFF": ("平安", "恩典")}


class CozeService:
    bot_id = main_bot_id or "7547552285878960168"
    hymn_bot_id = "7566915373069762569"
    executor = ThreadPoolExecutor(3)

    @staticmethod
    def chat_with_coze_async(user_id, msg_id):
        '''
        :param user_id:
        :param msg_id: 1 用户正常记录；其他 用户探索
        :return:
        '''
        try:
            logger.info(f"chat_with_coze_async: {user_id, msg_id}")
            CozeService.executor.submit(CozeService.chat_with_coze, user_id, msg_id)
        except Exception as e:
            logger.exception(e)

    @staticmethod
    def is_explore_msg(message):
        from services.message_service import MessageService
        return len(message.context_id) > 5 or message.action == MessageService.action_search_hymns

    @staticmethod
    def _fix_ai_response(message, ai_response):
        '''1.<对于用户内容同理心的回应（如：你的这个观点很值得探讨）>
        2.恩语是一个能帮你持续记录每一件感恩小事，圣灵感动，亮光发现等信息的信仰助手，并且我也努力学习圣经，期待能借助上帝的话语来鼓励你，帮助你在信仰之路上，不断看到上帝持续的工作和恩典哦。你以上的内容我暂时无法直接找到对应的信仰相关参考，但我已经帮你记录下来了。
        3.我想用这句圣经的话语来共勉：<给予一段鼓励经文>(如：以赛亚书 40:31说：“但那等候耶和华的，必从新得力，他们必如鹰展翅上腾，他们奔跑却不困倦，行走却不疲乏。”）
        4.如果这个事情对你来说重要，请持续把这个事情在恩语中记录吧，每天打开恩语来回顾，说不定很快就能看到上帝给到你新的发现，以及上帝每一步的保守与恩典哦。'''
        default_rsp = {
            "view": "你的这个观点很值得探讨。恩语是一个能帮你持续记录每一件感恩小事，圣灵感动，亮光发现等信息的信仰助手，并且我也努力学习圣经，期待能借助上帝的话语来鼓励你，帮助你在信仰之路上，不断看到上帝持续的工作和恩典哦。"
                    "你以上的内容我暂时无法直接找到对应的信仰相关参考，但我已经帮你记录下来了。"
                    "我想用这句圣经的话语来共勉： **“但那等候耶和华的，必从新得力，他们必如鹰展翅上腾，他们奔跑却不困倦，行走却不疲乏。”（以赛亚书 40:31）** "
                    "如果这个事情对你来说重要，请持续把这个事情在恩语中记录吧，每天打开恩语来回顾，说不定很快就能看到上帝给到你新的发现，以及上帝每一步的保守与恩典哦。",
            "bible": "“但那等候耶和华的，必从新得力，他们必如鹰展翅上腾，他们奔跑却不困倦，行走却不疲乏。”（以赛亚书 40:31）",
            "topic": "其他话题"}
        # FIXME
        message.feedback_text = default_rsp.get("view")
        message.feedback = json.dumps(default_rsp, ensure_ascii=False)

    @staticmethod
    def _extra_ai_response(message, response):
        result = {}
        try:
            result = json.loads(response)
        except Exception as e:
            logger.exception(e)
            try:
                from utils.json_robust import extract_json_values_robust,extract_json_list_robust
                result["explore"] = extract_json_list_robust(response, "explore")
                summary = extract_json_values_robust(response, "summary")
                if summary:
                    result["summary"] = summary[0]
            except Exception as e:
                logger.exception(e)

        view = result.get('view') or message.feedback_text
        if view:
            # result["view"] = view
            message.feedback_text = view.replace("<bible>", "<u class=\"bible\">").replace("</bible>", "</u>")
        else:
            raise Exception("view is null")

        summary = result.get("summary")
        if summary:
            message.summary = summary
        result.pop('view', None)
        return result

    @staticmethod
    def chat_with_coze(user_id, msg_id):
        session = None
        from models.message import Message
        try:
            session = DBSession()
            message = session.query(Message).filter_by(id=msg_id).filter(Message.status != 1).first()
        except exc.OperationalError as e:
            session.rollback()
            logger.exception(e)
            engine.dispose()
            session = DBSession()
            message = session.query(Message).filter_by(id=msg_id).filter(Message.status != 1).first()
        except Exception as e:
            logger.exception(e)
            return

        from services.message_service import MessageService
        from services.session_service import SessionService

        lang = ""
        if message.lang:
            lang = message.lang.lower()
            if "en" in lang:
                lang = "en"
            elif "hans" in lang:
                lang = "zh-hans"
            elif "hant" in lang or "tw" in lang or "hk" in lang:
                lang = 'zh-hant'

        session_lst = []
        session_qa_name = SessionService.session_qa[0]
        auto_session = None
        from models.session import Session
        custom_variables = {}
        additional_messages = []
        is_explore = CozeService.is_explore_msg(message)
        try:
            if message.content == "test":
                raise Exception("test error")
            elif message.content == "timeout":
                return
            if lang:
                custom_variables["lang"] = lang
            if is_explore:
                # 用户探索类型
                if message.action == MessageService.action_daily_pray:
                    context_msg = session.query(Message).filter_by(public_id=message.context_id).first()
                    if context_msg:
                        context_content = context_msg.content
                    else:
                        context_content = message.content
                    custom_variables["target"] = "pray"
                    custom_variables["user_message"] = context_content
                    # additional_messages.append(cozepy.Message.build_user_question_text(context_content))
                    # ask_msg = (custom_prompt + context_content) if custom_prompt else msg_pray + context_content
                else:
                    auto_session = [session_qa_name]
                    custom_variables["target"] = "hymn" if message.action == MessageService.action_search_hymns else "explore"
                    context_msg = session.query(Message).filter_by(public_id=message.context_id).first()
                    user_msg = ""
                    if context_msg:
                        user_msg += context_msg.feedback_text
                        # additional_messages.append(cozepy.Message.build_assistant_answer(context_msg.feedback_text))
                    user_msg += message.content
                    # additional_messages.append(cozepy.Message.build_user_question_text(message.content))
                    custom_variables["user_message"] = user_msg
                    session_lst = session.query(Session).filter_by(owner_id=user_id,
                                                                   session_name=session_qa_name).order_by(
                        desc(Session.id)).with_entities(Session.id, Session.session_name).limit(1).all()

                    # ask_msg = (custom_prompt + message.content) if custom_prompt else msg_explore + message.content
                # rsp_msg = message
            else:
                custom_variables["target"] = "general"
                session_lst = session.query(Session).filter_by(owner_id=user_id).order_by(
                    desc(Session.id)).with_entities(Session.id, Session.session_name).limit(100).all()
                # names = "["
                # for session_id, session_name in session_lst:
                #     names += f"\"{session_name}\","
                # names += "]"
                custom_variables["user_topics"] = [session_name for session_id, session_name in session_lst]
                # ask_msg += message.content
                messages = session.query(Message).filter_by(owner_id=user_id).filter(Message.id < msg_id).order_by(
                    desc(Message.id)).limit(5).all()
                if messages:
                    latest_lang = message.lang
                    for m in reversed(messages):
                        if m.lang == latest_lang:
                            additional_messages.append(cozepy.Message.build_user_question_text(m.content))
                            additional_messages.append(cozepy.Message.build_assistant_answer(m.feedback_text))
                        # if m.action == MessageService.action_daily_pray:
                        #     bible_study.append(m.content)
                        # elder_input += f"\nid:{m.id},用户输入:{m.content},AI回应:{m.feedback_text}"
                    # if bible_study:
                    #     ask_msg = ask_msg.replace("${bible_study}",
                    #                               f'如果用户输入是关于内容${bible_study}的灵修默想祷告，则返回"我的灵修"。')
                    # else:
                    #     ask_msg = ask_msg.replace("${bible_study}", "")
                reply = message.reply + "\n" if message.reply else ""
                additional_messages.append(cozepy.Message.build_user_question_text(reply + message.content))
        except Exception as e:
            logger.error("ai.error in ask msg")
            logger.exception(e)
            message.status = MessageService.status_err
            # message.feedback_text = str(e)
            CozeService._fix_ai_response(message, None)
            session.commit()
            return

        response = ""

        def _set_topics(topics):
            if topics and len(topics) > 0:
                topic = topics[0]
                if not topic and len(topics) > 1:
                    topic = topics[1]
                if topic:
                    if topic in SessionService.session_qa:
                        topic = session_qa_name
                    if not message.session_id:
                        for s_id, s_name in session_lst:
                            if topic == s_name:
                                message.session_id = s_id
                                if not message.feedback:
                                    message.feedback = json.dumps({"topic": topic}, ensure_ascii=False)
                                session.query(Session).filter_by(id=s_id).update({
                                    "updated_ts": get_utc_timestamp_millis()
                                })
                                session.commit()
                                break
                        if not message.session_id and topic:
                            new_session = Session(topic, user_id, 0)
                            session.add(new_session)
                            session.commit()
                            message.session_id = new_session.id
                            if not message.feedback:
                                message.feedback = json.dumps({"topic": topic}, ensure_ascii=False)
                            session.commit()
                return topic

        try:
            message.status = MessageService.status_pending
            session.commit()

            _set_topics(auto_session)
            # ask_msg = msg_json + ask_msg
            response = CozeService._chat_with_coze(session, message, user_id, custom_variables, additional_messages,
                                                   _set_topics if not is_explore else None)

            if message.action == MessageService.action_search_hymns:
                pass
            else:
                result = CozeService._extra_ai_response(message,response)
                if auto_session:
                    topic_name = _set_topics(auto_session)
                else:
                    topic_name = _set_topics([result.get("topic1"), result.get("topic2")])
                if topic_name:
                    result["topic"] = topic_name
                response = json.dumps(result, ensure_ascii=False)
            message.feedback = response
            message.status = MessageService.status_success
            session.commit()
        except Exception as e:
            logger.error("ai.error in chat2")
            logger.exception(e)
            if not message.feedback_text:
                message.status = MessageService.status_err
                CozeService._fix_ai_response(message, response)
                session.commit()
            else:
                logger.error(f"ai.error in chat and ignore:{message.id}")
                message.status = MessageService.status_success
                session.commit()
            # message.feedback_text = str(e)

        # finally:
        #     if session:
        #         session.close()  # 重要！清理会话

    @staticmethod
    def create_conversations():
        conversation = coze.conversations.create()
        return conversation.id

    @staticmethod
    def _extract_content(text, s):
        import re
        s1, e1, s2, e2 = s
        bible, detail = "", ""

        if not s1:
            match = re.search(r"(\"view\"\s*:\s*\")", text)
            if match:
                s[0] = s1 = match.end()

        if not s2:
            match = re.search(r"(,\s*\"bible\"\s*:\s*\")", text)
            if match:
                s[1] = e1 = match.start()
                s[2] = s2 = match.end()

        if not e2:
            match = re.search(r"(,\s*\"explore\"\s*:\s*)", text)
            if match:
                s[3] = e2 = match.start()
        if s1:
            detail = text[s1:e1 if e1 > 0 else -1]
        if s2:
            bible = text[s2:e2 if e2 > 0 else -1]
        return bible, detail

    @staticmethod
    def _chat_with_coze(session, ori_msg, user_id, custom_variables, additional_messages, f_set_topics=None):
        all_content = ""
        pos = [0, 0, 0, 0]
        topic_name = None
        from services.message_service import MessageService
        from utils.json_robust import unescape_json_string
        is_search_hymns = ori_msg.action == MessageService.action_search_hymns
        # is_explore = CozeService.is_explore_msg(ori_msg)
        dst_bot_id = CozeService.hymn_bot_id if is_search_hymns else CozeService.bot_id
        # logger.info(f"_chat_with_coze: {user_id, ori_msg.id, custom_variables,dst_bot_id}")
        pending = False
        start_time = time.time()
        last_len_hymns = 0
        last_complete = True
        last_message = None

        import bots
        from cozepy.request import Requester
        chat = bots.ChatClient(gw_coze_host, Requester())
        if is_search_hymns:
            hymns = chat.hymns(
                custom_variables=custom_variables)
            if hymns:
                try:
                    return json.dumps(hymns.__dict__, ensure_ascii=False)
                except Exception as e:
                    logger.exception(e)
            return
        for event in chat.stream(
                bot_id=dst_bot_id,
                user_id=str(user_id),
                custom_variables=custom_variables,
                additional_messages=additional_messages,
        ):
            if event.event == bots.ChatEventType.GW_MESSAGE_DELTA:
                if last_complete:
                    logger.info(
                        f"_chat_with_coze: {user_id, ori_msg.id} delta msg coming, cost:{time.time() - start_time} s")
                    last_complete = False
                    all_content = ""
                ai_rsp = event.message
                ai_rsp = ai_rsp.encode('utf-8', 'ignore').decode('utf-8')

                all_content += ai_rsp

                if is_search_hymns:
                    from utils.json_robust import extract_json_values_robust
                    # logger.info(f"hymns back:{all_content}")
                    result = {}
                    try:
                        response = extract_json_values_robust(all_content, "response")
                        if response:
                            result["response"] = response[0]
                    except Exception as e:
                        logger.exception(e)
                    try:
                        titles = extract_json_values_robust(all_content, "title")
                        if titles:
                            result["hymns"] = [{"title": x} for x in titles]
                    except Exception as e:
                        logger.exception(e)

                    hymns = result.get("hymns")
                    if hymns and len(hymns) > last_len_hymns:
                        for k in ["composer", "album", "lyrics", "artist", "play_url", "sheet_url", "ppt_url",
                                  "copyright"]:
                            try:
                                data = extract_json_values_robust(all_content, k)
                                if data and len(data) <= len(hymns):
                                    for index, value in enumerate(data):
                                        hymns[index][k] = value
                            except Exception as e:
                                logger.exception(e)
                    if result:
                        try:
                            ori_msg.feedback = json.dumps(result, ensure_ascii=False)
                        except Exception as e:
                            logger.exception(e)
                else:
                    if f_set_topics and not topic_name:
                        topics = re.findall(r'"topic\d":\s*"([^"]*)"\s*,', all_content)
                        topic_name = f_set_topics(topics)

                    if pos[3] <= 0:
                        bible, detail = CozeService._extract_content(all_content, pos)
                        if detail:
                            ori_msg.feedback_text = unescape_json_string(detail)
                        elif not all_content.startswith("{"):
                            ori_msg.feedback_text = all_content
                        # logger.info(f"_chat_detail: {all_content[-10:]} \n got {detail[-10:]}")
                # else:
                #     ori_msg.feedback_text = all_content
                # logger.info(f"CONVERSATION_MESSAGE_DELTA: {ori_msg.feedback}")
                ori_msg.status = 1
                session.commit()
            elif event.event == bots.ChatEventType.GW_MESSAGE_COMPLETED:
                last_complete = True
                return all_content
            elif event.event == ChatEventType.CONVERSATION_MESSAGE_COMPLETED:
                last_complete = True
                # logger.info(
                #     f"_chat_with_coze msg.complete: {user_id, ori_msg.id} done, cost:{time.time() - start_time} s, {ori_msg.feedback_text[:5]}")
                if event.message.type == MessageType.ANSWER:
                    last_message = event.message
                # logger.info(f"CONVERSATION_MESSAGE_COMPLETED: {event.message.content}")
            elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
                # logger.info(
                #     f"_chat_with_coze chat.complete:{user_id, ori_msg.id} done, cost:{time.time() - start_time} s, {ori_msg.feedback_text[:5]}")
                return last_message.content if last_message else ""
            # if event.message.content.startswith("{"):
            #     continue
            # msg_list.append(event.message.content)

    @staticmethod
    def _summary_by_coze(conversation_id, user_id):
        logger.info(f"_summary_by_coze: {user_id, conversation_id}")
        for event in coze.chat.stream(
                bot_id=CozeService.bot_id,
                user_id=str(user_id),
                additional_messages=[Message.build_user_question_text("10个字内描述本会话的主题")],
                conversation_id=conversation_id
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_COMPLETED:
                logger.info(f"_summary_by_coze got: {conversation_id, event.message.content}")
                return event.message.content
