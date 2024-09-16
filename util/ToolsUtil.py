import re
import json
import os
import time


# 提取两个字符串之间的内容
def extract_string_between(source_string, start_string, end_string):
    start_index = source_string.find(start_string) + len(start_string)
    end_index = source_string.find(end_string)
    extracted_string = source_string[start_index:-37]
    return extracted_string


# 去除多余的空格
def replace_multiple_spaces(string):
    pattern = r'\s+'
    replaced_string = re.sub(pattern, ' ', string)
    return replaced_string


# 替换十六进制编码
def process_old_html(message):
    def replace_hex(match):
        hex_value = match.group(0)
        byte_value = bytes(hex_value, 'utf-8').decode('unicode_escape')
        return byte_value

    new_text = re.sub(r'\\x[0-9a-fA-F]{2}', replace_hex, message)
    start_string = "html:'"
    end_string = "',opuin"
    new_text = extract_string_between(new_text, start_string, end_string)
    new_text = replace_multiple_spaces(new_text).replace('\\', '')
    return new_text


def show_author_info():
    CYAN = '\033[36m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    RESET = '\033[0m'
    RED = '\033[31m'

    author_art = r'''
░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓███████▓▒░  ░▒▓███████▓▒░   ░▒▓██████▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓███████▓▒░  
░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓███████▓▒░  ░▒▓███████▓▒░  ░▒▓████████▓▒░ ░▒▓████████▓▒░ ░▒▓███████▓▒░  
░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░        
░▒▓█▓▒░        ░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░        
░▒▓████████▓▒░ ░▒▓█▓▒░ ░▒▓███████▓▒░  ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░░▒▓█▓▒░ ░▒▓█▓▒░        
'''

    print(CYAN + author_art + RESET)

    author_info = f"{YELLOW}bilibili{RESET} {BLUE}@高数带我飞{RESET} {YELLOW}GetQzonehistory V1.0{RESET}"
    print(author_info)
    print(f'{RED}程序完全免费，且在github开源！！！！{RESET}')
    print(f'{RED}程序完全免费，且在github开源！！！！{RESET}')
    print(f'{RED}程序完全免费，且在github开源！！！！{RESET}')


def get_html_template():
    # HTML模板
    # HTML模板
    html_template = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>QQ空间动态</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
            }}
            .post {{
                background-color: #333;
                color: #fff;
                padding: 20px;
                margin: 20px;
                border-radius: 10px;
            }}
            .avatar {{
                float: left;
                margin-right: 20px;
            }}
            .avatar img {{
                width: 50px;
                height: 50px;
                border-radius: 50%;
            }}
            .content {{
                overflow: hidden;
            }}
            .nickname {{
                font-size: 1.2em;
                font-weight: bold;
            }}
            .time {{
                color: #999;
                font-size: 0.9em;
            }}
            .message {{
                margin-top: 10px;
                font-size: 1.1em;
            }}
            .image {{
                margin-top: 10px;
                display: flex;
                justify-content: space-around;
                align-items: center; /* 使两张图片垂直对齐 */
                padding: 20px;
            }}
            .image img {{
                max-width: 33vw;
                max-height: 33vh;
                border-radius: 10px;
                cursor: pointer;
            }}
            .comments {{
                margin-top: 5px; /* 调整这里的值来减少间距 */
                background-color: #444;
                padding: 2px 10px 10px 10px;
                border-radius: 10px;
            }}
            .comment {{
                margin-top: 10px; /* 调整单个评论之间的间距 */
                padding: 10px;
                background-color: #555;
                border-radius: 10px;
                color: #fff;
            }}
            .comment .avatar img {{
                width: 30px;
                height: 30px;
            }}
            .comment .nickname {{
                font-size: 1em;
                font-weight: bold;
            }}
            .comment .time {{
                font-size: 0.8em;
                color: #aaa;
            }}
        </style>
    </head>
    <body>

        {posts}
        <script>
            // 为所有图片添加点击事件
            document.querySelectorAll(".image img").forEach(img => {{
                img.addEventListener("click", function() {{
                    window.open(this.src, '_blank');  // 打开图片链接并在新标签页中展示
                }});
            }});
        </script>
    </body>
    </html>
    """

    # 生成每个动态的HTML内容
    post_template = """
    <div class="post">
        <div class="avatar">
            <img src="{avatar_url}" alt="头像">
        </div>
        <div class="content">
            <div class="nickname">{nickname}</div>
            <div class="time">{time}</div>
            <div class="message">{message}</div>
            {image}
        </div>
         {comments}
    </div>
    """

    # 评论区HTML模板
    comment_template = """
    <div class="comments">
        <div class="comment">
            <div class="avatar">
                <img src="{avatar_url}" alt="评论头像">
            </div>
            <div class="nickname">{nickname}</div>
            <div class="time">{time}</div>
            <div class="message">{message}</div>
        </div>
    </div>
    """

    return html_template, post_template, comment_template


# 格式化时间
def format_timestamp(timestamp):
    time_struct = time.localtime(timestamp)
    formatted_time = time.strftime("%Y年%m月%d日 %H:%M:%S", time_struct)
    return formatted_time


# 判断json是否合法
def is_valid_json(json_data):
    try:
        json_object = json.loads(json_data)  # 尝试解析JSON数据
        return True  # 解析成功，是有效的JSON
    except ValueError as e:  # 解析失败，捕获异常
        print(e)
        return False  # 解析失败，不是有效的JSON


# 写入信息
def write_txt_file(workdir, file_name, data):
    if not os.path.exists(workdir):
        os.makedirs(workdir)
    base_path_file_name = os.path.join(workdir, file_name)
    with open(base_path_file_name, 'w', encoding='utf-8') as file:
        file.write(data)


# 读取文件信息
def read_txt_file(workdir, file_name):
    base_path_file_name = os.path.join(workdir, file_name)
    if os.path.exists(base_path_file_name):
        with open(base_path_file_name, 'r', encoding='utf-8') as file:
            return file.read()
    return None


# QQ空间表情替换 [em]xxx[/em] 为 <img src="http://qzonestyle.gtimg.cn/qzone/em/xxx.gif">
def replace_em_to_img(match):
    # 获取匹配的 xxx 部分
    emoji_code = match.group(1)
    return f'<img src="http://qzonestyle.gtimg.cn/qzone/em/{emoji_code}.gif" alt="{emoji_code}">'

