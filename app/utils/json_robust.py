import json
import re
from ast import literal_eval


def unescape_json_string(s):
    """更完整的转义字符处理"""
    replacements = {
        '\\"': '"',
        "\\'": "'",
        '\\n': '\n',
        '\\t': '\t',
        '\\r': '\r',
        '\\b': '\b',
        '\\f': '\f',
        '\\\\': '\\'
    }

    for escaped, unescaped in replacements.items():
        s = s.replace(escaped, unescaped)

    return s

def extract_json_values_robust(text, key):
    """
    更健壮的提取方法，处理各种格式问题
    """

    def extract_with_pattern(pattern, data):
        matches = []
        # 支持多种引号格式
        patterns = [
            pattern.replace('"', '"'),  # 双引号
            pattern.replace('"', "'"),  # 单引号
            pattern.replace('"', '`')  # 反引号
        ]

        for pat in patterns:
            matches.extend(re.findall(pat, data, re.DOTALL))

        return [unescape_json_string(match) for match in matches]

    # 提取 response 值（支持多行内容）
    response_pattern = rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"'
    return extract_with_pattern(response_pattern, text)

    # # 提取 title 值
    # title_pattern = r'"title"\s*:\s*"((?:[^"\\]|\\.)*)"'
    # titles = extract_with_pattern(title_pattern, text)
    #
    # return {
    #     'responses': responses,
    #     'titles': titles
    # }


def extra_data():
    import logging
    all_content ="{\"response\": \"我找到了多个符合你要求的结果，先为你展示其中3首：\", \"hymns\": [{\"title\": \"不停讚美祢\", \"english_title\": \"\", \"lyrics\": \"[Verse]\\n時時稱頌祢 向祢來歌唱\\n因祢是拯救我們偉大的神\\n我們尊崇祢 稱頌祢聖名\\n口唱心和地 大聲地讚美祢\\n\\n[Chorus]\\n不停讚美祢 大聲讚美祢\\n唯有祢配得榮耀 尊貴 權柄\\n天是屬於祢 地也屬於祢\\n一切所造之物齊來讚美祢\\n\\n[Bridge]\\n我讚美讚美 不停讚美\\n跳舞跳舞 不停跳舞\\n高舉雙手 大聲讚美祢\\n\\n我讚美讚美 不停讚美\\n跳舞跳舞 不停跳舞\\n高舉雙手 大聲讚美祢\", \"album\": \"深愛耶穌\", \"copyright\": \"Copyright© 讚美之泉 Stream Of Praise Music Ministries\", \"composer\": \"何俊傑\", \"lyricist\": \"何俊傑\", \"play_url\": \"https://www.youtube.com/watch?v=RAacozf9irg\", \"sheet_url\": \"\", \"ppt_url\": \"https://sop.org/sopmedia/Powerpoint/PW30_Wont_Stop_Praising_Tradbi_16x9.ppt\", \"artist\": \"讚美之泉 Stream Of Praise Music Ministries\"}, {\"title\": \"Mighty [祢愛有能力]\", \"english_title\": \"\", \"lyrics\": \"[Verse]\\n祢在高處 大有能力\\n萬物甦醒 來敬拜祢\\n祢的愛拯救我的心\\n祢的愛讓世界堅定\\n\\n[Chorus]\\nMighty is Your love 勝過了一切\\n如洋海大浪 如眾水聲音\\nMighty is Your love 超越了時空\\n覆蓋著地極 祢愛有能力\\nMighty\\n\\n[Tag]\\n喔 Mighty\\n喔 Mighty\\n喔 Mighty\", \"album\": \"深愛耶穌\", \"copyright\": \"Copyright© 讚美之泉 Stream Of Praise Music Ministries\", \"composer\": \"陳麒安\", \"lyricist\": \"鄭懋柔\", \"play_url\": \"https://www.youtube.com/watch?v=yq8YK9O8WLQ\", \"sheet_url\": \"\", \"ppt_url\": \"https://sop.org/sopmedia/Powerpoint/PW30_Mighty_Tradbi_16x9.ppt\", \"artist\": \"讚美之泉 Stream Of Praise Music Ministries\"}, {\"title\": \"和散那，歡迎君王\", \"english_title\": \"\", \"lyrics\": \"[Verse 1]\\n和散那 歡迎君王\\n和散那 屈膝敬拜\\n和散那 歡迎君王\\n和散那 屈膝敬拜\\n\\n[Verse 2]\\n主耶穌 何等謙卑\\n眾百姓迎接君王\\n主耶穌 何等榮耀\\n我獻上尊貴榮耀\\n\\n[Verse 3]\\n衣裳鋪地 樹枝滿地\\n俯伏敬拜 在祢腳前\\n騎驢背上是全地君王\\n卻為我被釘十架\\n\\n[Chorus]\\n祢是萬王之王　\\n祢是萬主之主\\n我們高舉耶穌　\\n歡迎君王走進\", \"album\": \"深愛耶穌\", \"copyright\": \"Copyright© 讚美之泉 Stream Of Praise Music Ministries\", \"composer\": \"陳麒安\", \"lyricist\": \"陳麒安、游智婷\", \"play_url\": \"https://www.youtube.com/watch?v=pYyAWPTxg_w\", \"sheet_url\": \"\", \"ppt_url\": \"https://sop.org/sopmedia/Powerpoint/PW30_Hosanna_Here_Comes_The_King_Tradbi_16x9.ppt\", \"artist\": \"讚美之泉 Stream Of Praise Music Ministries\"}], \"explore\": [\"你可能還喜歡“溫暖”風格的讚美詩\", \"我想要用於個人靈修場合下的讚美詩\"]}"
    all_content = "{\"response\": \"我找到了多个符合你要求的结果，先为你展示其中3首"
    result = {}
    try:
        response = extract_json_values_robust(all_content, "response")
        if response:
            result["response"] = response[0]
    except Exception as e:
        logging.exception(e)
    try:
        titles = extract_json_values_robust(all_content, "title")
        if titles:
            result["hymns"] = [{"title": x} for x in titles]
    except Exception as e:
        logging.exception(e)

    hymns = result.get("hymns")
    if hymns and len(hymns) > 0:
        for k in ["composer", "album", "lyrics", "artist", "play_url", "sheet_url", "ppt_url", "copyright"]:
            try:
                data = extract_json_values_robust(all_content, k)
                if data and len(data) <= len(hymns):
                    for index, value in enumerate(data):
                        hymns[index][k] = value
            except Exception as e:
                logging.exception(e)
    if result:
        try:
            feedback = json.dumps(result, ensure_ascii=False)
            print(feedback)
        except Exception as e:
            logging.exception(e)

