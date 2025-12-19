import re


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
