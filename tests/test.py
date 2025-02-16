from pypinyin import pinyin, Style
def name_to_pinyin(text):
    # 使用pypinyin进行转换，普通风格
    result = pinyin(text, style=Style.NORMAL ,heteronym=False)
    # 提取拼音并首字母大写，不加空格
    pinyin_str = "".join([item[0].capitalize() for item in result])
    return pinyin_str


if __name__ == "__main__":
    print(name_to_pinyin("张三"))
