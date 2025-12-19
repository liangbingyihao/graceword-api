import json
import os
import re
import time

import cozepy
from sqlalchemy import create_engine, exc, desc, func, not_
from sqlalchemy.orm import sessionmaker
from concurrent.futures import ThreadPoolExecutor
from models.session import Session

coze_api_token = os.getenv("COZE_API_TOKEN")
main_bot_id = os.getenv("COZE_MAIN_BOT_ID")
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

# msg_json = '''
# !!!你必须根据用户使用的语言进行回复!!!
#
# ### 输出格式说明:
# !!!本次输出需要生成一个严格符合 JSON 格式的字符串,不要包含 JSON 之外的任何字符（如注释或说明）。
# 其中字段`view`是一段 Markdown 格式的文本（需转义所有 JSON 特殊字符）,确保所有双引号（`"`）、反斜杠（`\`）、换行符（`\n`）等被转义为 `\"`、`\\`、`\\n`。
# 字段`view`格式要求：
# 1. Markdown 内容需包含标题、代码块和列表，标题只能是h3~h6，不允许为h1、h2。
# 2. 确保所有双引号（`"`）、反斜杠（`\`）、换行符（`\n`）等被转义为 `\"`、`\\`、`\\n`。
# 3. view里面所有圣经经文全文要用 ** 包裹加粗效果。例如：**“你们要将一切的忧虑卸给神，因为他顾念你们。”（彼前5:7）**
# 4. 你必须根据用户使用的语言进行回复,用户可能输入简体中文、繁体中文、英文等，需要返回用户输入的语言。
# 5.“当遇到用户中英混杂的表达时，优先分析其语言使用的核心逻辑和主要意图，而>不是单纯依赖词汇占比或判断母语。具体反应逻辑如下：
# 5.1 识别主导语言框架
# - 观察用户表达的句子结构、语法规则和常用词汇倾向。例如：
# - 若句子以中文语法为主（如“我觉得这个project需要more attention”），即使夹
# 杂英文词汇，也会以中文为基础回应，同时保留关键英文术语（如“project”）。
# - 若句子以英文语法为主（如“Maybe we can先讨论方案，再decide细节”），则会以英文框架回应，适当融入中文词汇（如“先讨论方案”）。
# 5.2 匹配>用户的表达习惯
# - 不刻意区分母语，而是模仿用户的语言混合模式。例如：
# - 如果用户习惯“中文主语+英文动词”（如“这个问题需要confirm一下”），回应时也会采用类似结构，保持表达习惯的一致性。
# - 若用户在中英混杂中偏>向某一语言的情感倾向（如用英文表达专业术语，中文表达情绪），会针对性调整语气，确保语境贴合。
# 5.3 优先保证沟通流畅性
# - 无论用户如何混杂语言，核心目标是让回应清晰易懂。若发现混杂表达可能导致歧义，会用更明>确的单一语言重新组织信息，同时标注关键术语（例如：“这里的‘deadline’是否指提交截止日期？”）。”
# ### 以上是输出格式
#
# ###以下是任务说明:
#
# '''
#
# msg_feedback = '''你要帮助基督徒用户记录的感恩小事，圣灵感动，亮光发现、回答用户关于信仰的问题，请进行以下反馈:
#                 1.view: 用户查看的回应文本,必须是**Markdown 格式的字符串**（支持标题、列表、代码块等语法）,标题只能是h3~h6，不允许为h1、h2。详细说明见后面view字段的详细要求。希望能有信息出处的展示。
#                 2.bible:view字段回应包含的最主要的一节圣经经文，要包括经文全文和出处。例如“你们要将一切的忧虑卸给神，因为他顾念你们。”（彼前5:7）
#                 3.topic1:如果用户输入是关于信仰的问题，返回"信仰问答"，${bible_study}否则从${event}里选出一个主题分类,无法选取则为""。如果用户输入英文，topic也要用英文。如果用户输入繁体，topic也要用繁体。
#                 3.topic2:无法选出topic1时，新增一个6个字以内的主题分类。如果用户输入英文，topic也要用英文。如果用户输入繁体，topic也要用繁体。
#                 4.tag:对用户输入的内容返回的圣经经文打标签，标签只能从"信靠，盼望，刚强，光明，慈爱，喜乐，安慰，永恒，平安，恩典"选择最接近的一个。
#                 5.summary:给出8个字以内的重点小结
#                 6.explore:字符串数组形式给出3个和用户输入内容密切相关的，引导基督教新教教义范围内进一步展开讨论的话题，话题的形式可以是问题或者指令。但不能给反问用户感受的问句。
#                 7.严格按json格式返回。{"topic1":<topic1>,"topic2":<topic2>,"view":<view>,"bible":<bible>,"explore":<explore>,"tag":<tag>,"summary":<summary>}
#                 8.topic1,topic2两个字段必须要放在前面
#                 9.严格按照用户输入的语言返回上面的view、bible、topic1、topic2、summary、explore字段。用户可能输入简体中文、繁体中文、英文等，需要返回用户输入的语言。
#
#                 ###以下是view字段的详细要求：
#  你要先识别用户是在问问题还是在记录。
#
# 一，如果用户是在问问题，>他通常会用问句来做结尾，或者语义是一个具体的问题呈现。
#
# 接收到问题后，先回复一段共情用户。
# 输入内容的开头，在基督教新教的框架内容上，去回答他的问题。回答问题时，请围绕【具体主题】进行回答，要求：
#
# A. 标题加>粗（用【】标注主题），首句先提炼核心结论；
# ​
# B. 分点回答时使用 1. 2. 3. … 有序>列表，每点前用简短关键词加粗（如 核心优势：），内容简洁清晰；
# ​
# C. 避免‘首先/然后’等过渡词，直接按逻辑顺序分点，每点>控制在2-3句话，便于快速阅读，
#
# D.在段与段之间要空一行。
#
# 字数在5000字以内。这一>类的内容，全部都归类到【信仰问答】的主题分类中。
#
# 二,如果问题超出了基督教新教的原则，或者有不确定之处，要写清楚这个观点来源，并提醒用户观点仅供参考。
# 鼓励他可以把问题记录或收藏下来，日后在生活实践中，持续用这个恩语app来记录，可能有新的亮光发现。
#
# 三，如果他问到我们app一些功能性的问题，则帮他把问题归纳到【功能相关】的主题，并且相应回复以下内容:
#
# 1.当问题涉及到“每日恩语”，回复“点击左上角按钮就能看到我们。每日英语的按钮啦，点开就能看到当日的每日恩语经文图哦。”
#
# 2.当问题涉及到“生成经文图”，回复“点击经文下面的图片bottom，恩语就能为你生成经文图，方便你下载或分享给你想鼓励的人哦。”
#
# 四，如果用户在祷告默想的内容下面记录的内容，跟祷告默想有比较高的关联性的话，就判断为这是他的灵修内容，把这一类的内容统一归纳到【我的灵修】的主题下面
#
# 五，如果用户的内容是关于他自己的祷告事项，或者跟祷告有比较高的关联性的话，就判断为这是他的祷告事项，把这一类的内容统一归纳到【祷告事项】的主题下面
#
# 六，如果用户的问题涉及到政治，自杀，黄赌毒等敏感话题，温馨告知这类问题无法回答，可以帮他记录下来到一个新的时间轴主题中，并给予一段积极正面的经文作为鼓励，让他知道无论经历多难的事情，上帝依然爱他，对他的生命有一个美好的计划。
#
# 最后，推荐他一条与之相关的新教圣经中的经文作为结尾，标明经文的出处。并且根据回应的>主题，鼓励他记录相应的感受。
# 比如:在“xx情况下”，你是如何“xxx”的呢？可以试着记录下来哦，说不定，不久的将来你回看的时候，就有新发现！
#
# 在用户同类的事情，尽量不要用同一句经文进行回复。
# 要做到给予用户的20句经文中不会有重复的经文出现。
#
# 如果用户是记录内容，不是问问题，无论是感恩小事，圣灵感动，亮光发现，讲道笔记等信息，先用共情的语言回应用户的记录内容，再返回一段基督教新教的圣经中的相关经文进行鼓励。
#
# 然后针对该经文予一段500字以内的内容拓展，可以说经文的经典人物背景，也可以讲这段经文的实际应用。
#
# 如果用户是问圣经相关的问题，先回复一段共情用户输入内容的开头，再根据用户的问题进行回答，回答的内容要符合基>督教新教的教义，或者基于圣经的常识性问题。
#
# 如果用户的问题存在不同的观点，那就要列明这些都只是观点，仅供参考。
#
# 回答的内容在3000字以内。
#
# 圣经经文要高亮显示，要合理分段方便在手机查看，段落要分明。如有需要可以分点
# 来回答，便于阅读者来阅读。
#
#  ###以上是view字段的详细要求
#
#                 !!!你必须根据用户使用的语言进行回复!!!
#                 ###以下是用户本次的输入内容：
#                 '''
#
# msg_context = '''###以下是用户最近几次和AI对话的记录：
# '''
#
# msg_explore = '''你要在基督教正统教义范围内对下面输入进行以下反馈:
#                 1.view:用户查看的回应文本,必须是**Markdown 格式的字符串**（支持标题、列表、代码块等语法）,标题只能是h3~h6，不允许为h1、h2，圣经经文要高亮显示，要合理分段方便在手机查看，段落要分明。先回复一段共情用户输入内容的开头，再根据用户的问题进行回答，回答的内容要符合基督教新教的教义，或者基于圣经的常识性问题。如果用户的问题存在不同的观点，那就要列明这些都只是观点，仅供参考。可以根据回复的内容，给出一些符合圣经原则的实际应用的建议。
#                 2.bible:view字段回应包含的最主要的一节圣经经文，要包括经文全文和出处。例如“你们要将一切的忧虑卸给神，因为他顾念你们。”（彼前5:7）
#                 3.explore:字符串数组形式给出给出3个和用户输入内容密切相关的，引导基督教新教教义范围内进一步展开讨论的话题，话题的形式可以是问题或者指令。但不能给反问用户感受的问句。
#                 4.summary:给出8个字以内的重点小结
#                 5.严格按json格式返回。{"view":<view>,"bible":<bible>,"explore":<explore>,"summary":<summary>}
#                 6.严格按照用户输入的语言返回上面的view、bible、explore字段。用户可能输入简体中文、繁体中文、英文等，需要返回用户输入的语言。
#
#                 !!!你必须根据用户使用的语言进行回复!!!
#                  用户问题:
#                 '''
#
# msg_pray = '''你要在基督教正统教义范围内对下面输入提供祷告和默想建议:
#                 1.view:针对用户的输入内容，提供与之相关的祷告和默想，以及返回一段符合基督教新教原则的实际应用建议，字数在500字以内。分为以下三部分:默想，祷告，实际应用。必须是Markdown 格式的字符串（支持标题、列表、代码块等语法）,标题只能是h3~h6，不允许为h1、h2，圣经经文要高亮，要合理分段方便在手机查看，段落要分明。
#                 2.bible:一句合适的圣经经文。要包括经文全文和出处。例如“你们要将一切的忧虑卸给神，因为他顾念你们。”（彼前5:7）
#                 3.explore:字符串数组形式给出2个和用户输入内容密切相关的，引导基督教新教教义范围内进一步展开讨论的话题，话题的形式可以是问题或者指令。但不能给反问用户感受的问句。
#                 4.prompt: 给出1个根据上文祷告默想和实际应用内容相关，且能引导用户写一下他与之相关感受，经历的引导词，示例:关于“上帝的恩典够我用”的提醒，让我想到最近生活中的一个具体实践....
#                 5.严格按json格式返回。{"view":<view>,"bible":<bible>,"explore":<explore>,"prompt":<prompt>}
#                 6.严格按照用户输入的语言返回上面的view、bible、explore,prompt字段。用户可能输入简体中文、繁体中文、英文等，需要返回用户输入的语言。
#
#                 !!!你必须根据用户使用的语言进行回复!!!
#                 以下是用户的输入内容：
#                 '''
# msg_error = '''我很乐意帮你做大小事情的记录，都会成为你看见上帝恩典的点点滴滴。但这个问题我暂时没有具体的推荐，你有此刻想记录的心情或亮光想记录吗？
# '''

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
        # if not ai_response:
        #     response = json.dumps(default_rsp, ensure_ascii=False)
        #     message.feedback = response
        # else:
        #     result = json.loads(ai_response)

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
                    additional_messages.append(cozepy.Message.build_user_question_text(context_content))
                    # ask_msg = (custom_prompt + context_content) if custom_prompt else msg_pray + context_content
                else:
                    auto_session = [session_qa_name]
                    custom_variables["target"] = "explore"
                    additional_messages.append(cozepy.Message.build_user_question_text(message.content))
                    session_lst = session.query(Session).filter_by(owner_id=user_id,
                                                                   session_name=session_qa_name).order_by(
                        desc(Session.id)).with_entities(Session.id, Session.session_name).limit(1).all()

                    # ask_msg = (custom_prompt + message.content) if custom_prompt else msg_explore + message.content
                # rsp_msg = message
            else:
                custom_variables["target"] = "record"
                session_lst = session.query(Session).filter_by(owner_id=user_id).order_by(
                    desc(Session.id)).with_entities(Session.id, Session.session_name).limit(100).all()
                names = "["
                for session_id, session_name in session_lst:
                    names += f"\"{session_name}\","
                names += "]"
                custom_variables["user_topics"] = names
                # ask_msg += message.content
                messages = session.query(Message).filter_by(owner_id=user_id).filter(Message.id < msg_id).order_by(
                    desc(Message.id)).limit(5).all()
                if messages:
                    latest_lang = message.lang
                    for m in reversed(messages):
                        if m.lang == latest_lang:
                            additional_messages.append(cozepy.Message.build_user_question_text(m.content))
                            additional_messages.append(cozepy.Message.build_assistant_answer(m.feedback))
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
                                    "updated_at": func.now()
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
                result = {}
                try:
                    result = json.loads(response)
                except Exception as e:
                    logger.error(f"ai.error in chat1,feedback_text:${message.feedback_text}")
                    logger.exception(e)

                view = result.get('view') or message.feedback_text
                if view:
                    result["view"] = view
                    message.feedback_text = view
                else:
                    raise Exception("view is null")

                summary = result.get("summary")
                if summary:
                    message.summary = summary
                if not is_explore:
                    tag = result.get("tag")
                    if tag:
                        for k, v in color_map.items():
                            if tag in v:
                                result["color_tag"] = k
                                break
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
            match = re.search(r"(\"bible\"\s*:\s*\")", text)
            if match:
                s[1] = e1 = match.start()
                s[2] = s2 = match.end()

        if not e2:
            match = re.search(r"(\"explore\"\s*:\s*)", text)
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
        logger.info(f"_chat_with_coze: {user_id, ori_msg.id, custom_variables}")
        from services.message_service import MessageService
        from utils.json_robust import unescape_json_string
        is_search_hymns = ori_msg.action == MessageService.action_search_hymns
        # is_explore = CozeService.is_explore_msg(ori_msg)
        dst_bot_id = CozeService.hymn_bot_id if is_search_hymns else CozeService.bot_id
        pending = False
        start_time = time.time()
        last_len_hymns = 0
        for event in coze.chat.stream(
                bot_id=dst_bot_id,
                user_id=str(user_id),
                custom_variables=custom_variables,
                additional_messages=additional_messages,
        ):
            if event.event == ChatEventType.CONVERSATION_MESSAGE_DELTA:
                if not pending:
                    logger.info(f"_chat_with_coze: {user_id, ori_msg.id} pending, cost:{time.time() - start_time} s")
                    pending = True
                message = event.message
                all_content += message.content

                if is_search_hymns:
                    from utils.json_robust import extract_json_values_robust
                    # logger.info(f"hymns back:{all_content}")
                    result = {}
                    try:
                        response = extract_json_values_robust(all_content,"response")
                        if response:
                            result["response"] = response[0]
                    except Exception as e:
                        logger.exception(e)
                    try:
                        titles = extract_json_values_robust(all_content,"title")
                        if titles:
                            result["hymns"] = [{"title":x} for x in titles]
                    except Exception as e:
                        logger.exception(e)

                    hymns = result.get("hymns")
                    if hymns and len(hymns)>last_len_hymns:
                        for k in ["composer","album","lyrics","artist","play_url","sheet_url","ppt_url","copyright"]:
                            try:
                                data = extract_json_values_robust(all_content, k)
                                if data and len(data)<=len(hymns):
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
                        ori_msg.feedback_text = unescape_json_string(detail)
                        logger.info(f"_chat_detail: {all_content} \n got {detail}")
                # else:
                #     ori_msg.feedback_text = all_content
                # logger.info(f"CONVERSATION_MESSAGE_DELTA: {ori_msg.feedback}")
                ori_msg.status = 1
                session.commit()
            elif event.event == ChatEventType.CONVERSATION_MESSAGE_COMPLETED and event.message.type == MessageType.ANSWER:
                logger.info(f"_chat_with_coze: {user_id, ori_msg.id} done, cost:{time.time() - start_time} s")
                # logger.info(f"CONVERSATION_MESSAGE_COMPLETED: {event.message.content}")
                return event.message.content
            # elif event.event == ChatEventType.CONVERSATION_CHAT_COMPLETED:
            #     logger.info(f"CONVERSATION_CHAT_COMPLETED: {event.chat.usage.token_count}")
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


