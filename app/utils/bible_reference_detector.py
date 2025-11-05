import re


def tag_bible_references(text):
    """
    识别文本中的圣经出处并使用<u class="bible">标签进行包裹

    Args:
        text (str): 输入文本

    Returns:
        str: 标注后的文本
    """

    # 中文圣经卷名缩写列表
    chinese_abbrs = [
        # 旧约
        '创', '出', '利', '民', '申', '书', '士', '得', '撒上', '撒下',
        '王上', '王下', '代上', '代下', '拉', '尼', '斯', '伯', '诗', '箴',
        '传', '歌', '赛', '耶', '哀', '结', '但', '何', '珥', '摩', '俄',
        '拿', '弥', '鸿', '哈', '番', '该', '亚', '玛',
        # 新约
        '太', '可', '路', '约', '徒', '罗', '林前', '林后', '加', '弗',
        '腓', '西', '帖前', '帖后', '提前', '提后', '多', '门', '来', '雅',
        '彼前', '彼后', '约一', '约二', '约三', '犹', '启'
    ]

    # 中文圣经卷名全称列表
    chinese_full_names = [
        # 旧约
        '创世记', '出埃及记', '利未记', '民数记', '申命记', '约书亚记', '士师记', '路得记',
        '撒母耳记上', '撒母耳记下', '列王纪上', '列王纪下', '历代志上', '历代志下',
        '以斯拉记', '尼希米记', '以斯帖记', '约伯记', '诗篇', '箴言', '传道书', '雅歌',
        '以赛亚书', '耶利米书', '耶利米哀歌', '以西结书', '但以理书', '何西阿书', '约珥书',
        '阿摩司书', '俄巴底亚书', '约拿书', '弥迦书', '那鸿书', '哈巴谷书', '西番雅书',
        '哈该书', '撒迦利亚书', '玛拉基书',
        # 新约
        '马太福音', '马可福音', '路加福音', '约翰福音', '使徒行传', '罗马书', '哥林多前书',
        '哥林多后书', '加拉太书', '以弗所书', '腓立比书', '歌罗西书', '帖撒罗尼迦前书',
        '帖撒罗尼迦后书', '提摩太前书', '提摩太后书', '提多书', '腓利门书', '希伯来书',
        '雅各书', '彼得前书', '彼得后书', '约翰一书', '约翰二书', '约翰三书', '犹大书', '启示录'
    ]

    # 英文圣经卷名缩写列表
    english_abbrs = [
        # 旧约
        'Gen', 'Ex', 'Lev', 'Num', 'Deut', 'Josh', 'Judg', 'Ruth', '1Sam', '2Sam',
        '1Kgs', '2Kgs', '1Chr', '2Chr', 'Ezra', 'Neh', 'Esth', 'Job', 'Ps', 'Prov',
        'Eccl', 'Song', 'Isa', 'Jer', 'Lam', 'Ezek', 'Dan', 'Hos', 'Joel', 'Amos',
        'Obad', 'Jonah', 'Mic', 'Nah', 'Hab', 'Zeph', 'Hag', 'Zech', 'Mal',
        # 新约
        'Matt', 'Mark', 'Luke', 'John', 'Acts', 'Rom', '1Cor', '2Cor', 'Gal', 'Eph',
        'Phil', 'Col', '1Thess', '2Thess', '1Tim', '2Tim', 'Titus', 'Phlm', 'Heb',
        'Jas', '1Pet', '2Pet', '1John', '2John', '3John', 'Jude', 'Rev'
    ]

    # 英文圣经卷名全称列表
    english_full_names = [
        # 旧约
        'Genesis', 'Exodus', 'Leviticus', 'Numbers', 'Deuteronomy', 'Joshua', 'Judges',
        'Ruth', '1Samuel', '2Samuel', '1Kings', '2Kings', '1Chronicles', '2Chronicles',
        'Ezra', 'Nehemiah', 'Esther', 'Job', 'Psalms', 'Proverbs', 'Ecclesiastes',
        'Song of Songs', 'Isaiah', 'Jeremiah', 'Lamentations', 'Ezekiel', 'Daniel',
        'Hosea', 'Joel', 'Amos', 'Obadiah', 'Jonah', 'Micah', 'Nahum', 'Habakkuk',
        'Zephaniah', 'Haggai', 'Zechariah', 'Malachi',
        # 新约
        'Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1Corinthians', '1 Corinthians',
        '2Corinthians', '2 Corinthians', 'Galatians', 'Ephesians', 'Philippians', 'Colossians',
        '1Thessalonians', '1 Thessalonians', '2Thessalonians', '2 Thessalonians',
        '1Timothy', '1 Timothy', '2Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews',
        'James', '1Peter', '1 Peter', '2Peter', '2 Peter', '1John', '1 John', '2John', '2 John',
        '3John', '3 John', 'Jude', 'Revelation'
    ]

    # 繁体中文圣经卷名缩写列表
    traditional_chinese_abbrs = [
        # 旧约
        '創', '出', '利', '民', '申', '書', '士', '得', '撒上', '撒下',
        '王上', '王下', '代上', '代下', '拉', '尼', '斯', '伯', '詩', '箴',
        '傳', '歌', '賽', '耶', '哀', '結', '但', '何', '珥', '摩', '俄',
        '拿', '彌', '鴻', '哈', '番', '該', '亞', '瑪',
        # 新約
        '太', '可', '路', '約', '徒', '羅', '林前', '林後', '加', '弗',
        '腓', '西', '帖前', '帖後', '提前', '提後', '多', '門', '來', '雅',
        '彼前', '彼後', '約一', '約二', '約三', '猶', '啟'
    ]

    # 章节格式的正则表达式模式
    # 支持:
    # - 章节号: 12:34
    # - 章节号范围: 12:34-35, 12:34-13:1
    # - 多个不连续节号: 12:34,36,38
    # - 章节号带字母: 12:34a
    verse_pattern = r'''
        (?:
            \d+:\d+[a-z]?        # 单节，如 12:34 或 12:34a
            (?:
                -                # 范围分隔符
                (?:
                    \d+:\d+[a-z]?# 跨章范围，如 34-13:1
                    |
                    \d+[a-z]?    # 同章内范围，如 34-35 或 34a-35b
                )
            )?
            |
            \d+                  # 整章，如 12
            (?:
                -                # 整章范围，如 12-13
                \d+
            )?
        )
        (?:
            ,                    # 多个不连续的章节引用
            \s*                  # 可能的空格
            (?:
                \d+:\d+[a-z]?    # 单节，如 34 或 34a
                (?:
                    -            # 范围分隔符
                    (?:
                        \d+:\d+[a-z]?# 跨章范围，如 34-13:1
                        |
                        \d+[a-z]?# 同章内范围，如 34-35
                    )
                )?
                |
                \d+              # 整章，如 12
                (?:
                    -            # 整章范围，如 12-13
                    \d+
                )?
            )
        )*
    '''

    # 语言检测和处理函数
    def detect_and_process_language(book_patterns, text):
        """检测并处理特定语言的圣经引用"""
        # 对书卷名称进行排序，确保较长的名称先匹配
        sorted_books = sorted(book_patterns, key=lambda x: len(x), reverse=True)
        book_pattern = '|'.join(re.escape(book) for book in sorted_books)

        # 构建完整的正则表达式
        regex_pattern = re.compile(
            r'''
            (                       # 第1组：整个匹配
                (?:\(?)             # 可选的左括号
                (                   # 第2组：圣经引用内容（不包含括号）
                    (''' + book_pattern + r''')  # 第3组：书卷名称
                    \s*             # 书卷名和章节之间的可选空格
                    (''' + verse_pattern + r''') # 第4组：章节部分
                )
                (?:\)?)             # 可选的右括号
            )
            ''',
            re.VERBOSE | re.IGNORECASE
        )

        def replace_match(match):
            """修正后的替换函数：不包含括号"""
            full_match = match.group(1)  # 完整匹配，包含括号
            bible_content = match.group(2)  # 圣经引用内容，不包含括号

            # 检查是否有括号
            has_left_paren = full_match.startswith('(')
            has_right_paren = full_match.endswith(')')

            # 重建内容，保持原有括号在外面
            result = ''
            if has_left_paren:
                result += '('

            result += f'<u class="bible">{bible_content}</u>'

            if has_right_paren:
                result += ')'

            return result

        # 检查是否有匹配
        if regex_pattern.search(text):
            # 执行替换
            return regex_pattern.sub(replace_match, text), True
        return text, False

    # 检测中文圣经引用
    chinese_books = chinese_abbrs + chinese_full_names
    result, chinese_detected = detect_and_process_language(chinese_books, text)

    if chinese_detected:
        return result

    # 检测繁体中文圣经引用
    result, traditional_chinese_detected = detect_and_process_language(traditional_chinese_abbrs, result)

    if traditional_chinese_detected:
        return result

    # 检测英文圣经引用
    english_books = english_abbrs + english_full_names
    result, english_detected = detect_and_process_language(english_books, result)

    return result