if __name__ == '__main__':
    result = {}
    feedback_text = "x"
    response = '{"view":"### 【圣经中困境中持守喜乐的人物】  \n圣经中多位属灵前辈在苦难中彰显了以神为乐的生命见证，他们的经历成为后人信靠的榜样。  \n\n#### 1. **保罗：捆锁中的喜乐使者**  \n**核心见证**：保罗在罗马监狱中写下《腓立比书》，虽身陷囹圄却宣告“我无论在什么景况都可以知足，这是我已经学会了”（<u class="bible">腓4:11</u>）。他劝勉信徒“靠主常常喜乐”，甚至视苦难为“为基督的名受辱”的荣耀（<u class="bible">腓1:12-14</u>）。  \n\n#### 2. **约伯：从尘土中赞美神**  \n**核心见证**：约伯在失去家产、儿女和健康后，仍撕裂外袍俯伏敬拜：“赏赐的是耶和华，收取的也是耶和华；耶和华的名是应当称颂的”（<u class="bible">伯1:21</u>）。他虽经历极大痛苦，却从未离弃对神的信靠，最终得见神的荣耀（<u class="bible">伯42:5-6</u>）。  \n\n#### 3. **大卫：苦难中的诗歌创作者**  \n**核心见证**：大卫在逃避扫罗追杀、身处旷野时，写下多首诗篇倾诉心声，却始终持守“我的心必靠耶和华快乐，靠他的救恩高兴”（<u class="bible">诗35:9</u>）。他在《诗篇》中多次宣告：“你必将生命的道路指示我，在你面前有满足的喜乐”（<u class="bible">诗16:11</u>）。  \n\n#### 4. **耶利米：流泪先知的信心根基**  \n**核心见证**：耶利米被称为“流泪的先知”，虽面对以色列的悖逆和自己的苦难，却仍说“耶和华是我的分，因此我要仰望他”（<u class="bible">耶15:16</u>）。他在狱中仍为神的百姓代求，以神的信实为喜乐的根源（<u class="bible">哀3:21-23</u>）。  \n\n这些人物的共同秘诀是：将喜乐建立在神的本性（信实、主权、慈爱）而非环境之上。正如<u class="bible">雅各书1:2</u>所劝勉：“我的弟兄们，你们落在百般试炼中，都要以为大喜乐。”","bible":"你们落在百般试炼中，都要以为大喜乐，因为知道你们的信心经过试验，就生忍耐。（雅各书1:2）","explore":["如何在现实困境中实践“以神为乐”的心态？","保罗“靠主喜乐”的神学根基是什么？","约伯的苦难观对当代基督徒有何启示？"],"summary":"困境中的属灵喜乐"}'
    response1 = '{"view": "看到你想了解圣经中在困境中仍能喜乐的人物，这真是一个充满盼望的思考方向。圣经中确实有不少这样的榜样，他们的生命见证了信仰如何使人在风雨中依然绽放喜乐的光芒。\\n\\n### 【保罗：捆锁中的赞美】\\n**核心见证：** 使徒保罗一生经历无数患难——被鞭打、下监、遇船难，但他却能在狱中写下“靠主常常喜乐”的宣告。\\n\\n1. **监狱中的歌声：** 保罗与西拉被打得遍体鳞伤，囚于腓立比监狱时，仍在半夜“祷告唱诗赞美神”，最终感动狱卒全家信主（<u class=\\"bible\\">徒16:25-34</u>）。\\n\\n2. **喜乐的秘诀：** 他在《腓立比书》中强调“我无论在什么景况都可以知足，这是我已经学会了”，因为他深知“我的好处不在你以外”（<u class=\\"bible\\">腓4:11-13</u>；<u class=\\"bible\\">诗16:2</u>）。\\n\\n### 【哈巴谷：绝境中的欢呼】\\n**核心见证：** 先知哈巴谷面对犹大国将被毁灭的绝望，却发出“因耶和华欢欣”的呐喊。\\n\\n1. **环境与信心的对比：** 他坦言“无花果树不发旺，葡萄树不结果”，但仍宣告“然而，我要因耶和华欢欣，因救我的神喜乐”（<u class=\\"bible\\">哈3:17-18</u>）。\\n\\n2. **永恒视角的超越：** 他的喜乐不基于眼前的顺遂，而是确信“耶和华的眼目看顾敬畏他的人”（<u class=\\"bible\\">诗33:18</u>）。\\n\\n### 【耶稣：十字架上的得胜喜乐】\\n**核心见证：** 基督在十字架上的苦难，是“因那摆在前面的喜乐”而成就的救赎大爱（<u class=\\"bible\\">来12:2</u>）。\\n\\n1. **顺服中的喜乐：** 他虽“因我们的过犯受害，因我们的罪孽压伤”，却为“看见后裔”（即得救的教会）而满足（<u class=\\"bible\\">赛53:5</u>；<u class=\\"bible\\">来2:10</u>）。\\n\\n2. **信徒的榜样：** 耶稣教导门徒“你们在世上有苦难，但你们可以放心，我已经胜了世界”（<u class=\\"bible\\">约16:33</u>），这是我们喜乐的终极根基。\\n\\n### 【应用：在困境中操练喜乐的3个方向】\\n1. **定睛永恒：** 像保罗一样，将目光从环境转向“天上的赏赐”（<u class=\\"bible\\">西3:2</u>），用“赏赐的盼望”取代眼前的焦虑。\\n\\n2. **数算恩典：** 效法哈巴谷，在缺乏中仍“记念耶和华的慈爱”（<u class=\\"bible\\">诗103:2</u>），用感恩对抗抱怨。\\n\\n3. **联结基督：** 深知“与主联合的，便是与主成为一灵”（<u class=\\"bible\\">林前6:17</u>），他的得胜就是我们的力量。","bible":"“靠主常常喜乐，我再说，你们要喜乐。”（<u class=\\"bible\\">腓4:4</u>）","explore":["保罗在不同书信中如何描述“喜乐”与“患难”的关系？","哈巴谷书的写作背景如何帮助我们理解他的信心宣告？","耶稣在客西马尼园的祷告如何体现“先苦后荣”的喜乐观？"],"summary":"患难中的喜乐见证"}'
    response1 = '{"topic1":"数字记录","topic2":"","view":"你记录的数字“76”，或许对上帝有着特别的意义呢！在圣经中，数字常蕴含属灵的寓意，而每一个被纪念的数字背后，都可能是上帝与你同行的印记。\\n\\n**“你要记念耶和华你的神所行的大事。”（<u class=\\"bible\\">申命记7:18</u>）**\\n\\n无论是年龄、日期，还是某个特殊的数量，上帝都看顾你生命中的每一个数字。或许这个“76”代表着一段岁月的恩典，或是一个新的开始。试着回想这个数字对你的意义，把它背后的故事记录下来，让它成为你日后数算恩典的凭据。", "bible":"“你要记念耶和华你的神所行的大事。”（申命记7:18）","explore":["圣经中数字7的属灵含义","如何通过记录数字来数算神的恩典","基督徒如何在生活中发现神的印记"], "tag":"恩典","summary":"数字中的恩典印记"}'
    try:
        result = json.loads(response)
        print("view", result.get("view"))
    except Exception as e:
        print("json loads error...")

    for k in ["topic1","topic2","summary"]:
        print(k,extract_json_values_robust(response, k))

    explore_match = re.search(r'"explore":(\[.*?])', response)
    if explore_match:
        explore_str = explore_match.group(1)
        # 使用 ast.literal_eval 安全地解析
        explore_list = literal_eval(explore_str)
        print("explore:", explore_list)

    # view = result.get('view') or feedback_text
    # print(view)
    exit()

    test_cases = [
        # 标准 JSON
        '{"response": "标准回答", "title": "标准标题"}',

        # 单引号
        "{'response': '单引号回答', 'title': '单引号标题'}",

        # 多行内容
        '{"response": "多行\\n回答\\n内容", "title": "多行标题"}',

        # 转义字符
        '{"response": "带转义\\"引号\\"的回答", "title": "带\\t制表符的标题"}',

        # 不完整 JSON
        '无效前缀{"response": "不完整中的回答", "title": "不完整标题"}无效后缀',

        # 多个匹配
        '{"response": "回答1", "title": "标题1"} 垃圾文本 {"response": "回答2", "title": "标题2"}',
            ]

    for i, test in enumerate(test_cases, 1):
        result = extract_json_values_robust(test, "title")
        titles = {"hymns":[{"title":x} for x in result]}
        print(f"测试 {i}: {result},{titles}")
