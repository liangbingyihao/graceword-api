import re


def extract_json_values_robust(text, key):
    """
    更健壮的提取方法，处理各种格式问题
    """

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
      '''
    ]
    for i, test in enumerate(test_cases, 1):
        result = extract_json_values_robust(test, "title")
        titles = {"hymns":[{"title":x} for x in result]}
        print(f"测试 {i}: {result},{titles}")