# 示例用法
if __name__ == "__main__":
    test_texts = [
        # 中文示例
        "圣经中说：(创 1:1) 起初神创造天地。",
        "耶稣说：(约 3:16) 神爱世人，甚至将他的独生子赐给他们。",
        "圣经教导我们要爱人如己(利 19:18)，这是最大的诫命之一。",
        "保罗写道：(罗 8:28) 万事都互相效力，叫爱神的人得益处。",
        "我们可以在(诗 23:1-6)中找到安慰，这是大卫的诗篇。",
        "先知以赛亚说：(赛 53:5) 他为我们的过犯受害，为我们的罪孽压伤。",

        # 英文示例
        "For God so loved the world (John 3:16) that he gave his one and only Son.",
        "The Lord is my shepherd (Ps 23:1), I lack nothing.",
        "Faith without works is dead (James 2:26).",
        "In the beginning God created the heavens and the earth (Gen 1:1).",
        "Love your neighbor as yourself (Lev 19:18).",

        # 繁体中文示例
        "聖經中說：(創 1:1) 起初神創造天地。",
        "耶穌說：(約 3:16) 神愛世人，甚至將他的獨生子賜給他們。",

        # 混合示例
        "圣经告诉我们(创 1:1)和John 3:16都是重要的经文。",
        "我们应当记住(诗 23:1)和(腓 4:13)中的教导。",

        # 复杂章节格式示例
        "请阅读(太 5:1-12)中的登山宝训。",
        "这段教导可以在(林前 13:1-13)找到。",
        "参考(出 20:1-17)的十诫和(申 5:6-21)的重复。",
        "重要的应许在(约 14:1-6, 16:7-15)中。",
        "请比较(赛 53:1-12)和(彼前 2:24-25)的内容。",
        "这段经文在(诗 119:105)中：'你的话是我脚前的灯，是我路上的光。'",

        # 完整书名示例
        "在(创世记 1:1)中我们看到上帝的创造大能。",
        "耶稣在(马太福音 5:1-12)中讲论了八福。",
        "保罗在(哥林多前书 13:1-13)中论到爱的真谛。",

        # 整章引用示例
        "请阅读(诗篇 23)这整篇诗篇。",
        "保罗的问候在(罗马书 1)中。",

        # 跨章节引用示例
        "这段叙事从(创世记 12:1)延续到(创世记 25:10)。",
        "耶稣的家谱记载在(马太福音 1:1-17)和(路加福音 3:23-38)。"
    ]

    test_texts = ["看到你再次寻找编号123的赞美诗，这份对敬拜的渴慕本身就是蒙神喜悦的！即使暂时未明确诗歌内容，神依然在我们的寻求中与我们相遇。\n\n**“你们要赞美耶和华！我的心哪，你要赞美耶和华。”（诗146:1）**\n\n就像大卫无论身处顺境逆境都以赞美为祭，我们也可以在等待中用心灵和诚实敬拜。或许可以尝试哼唱你熟悉的诗歌片段，或默想诗篇中的赞美话语，让敬拜的焦点从“找到特定诗歌”转向“遇见赐诗歌的神”。下次灵修时，不妨写下你此刻心中浮现的对神的感谢，这些真挚的心声也是最美的“即兴赞美诗”哦！"]

    print("=== 圣经出处标注示例 ===\n")
    for i, text in enumerate(test_texts, 1):
        print(f"原文 {i}: {text}")
        tagged = tag_bible_references(text)
        print(f"标注 {i}: {tagged}")
        print("-" * 80)
