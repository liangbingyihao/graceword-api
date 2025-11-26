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
        '''{
  "response": "我找到了 1 个符合你要求的结果哦，你看看是否符合你当下的需求",
  "hymns": [
    {
      "title": "想起祢 (When I think of You)",
      "english_title": "When I think of You",'
      ''',
        '''{"topic1": "", "topic2": "数字记录", "view": "看到你记录了数字“7”，这让我想到在圣经中，“7”是一个充满恩典与完全的数字。上帝用六日创造天地，第七日安息，设立了安息日，预表祂的恩典使我们得以在祂里面得着真正的歇息。\n\n**“到第七日，神造物的工已经完毕，就在第七日歇了他一切的工，安息了。”（<u class=\"bible\">创2:2</u>）**\n\n在信仰生活中，“7”也常提醒我们上帝的信实与预备。无论是旧约中七天的洁净礼仪，还是新约中耶稣治愈病人时多次提及的“七”，都指向上帝完备的恩典。或许你记录这个数字，正是圣灵在提醒你：上帝的工作总是完全的，祂对你的带领也必如七日的创造般有序且充满智慧。试着回想近期经历中，上帝在哪些时刻让你看见祂“完全”的恩典呢？可以记录下来哦，这会成为你信心的印记。", "bible": "“到第七日，神造物的工已经完毕，就在第七日歇了他一切的工，安息了。”（创2:2）", "explore": ["圣经中“7”在不同经文的象征意义", "安息日作为“第七日”的属灵意义", "如何在生活中实践“第七日”的安息真理"], "tag": "恩典", "summary": "恩典的完全数", "color_tag": "#E8FFFF", "topic": "数字记录"}
        '''
    ]

    for i, test in enumerate(test_cases, 1):
        result = extract_json_values_robust(test, "title")
        titles = {"hymns":[{"title":x} for x in result]}
        print(f"测试 {i}: {result},{titles}")
