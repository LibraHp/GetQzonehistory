import flet as ft
import requests
import base64
import re
import time
from datetime import datetime
import json
import threading
from bs4 import BeautifulSoup
from collections import Counter
import os
import pandas as pd
import pandas.io.clipboard as cb
import platform
from pathlib import Path
import traceback

# 程序版本
version = "1.0.2"

is_debug = True

# 初始化所有消息列表
all_messages = []
# 初始化说说列表
user_says = []
# 初始化好友列表
friends = []
# 初始化转发列表
forward = []
# 初始化留言列表
leaves = []
# 初始换其他列表
other = []
# 初始化交互排行榜
interact_counter = []
# 初始化当前登录用户
now_login_user = None
# 初始化交互排行榜
most_interactive_user = None
# 初始化保存路径
save_path = None
# 日志组件引用
log_info_ref = ft.Ref[ft.Text]()
# 全局page
global_page = ft.Page

# 全局header
headers = {
    'authority': 'user.qzone.qq.com',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'cache-control': 'no-cache',
    'pragma': 'no-cache',
    'sec-ch-ua': '"Not A(Brand";v="99", "Microsoft Edge";v="121", "Chromium";v="121"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'none',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 '
                  'Safari/537.36 Edg/121.0.0.0',
}

def bkn(pSkey):
    # 计算bkn
    
    t, n, o = 5381, 0, len(pSkey)

    while n < o:
        t += (t << 5) + ord(pSkey[n])
        n += 1

    return t & 2147483647


def ptqrToken(qrsig):
    # 计算ptqrtoken
    n, i, e = len(qrsig), 0, 0

    while n > i:
        e += (e << 5) + ord(qrsig[i])
        i += 1

    return 2147483647 & e


def extract_string_between(source_string, start_string, end_string):
    start_index = source_string.find(start_string) + len(start_string)
    end_index = source_string.find(end_string)
    extracted_string = source_string[start_index:-37]
    return extracted_string


def replace_multiple_spaces(string):
    pattern = r'\s+'
    replaced_string = re.sub(pattern, ' ', string)
    return replaced_string


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


def parse_time_strings(time_str):
    today = datetime.today().date()  # 获取今天的日期
    try:
        if len(time_str) == 5:  # 格式为 HH:MM
            return datetime.combine(today, datetime.strptime(time_str, "%H:%M").time())
        elif "年" in time_str:  # 包含“年”的格式
            return datetime.strptime(time_str, "%Y年%m月%d日 %H:%M")
        elif "月" in time_str:  # 包含“月”的格式
            return datetime.strptime(time_str, "%m月%d日 %H:%M").replace(year=today.year)
        else:
            return datetime.now()  # 不符合任何格式时返回最早的时间
    except ValueError:
        return datetime.now()  # 如果解析失败，返回最早的时间

def get_big_img_dlg(img_url):
    return ft.AlertDialog(
        modal=False,
        title=ft.Text("查看大图"),
        content=ft.Column(
            controls=[
                ft.Image(src=img_url,height=500,fit=ft.ImageFit.FIT_HEIGHT),
            ]
        ),
    )

def log(message,type="info"):
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    log_info_ref.current.value = f"[{now}] - [{type}] {message}"

    # 写入日志到文件
    if is_debug:
        with open(f"log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{now}] - {message}\n")

    if type == "success":
        # 开头添加[success]
        log_info_ref.current.color = "green"
    elif type == "error":
        log_info_ref.current.color = "red"
    elif type == "debug":
        log_info_ref.current.color = "yellow"
    else:
        log_info_ref.current.color = "blue"
    global_page.update()


def clean_content():
    global all_messages, user_says, forward, leaves, other, friends, now_login_user, most_interactive_user
    try:
        # 统计互动次数最多的用户
        user_counter = Counter((message.user.username, message.user.uin) for message in all_messages if message.user)
        most_interactive_user = user_counter.most_common(10)
        # 好友去重，使用字典确保唯一性
        friends = list({friend.uin: friend for friend in friends if friend}.values())
        # 消息去重，使用消息内容作为键
        all_messages = list({message.content: message for message in all_messages if message.content}.values())
        # 按时间排序，确保消息有时间字段
        all_messages.sort(key=lambda x: x.time if x.time else datetime.min, reverse=True)
        # 清理并分类消息
        for message in all_messages:
            if not message or not message.content:
                continue  # 忽略无效消息
            content = message.content
            # 处理留言
            if '留言' in content:
                content = content.replace(now_login_user.username, '')
                leaves.append(message)
            # 处理转发
            elif '转发' in content:
                forward.append(message)
            # 处理当前用户发送的消息
            elif now_login_user.username in content:
                message.user = now_login_user
                content = content.replace(now_login_user.username + ' ：', '')
                user_says.append(message)
            # 处理其他类型的消息
            else:
                other.append(message)
                content = content.replace(now_login_user.username + ' ：', '')
            # 移除当前登录用户的名字
            message.content = content.replace(now_login_user.username, '')
    except Exception as e:
        print(traceback.format_exc())
        log(f"清理内容时发生错误: {e}", "error")


def save_image(url,file_name):
    global save_path
    valid_file_name = re.sub(r'[<>:"/\\|?*]', '_', file_name)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(f'{save_path}/{valid_file_name}.jpg', 'wb') as f:
                f.write(response.content)
                log(f"图片保存成功：{save_path}/{valid_file_name}.jpg")
    except Exception as e:
        log(e,"error")


class PaginatedContainer(ft.Column):
    def __init__(self, data, items_per_page=5, title="Title"):
        super().__init__()
        self.data = data
        self.items_per_page = items_per_page
        self.title = title
        self.current_page = 1
        self.total_pages = (len(data) - 1) // items_per_page + 1

        # 页面内容显示区域
        self.content_area = ft.Column(spacing=10, expand=True)
        # 页码显示区域
        self.page_info = ft.Text()
        # 输入框用于输入目标页码
        self.page_input = ft.TextField(label="跳转到页数", width=120)

        # 上一页按钮
        self.prev_button = ft.ElevatedButton("<", on_click=self.previous_page)
        # 下一页按钮
        self.next_button = ft.ElevatedButton(">", on_click=self.next_page)
        # 跳转按钮
        self.jump_button = ft.ElevatedButton("跳转", on_click=self.jump_to_page)

    def build(self):
        # 导出组件
        export_control = ft.PopupMenuButton(
            icon=ft.icons.SEND_AND_ARCHIVE,
            items=[
                ft.PopupMenuItem(text="导出为JSON", on_click=self.export_json),
                ft.PopupMenuItem(text="导出为Excel", on_click=self.export_excel),
                ft.PopupMenuItem(text="导出为Markdown", on_click=self.export_markdown),
            ],
            tooltip="导出为",
        )
        
        if self.data and isinstance(self.data[0], Message):
            export_control.items.append(
                ft.PopupMenuItem(text="导出为HTML", on_click=self.export_html)
            )
        
        return ft.Column(
            [
                ft.Row(
                    controls=[
                        ft.Text(self.title, size=20, weight="bold"),
                        ft.Row(
                            controls=[
                                ft.Text("导出为"),
                                export_control
                            ]
                        )
                        
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN
                ),
                # 主要内容区域
                ft.Container(
                    content=self.content_area,
                    expand=True,
                    padding=ft.padding.all(10),
                    alignment=ft.alignment.center,
                ),
                # 底部分页栏
                ft.Container(
                    content=ft.Row(
                        [
                            self.prev_button,
                            self.page_info,
                            self.next_button,
                            self.page_input,
                            self.jump_button,
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    alignment=ft.alignment.center,
                ),
            ],
            expand=True,
        )

    # 新增的跳转到指定页数的逻辑
    def jump_to_page(self, e):
        try:
            target_page = int(self.page_input.value)
            if 1 <= target_page <= self.total_pages:
                self.current_page = target_page
                self.update_page_info()
            else:
                log("请输入有效的页码。", "error")
        except ValueError:
            log("请输入有效的页码。", "error")
    
    def export_json(self,e):
        json_data = []
        for item in self.data:
            if isinstance(item, User):
                json_data.append({
                    "username": item.username,
                    "uin": item.uin,
                    "link": item.link,
                    "avatar_url": item.avatar_url
                })
            elif isinstance(item, Message):
                json_data.append({
                    "username": item.user.username,
                    "time": str(item.time),
                    "content": item.content,
                    "images": item.images,
                    "comment": item.comment.content if item.comment else None,
                    "avatar_url": item.user.avatar_url
                })

        # 将数据转换为 JSON 字符串
        json_string = json.dumps(json_data, ensure_ascii=False, indent=4)
        # 写入到文件
        try:
            with open(f"{save_path}/{now_login_user.uin}_{self.title}_data.json", "w", encoding="utf-8") as f:
                f.write(json_string)
            log(f"导出成功 请查看 {save_path}/{now_login_user.uin}_{self.title}_data.json","success")
        except Exception as e:
            log(e,"error")


    def export_excel(self,e):
        export_data = []
        for item in self.data:
            if isinstance(item, User):
                export_data.append({
                    'Type': 'User',
                    'Username': item.username,
                    'QQ': item.uin,
                    'Avatar URL': item.avatar_url
                })
            elif isinstance(item, Message):
                export_data.append({
                    'Type': 'Message',
                    'Username': item.user.username,
                    'Avatar URL': item.user.avatar_url,
                    'Time': str(item.time),
                    'Content': item.content,
                    'Images': item.images if item.images else '',
                    'Comment': item.comment.content if item.comment else '',
                })
        try:
            # 将数据转换为 DataFrame
            df = pd.DataFrame(export_data)
            # 保存为 Excel 文件
            df.to_excel(f"{save_path}/{now_login_user.uin}_{self.title}_data.xlsx", index=False)
            log(f"导出成功 请查看 {save_path}/{now_login_user.uin}_{self.title}_data.xlsx","success")
        except Exception as e:
            log(e,"error")


    def export_html(self, e):
        # HTML 头部和样式
        html_start = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Exported Data</title>
            <style>
                body {
                    font-family: 'Arial', sans-serif;
                    background-color: #f4f4f4;
                    display: flex;
                    justify-content: center;
                    align-items: flex-start;
                    height: 100vh;
                    margin: 0;
                    padding: 20px;
                }
                .card-container {
                    display: flex;
                    flex-direction: column;
                    gap: 20px;
                    width: 50%;
                }
                .card {
                    background-color: #fff;
                    border-radius: 10px;
                    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }
                .card-header {
                    display: flex;
                    align-items: center;
                    padding: 15px;
                }
                .avatar {
                    width: 50px;
                    height: 50px;
                    border-radius: 50%;
                    margin-right: 15px;
                }
                .user-info {
                    display: flex;
                    flex-direction: column;
                }
                .nickname {
                    font-weight: bold;
                    color: #333;
                }
                .time {
                    font-size: 12px;
                    color: #777;
                }
                .card-content {
                    padding: 0 15px 15px;
                }
                .text {
                    color: #555;
                    margin-bottom: 15px;
                }
                .card-image {
                    width: 100%;
                    height: auto;
                }
                .card-footer {
                    border-top: 1px solid #eee;
                    padding: 15px;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .comments {
                    color: #777;
                    font-size: 14px;
                }
                .comments:hover {
                    text-decoration: underline;
                    cursor: pointer;
                }
                .card:hover {
                    transform: translateY(-5px);
                    transition: transform 0.2s ease;
                }
            </style>
        </head>
        <body>
            <div class="card-container">
        '''
        
        # HTML 中间部分，动态生成每个数据项的卡片
        html_middle = ''
        for item in self.data:
            # 处理每个数据项的内容，包括用户头像、用户名、发布时间、内容等
            html_middle += f'''
                <div class="card">
                    <div class="card-header">
                        <img src="{item.user.avatar_url or 'https://via.placeholder.com/50'}" alt="avatar" class="avatar">
                        <div class="user-info">
                            <span class="nickname">{item.user.username}</span>
                            <span class="time">{item.time}</span>
                        </div>
                    </div>
                    <div class="card-content">
                        <p class="text">{item.content}</p>
                        {f'<img src="{item.images}" alt="post-image" class="card-image">' if item.images and 'http' in item.images else ''}
                    </div>
                    <div class="card-footer">
                        {f'<span class="comments">{item.comment.content}</span>' if item.comment else ''}
                    </div>
                </div>
            '''

        # HTML 尾部
        html_end = '''
            </div>
        </body>
        </html>
        '''

        # 生成最终的 HTML 文件
        html_content = html_start + html_middle + html_end

        # 保存 HTML 文件
        file_name = f"{now_login_user.uin}_{self.title}_data.html"
        file_path = f"{save_path}/{file_name}"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            # 日志记录
            log(f"导出成功 请查看 {save_path}/{file_name}", "success")
        except Exception as e:
            log(f"导出失败 {e}", "error")


    
    def export_markdown(self,e):
        # 创建 Markdown 内容的列表
        markdown_lines = []

        # 添加标题
        markdown_lines.append(f"# {self.title}\n")

        # 填充数据
        for item in self.data:
            if isinstance(item, User):
                markdown_lines.append(f"## 用户: {item.username}\n")
                markdown_lines.append(f"**QQ**: {item.uin}\n")
                markdown_lines.append(f"**头像 URL**: ![{item.uin}]({item.avatar_url})\n")
                markdown_lines.append("\n")
            elif isinstance(item, Message):
                # 处理时间格式
                time_str = item.time.strftime('%Y-%m-%d %H:%M:%S') if isinstance(item.time, datetime) else item.time
                markdown_lines.append(f"## 消息来自: {item.user.username}\n")
                markdown_lines.append(f"**时间**: {time_str}\n")
                markdown_lines.append(f"**内容**: {item.content}\n")
                if item.images:
                    markdown_lines.append(f"**图片**: ![]({item.images})\n")
                if item.comment:
                    markdown_lines.append(f"**评论**: {item.comment.content}\n")
                markdown_lines.append(f"**头像 URL**: ![{item.user.uin}]({item.user.avatar_url})\n")
                markdown_lines.append("\n")  # 添加空行以分隔消息

        # 生成 Markdown 内容
        markdown_content = "\n".join(markdown_lines)
        try:

            with open(f"{save_path}/{now_login_user.uin}_{self.title}_data.md", 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            log(f"导出成功 请查看 {save_path}/{now_login_user.uin}_{self.title}_data.md","success")
        except Exception as e:
            print(traceback.format_exc())
            log(e,"error")


    def did_mount(self):
        """This method is called when the control is added to the page."""
        self.update_page_info()


    def update_page_info(self):
        # 更新当前页的内容
        self.load_page_data()
        # 更新页码信息
        self.page_info.value = f"Page {self.current_page} of {self.total_pages}"
        # 更新按钮状态
        self.prev_button.disabled = self.current_page == 1
        self.next_button.disabled = self.current_page == self.total_pages
        self.update()

    def load_page_data(self):
        # 获取当前页的数据
        start = (self.current_page - 1) * self.items_per_page
        end = start + self.items_per_page
        current_data = self.data[start:end]

        # 清空当前内容并重新加载卡片
        self.content_area.controls.clear()
        # 定义一个容器来存放所有的卡片，使用 Column 容器来纵向排列三行
        rows = ft.Column(spacing=10, expand=True)

        # 每一行是一个 Row，包含两个 Card
        current_row = ft.Row(spacing=10, expand=True)
        row_count = 0

        for index, item in enumerate(current_data):
            if isinstance(item, User):
                # 创建 User Card
                card = ft.Card(
                    content=ft.Row(
                        controls=[
                            ft.Image(src=item.avatar_url, fit=ft.ImageFit.COVER, border_radius=100),
                            ft.Column(
                                controls=[
                                    ft.Text(item.username, size=18, weight="bold"),
                                    ft.Text(f'QQ: {item.uin}', size=14),
                                    ft.Text(item.link, size=12, color=ft.colors.BLUE_500),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                                spacing=4,
                            )
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        expand=True
                    ),
                    expand=True,
                )
            elif isinstance(item, Message):
                # 创建 Message Card
                controls = [
                    ft.Image(src=item.user.avatar_url, fit=ft.ImageFit.COVER, border_radius=100),
                    ft.Column(
                        controls=[
                            ft.Text(item.user.username, size=18, weight="bold"),
                            ft.Text(f'{item.time}', size=14),
                            ft.Text(item.content, size=16,width=300),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=4,
                    )
                ]

                # 如果存在图片，添加到 controls 中
                if item.images and 'http' in item.images:
                    image_control = ft.PopupMenuButton(
                        content=ft.Image(src=item.images, fit=ft.ImageFit.FIT_WIDTH,height=300,width=300,border_radius=10),
                        items=[
                            ft.PopupMenuItem(text="复制图片链接", on_click=lambda e, current_item=item: cb.copy(current_item.images)),
                            ft.PopupMenuItem(text="保存图片", on_click=lambda e, current_item=item: save_image(current_item.images, str(current_item.time))),
                            ft.PopupMenuItem(text="查看大图", on_click=lambda e, current_item=item: self.page.open(get_big_img_dlg(current_item.images))),
                        ],
                        tooltip="显示操作",
                    )
                    controls[1].controls.append(image_control)

                # 如果存在评论，添加到 controls 中
                if item.comment:
                    controls[1].controls.append(ft.Text(f'{item.comment.content}', size=12, color=ft.colors.BLUE_700,width=300))

                card = ft.Card(
                    content=ft.Row(
                        controls=controls,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                    ),
                    expand=True,
                )

            # 将 Card 添加到当前行
            current_row.controls.append(card)

            # 检查当前行是否已达到两列
            if len(current_row.controls) == 2:
                # 将当前行添加到容器中
                rows.controls.append(current_row)
                # 创建新的一行
                current_row = ft.Row(spacing=10, expand=True)
                row_count += 1

            # 如果达到了三行，就结束布局（可选，控制最多显示三行）
            if row_count == 3:
                break

        # 检查最后一行是否有剩余卡片且未添加
        if current_row.controls:
            rows.controls.append(current_row)
        
        # 如果传入的数据为空
        if not current_data:
            rows.controls.append(ft.Text("没有更多数据了"))
        # 最终将所有卡片的布局添加到 content_area
        self.content_area.controls.append(rows)


    def next_page(self, e):
        if self.current_page < self.total_pages:
            self.current_page += 1
            self.update_page_info()

    def previous_page(self, e):
        if self.current_page > 1:
            self.current_page -= 1
            self.update_page_info()

class User:
    def __init__(self, uin, username):
        self.uin = str(uin)  # 将 uin 转换为字符串
        self.avatar_url = f'http://q1.qlogo.cn/g?b=qq&nk={self.uin}&s=100'  # 使用 self.uin
        self.username = username
        self.link = f'https://user.qzone.qq.com/{self.uin}/'  # 使用 self.uin
    

class Comment:
    def __init__(self, user, time, content):
        self.user = user
        self.time = time
        self.content = content


class Message:
    def __init__(self, user, type, time, content, images=None, comment=None):
        self.user = user
        self.type = type
        self.time = time
        self.content = content
        self.images = images
        self.comment = comment


def reset_save_content():
    global all_messages, user_says, forward, leaves, other, friends
    all_messages = []
    user_says = []
    forward = []
    leaves = []
    other = []
    friends = []


def main(page: ft.Page):
    page.window.center()
    page.title = f"QQ空间历史内容获取 v{version} Powered by LibraHp"
    page.horizontal_alignment = "start"
    page.vertical_alignment = "center"
    # page.window.resizable = False
    page.padding = ft.padding.only(20,20,20,5)
    page.window.min_height = 700
    page.window.min_width = 1200
    # page.bgcolor = "#f0f0f0"
    # page.window.icon = "https://picsum.photos/200"
    # 字体使用系统默认字体
    page.theme= ft.Theme(font_family="Microsoft YaHei")
    global global_page
    global_page = page

    def logout():
        page.session.clear()
        user_info.content.controls[0].src = "https://raw.gitmirror.com/LibraHp/GetQzonehistory/refs/heads/gui/assets/logo.jpg"
        user_info.content.controls[1].value = "LibraHp"
        global now_login_user
        now_login_user = None
        reset_save_content()
        content_area.content = create_get_content_page()
        for tab in tabs.controls:
            if tab.data != "GetContent" and tab.data != "Logout" and tab.data != "Github":
                tab.disabled = True
        page.update()
                

    def handle_close(e):
        page.close(dlg_modal)
        if e.control.text == "Yes":
            logout()

    dlg_modal = ft.AlertDialog(
        modal=True,
        title=ft.Text("TIPS"),
        content=ft.Text("确定要退出登录吗？"),
        actions=[
            ft.TextButton("Yes", on_click=handle_close),
            ft.TextButton("No", on_click=handle_close),
        ],
        actions_alignment=ft.MainAxisAlignment.END
    )
    def QR():
    # 获取 qq空间 二维码
        url = 'https://ssl.ptlogin2.qq.com/ptqrshow?appid=549000912&e=2&l=M&s=3&d=72&v=4&t=0.8692955245720428&daid=5&pt_3rd_aid=0'

        try:
            response = requests.get(url)
            response.raise_for_status()  # 确保请求成功

            # 获取二维码图片的二进制内容
            image_data = response.content
            
            # 将二进制内容转换为 Base64 编码
            base64_image = base64.b64encode(image_data).decode('utf-8')

            # 获取 qrsig (可选)
            qrsig = requests.utils.dict_from_cookiejar(response.cookies).get('qrsig')
            page.session.set("qrsig", qrsig)
            return base64_image

        except Exception as e:
            print(traceback.format_exc())
            log("二维码获取问题：" + e, "error")
            return None
        
    def get_login_user_info():
        cookies = page.session.get("user_cookies")
        g_tk = bkn(cookies['p_skey'])
        uin = re.sub(r'o0*', '', cookies.get('uin'))
        response = requests.get('https://r.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?g_tk=' + str(g_tk) + '&uins=' + uin,
                                headers=headers, cookies=cookies)
        info = response.content.decode('GBK')
        info = info.strip().lstrip('portraitCallBack(').rstrip(');')
        info = json.loads(info)
        user_info.content.controls[0].src = f'http://q1.qlogo.cn/g?b=qq&nk={uin}&s=100'
        user_info.content.controls[1].value = info[uin][6]
        global now_login_user
        now_login_user = User(uin,info[uin][6])
        page.update()
    
    # 路由改变函数
    def change_route(e):
        selected_tab = e.control.data
        if selected_tab == "GetContent":
            content_area.content = create_get_content_page()
        elif selected_tab == "User":
            content_area.content = PaginatedContainer(user_says, items_per_page=2,title="说说列表")
        elif selected_tab == "Leave":
            content_area.content = PaginatedContainer(leaves, items_per_page=1,title="留言列表")
        elif selected_tab == "Friends":
            content_area.content = PaginatedContainer(friends, items_per_page=4,title="好友列表")
        elif selected_tab == "Forward":
            content_area.content = PaginatedContainer(forward, items_per_page=2,title="转发列表")
        elif selected_tab == "Other":
            content_area.content = PaginatedContainer(other, items_per_page=2,title="其他列表")
        elif selected_tab == "Pictures":
            content_area.content = create_pictures_page()
        elif selected_tab == "Logout":
            page.open(dlg_modal)

        page.update()

    def create_pictures_page():
        pictures_page = ft.GridView(
            expand=1,
            runs_count=5,
            max_extent=300,
            child_aspect_ratio=1.0,
            spacing=5,
            run_spacing=5,
        )

        for item in all_messages:
            # 如果存在图片，添加到 controls 中
            if item.images and 'http' in item.images:
                image_control = ft.PopupMenuButton(
                    content=ft.Image(src=item.images, fit=ft.ImageFit.FIT_WIDTH, height=300, width=300, border_radius=10),
                    items=[
                        ft.PopupMenuItem(text="复制图片链接", on_click=lambda e, current_item=item: cb.copy(current_item.images)),
                        ft.PopupMenuItem(text="保存图片", on_click=lambda e, current_item=item: save_image(current_item.images, str(current_item.time))),
                        ft.PopupMenuItem(text="查看大图", on_click=lambda e, current_item=item: page.open(get_big_img_dlg(current_item.images))),
                    ],
                    tooltip="显示操作",
                )
                pictures_page.controls.append(image_control)
                page.update()

        if len(pictures_page.controls) == 0:
            pictures_page.controls.append(ft.Text("暂无图片"))
        return pictures_page

    def unlock_tabs():
        for tab in tabs.controls:
            tab.disabled = False

    def show_login_content():
        progress_bar = None
        login_text = None
        for content in content_area.content.controls:
            if content.data == 'not_login':
                content.visible = False
            elif content.data == 'login_progress':
                content.visible = True
                progress_bar = content
            elif content.data == 'login_text':
                login_text = content
                content.visible = True
            elif content.data == 'login_pic':
                content.visible = True
        return progress_bar, login_text


    def create_user_dir():
        global save_path
        try:
            # 获取当前系统
            system = platform.system()

            if system == "Darwin":  # 如果是 macOS 系统
                # 将文件保存到用户的 ~/Documents/app_data 目录
                base_path = os.path.join(str(Path.home()), "Documents", "QzoneExport")
            elif system == "Windows":  # 如果是 Windows 系统
                # 将文件保存到程序的当前运行目录的results文件夹
                base_path = os.path.join(os.getcwd(), "results")
            else:  # 其他系统
                # 将文件保存到程序的当前运行目录
                base_path = os.getcwd()

            # 如果 base_path 不存在，则创建它 (确保 app_data 文件夹存在)
            if not os.path.exists(base_path):
                os.makedirs(base_path, exist_ok=True)

            # 构建用户特定的目录路径
            user_path = os.path.join(base_path, now_login_user.uin)

            # 检查是否有写权限
            if not os.access(base_path, os.W_OK):
                raise PermissionError(f"无法写入路径: {base_path}。请检查权限或以管理员身份运行。")

            # 创建用户目录
            if not os.path.exists(user_path):
                os.makedirs(user_path, exist_ok=True)

            save_path = user_path  # 更新全局保存路径
            log(f"用户目录创建成功: {save_path}", "success")

        except PermissionError as e:
            log(f"文件权限不足: {e}. 请尝试选择不同的目录或以管理员身份运行。", "error")
        except Exception as e:
            print(traceback.format_exc())
            log(f"创建用户目录时发生错误: {e}", "error")


    
    # 获取内容页面
    def create_get_content_page():
        if page.session.contains_key("user_cookies"):
            return get_message_result()
        base64_image = QR()
        # 更新二维码状态的函数（模拟，需实际实现逻辑）
        def update_qr_code_status(e):
            ptqrtoken = ptqrToken(page.session.get("qrsig"))
            url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara' \
              '%3Dizone&ptqrtoken=' + str(ptqrtoken) + '&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-' \
              + str(time.time()) + '&js_ver=20032614&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&'
            cookies = {'qrsig': page.session.get("qrsig")}
            try:
                r = requests.get(url, cookies=cookies)
                r.encoding = 'utf-8'
                if '二维码未失效' in r.text:
                    qr_status.value = "二维码状态：未失效"
                    pass
                elif '二维码认证中' in r.text:
                    qr_status.value = "二维码状态：认证中"
                elif '二维码已失效' in r.text:
                    qr_status.value = "二维码状态：已失效"
                elif '本次登录已被拒绝' in r.text:
                    qr_status.value = "二维码状态：已拒绝"
                elif '登录成功' in r.text:
                    qr_status.value = "二维码状态：已登录"
                    cookies = requests.utils.dict_from_cookiejar(r.cookies)
                    uin = requests.utils.dict_from_cookiejar(r.cookies).get('uin')
                    regex = re.compile(r'ptsigx=(.*?)&')
                    sigx = re.findall(regex, r.text)[0]
                    url = 'https://ptlogin2.qzone.qq.com/check_sig?pttype=1&uin=' + uin + '&service=ptqrlogin&nodirect=0' \
                                                                                        '&ptsigx=' + sigx + \
                        '&s_url=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&f_url=&ptlang' \
                        '=2052&ptredirect=100&aid=549000912&daid=5&j_later=0&low_login_hour=0&regmaster=0&pt_login_type' \
                        '=3&pt_aid=0&pt_aaid=16&pt_light=0&pt_3rd_aid=0'
                    try:
                        r = requests.get(url, cookies=cookies, allow_redirects=False)
                        target_cookies = requests.utils.dict_from_cookiejar(r.cookies)
                        page.session.set("user_cookies", target_cookies)
                        log(f"登录成功,欢迎您，{page.session.get('user_cookies')['uin']}", "success")
                        get_login_user_info()
                        create_user_dir()
                        progress_bar, login_text = show_login_content()
                        create_card_list_view(progress_bar, login_text)
                        # p_skey = requests.utils.dict_from_cookiejar(r.cookies).get('p_skey')
                        return
                    except Exception as e:
                        log("登录过程问题：" + e,"error")
                        return
            except Exception as e:
                print(traceback.format_exc())
                log("二维码状态问题：" + e,"error")
                return

            page.update()

        # 获取新的二维码的函数（模拟，需实际实现逻辑）
        def refresh_qr_code(e):
            base64_image = QR()
            # 刷新已渲染的图片
            qr_image.src_base64 = base64_image
            qr_status.value = "二维码状态：等待扫描"  # 重置状态为等待扫描
            page.update()

        qr_image = ft.Image(src_base64=base64_image, width=200, height=200,fit=ft.ImageFit.CONTAIN, data='not_login')
        qr_status = ft.Text("二维码状态：等待扫描", size=16, color="green", data='not_login')
        def task():
            while True:
                # 使用 in 分别检查多个条件
                if any(status in qr_status.value for status in ['已登录', '已拒绝', '已失效']):
                    break
                log(qr_status.value)
                update_qr_code_status(None)
                time.sleep(2)
        thread = threading.Thread(target=task)
        thread.start()


        # 返回一个包含二维码和状态更新的布局
        return ft.Column(
            controls=[
                ft.Text("请使用手机QQ扫码登录", size=24, weight="bold", data='not_login'),
                qr_image,  # 展示二维码
                qr_status,  # 展示二维码状态
                ft.Row(
                    [
                        ft.ElevatedButton("刷新二维码", on_click=refresh_qr_code),
                        ft.ElevatedButton("更新状态", on_click=update_qr_code_status),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    data='not_login'
                ),
                ft.Image(src="https://raw.gitmirror.com/LibraHp/GetQzonehistory/refs/heads/gui/assets/loading.gif", expand=True, data='login_pic', visible=False),
                ft.Text("获取空间消息中...", size=24, weight="bold", data='login_text',visible=False),
                ft.ProgressBar(data='login_progress', visible=False,bar_height=10,border_radius=10),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment="center",
            expand=True,
        )
    
    def get_message(start, count):
        cookies = page.session.get("user_cookies")
        g_tk = bkn(cookies['p_skey'])
        uin = re.sub(r'o0*', '', cookies.get('uin'))
        params = {
            'uin': uin,
            'begin_time': '',
            'end_time': '',
            'getappnotification': '1',
            'getnotifi': '1',
            'has_get_key': '0',
            'offset': start,
            'set': '0',
            'count': count,
            'useutf8': '1',
            'outputhtmlfeed': '1',
            'scope': '1',
            'format': 'jsonp',
            'g_tk': [
                g_tk,
                g_tk,
            ],
        }
        
        try:
            response = requests.get(
                'https://user.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds2_html_pav_all',
                params=params,
                cookies=cookies,
                headers=headers,
                timeout=(5, 10)  # 设置连接超时为5秒，读取超时为10秒
            )
        except requests.Timeout:
            return None
        
        return response
    
    def get_message_count():
        try:
            # 初始的总量范围
            lower_bound = 0
            upper_bound = 10000000  # 假设最大总量为1000000
            total = upper_bound // 2  # 初始的总量为上下界的中间值
            while lower_bound <= upper_bound:
                response = get_message(total, 10)
                if "img" in response.text:
                    # 请求成功，总量应该在当前总量的右侧
                    lower_bound = total + 1
                else:
                    log(response.text)
                    # 请求失败，总量应该在当前总量的左侧
                    upper_bound = total - 1
                total = (lower_bound + upper_bound) // 2  # 更新总量为新的中间值
                log(f"获取消息列表数量中... 当前 - Total: {total}")
            return total
        except Exception as e:
            print(traceback.format_exc())
            if is_debug:
                log(e, "error")
            return total
    

    def get_hitokoto():
        try:
            url = "https://v1.hitokoto.cn/"
            response = requests.get(url,headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                return data['hitokoto'], data['from']
            else:
                return "故地重游就像是刻舟求剑，但只有那年胜过年年", "互联网"
        except Exception as e:
            return "故地重游就像是刻舟求剑，但只有那年胜过年年", "互联网"
        
    def create_card_list_view(progress_bar, login_text):
        try:
            # 创建一个空的卡片列表，用于存放所有卡片
            login_text.value = "获取空间消息数量中..."
            page.update()
            count = get_message_count()
            page.client_storage.set(f"{now_login_user.uin}_message_count", count)
            login_text.value = "获取空间消息列表中..."
            page.update()

            for i in range(int(count / 100) + 1):
                try:
                    # 获取消息并解码
                    message_content = get_message(i * 100, 100).content
                    message = message_content.decode('utf-8') if message_content else None
                    # if is_debug:
                    #     log(message, "debug")
                    # 确保消息内容存在
                    if not message:
                        continue

                    # 处理消息
                    html = process_old_html(message)
                    # 确保 HTML 中包含有效信息
                    if is_debug:
                        log(html, "debug")
                    if "li" not in html:
                        continue

                    soup = BeautifulSoup(html, 'html.parser')

                    # 遍历所有的列表项
                    for element in soup.find_all('li', class_='f-single f-s-s'):
                        # 初始化
                        res_message = Message(user=None, type=None, time=None, content=None, images=None, comment=None)
                        comment = Comment(user=None, time=None, content=None)

                        # 处理好友信息
                        friend_element = element.find('a', class_='f-name q_namecard')
                        if friend_element:
                            friend_name = friend_element.get_text()
                            friend_qq = friend_element.get('link', '')[9:] if friend_element.get('link', '') else '123456' # 使用默认空值
                            friend = User(uin=friend_qq, username=friend_name)
                            comment.user = friend
                            res_message.user = friend
                            friends.append(friend)

                        # 处理时间、文本、图片等信息
                        time_element = element.find('div', class_='info-detail')
                        text_element = element.find('p', class_='txt-box-title ellipsis-one')
                        img_element = element.find('a', class_='img-item')
                        message_type_element = element.find('span', class_='ui-mr10 state')
                        comment_element = element.find('div', class_='comments-content font-b')

                        # 消息类型
                        if message_type_element:
                            res_message.type = message_type_element.get_text()

                        # 评论
                        if comment_element:
                            comment_time_element = comment_element.find('span', class_='ui-mr10 state')
                            comment.time = parse_time_strings(comment_time_element.get_text()) if comment_time_element else None
                            comment.content = comment_element.get_text()
                            res_message.comment = comment

                        # 发送时间和内容
                        if time_element and text_element:
                            put_time = time_element.get_text().replace('\xa0', ' ')
                            res_message.time = parse_time_strings(put_time)
                            res_message.content = text_element.get_text().replace('\xa0', ' ')

                        # 图片处理
                        if img_element:
                            img_src = img_element.find('img').get('src')
                            if img_src:
                                img_src = img_src.replace("/m&ek=1&kp=1", "/s&ek=1&kp=1").replace(r"!/m/", "!/s/")
                                res_message.images = img_src

                        # 添加消息到列表
                        all_messages.append(res_message)
                        page.update()

                    # 更新进度条
                    progress_value = i / int(count / 100)
                    progress_bar.value = progress_value
                    page.window.progress_bar = progress_value
                    log(f'当前进度：{progress_value * 100:.1f}%  第 {i} 页/共 {round(count/100)} 页')

                except Exception as e:
                    print(traceback.format_exc())
                    log(f"处理消息时发生错误: {e}", "error")
                    continue

            # 完成消息获取
            content_area.content.clean()
            log("获取成功！", "success")
            clean_content()
            unlock_tabs()
            content_area.content.controls.append(get_message_result())
            page.update()

        except Exception as e:
            print(traceback.format_exc())
            log(f"获取消息时发生错误: {e}", "error")


    def get_message_result():
        # 用户信息栏
        user_info = ft.Card(
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Row([
                            ft.CircleAvatar(
                                foreground_image_src=now_login_user.avatar_url,
                                content=ft.Text(f"{now_login_user.username}"), 
                                radius=40
                            ),  # 圆形头像
                            ft.Column(
                                [
                                    ft.Text("你好！", size=16),
                                    ft.Text(f"{now_login_user.username}", size=20, weight=ft.FontWeight.BOLD),
                                ],
                                alignment=ft.MainAxisAlignment.CENTER,
                            )
                        ]),
                        # 操作栏
                        ft.Row(
                            controls=[
                                ft.Column(
                                    controls=[
                                        ft.ElevatedButton(text="空间网页版"),
                                        ft.ElevatedButton(text="打开导出文件夹"),
                                    ],
                                ),
                                ft.Column(
                                    controls=[
                                        ft.ElevatedButton(text="重新获取"),
                                        ft.ElevatedButton(text="保存登录状态"),
                                    ],
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,  # 按钮列居中对齐
                            spacing=20  # 列之间的间距
                        )
                    ],
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                padding=20,
            ),
            height=300,
            col=4
        )


        # 交互信息栏
        interaction_info = ft.Card(
            content=ft.Container(
                content = ft.Column(
                    [
                        ft.Text("自空间交互以来：", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(f"你发布了", size=20, spans=[ft.TextSpan(f" {user_says.__len__() } ", ft.TextStyle(weight=ft.FontWeight.BOLD,color=ft.colors.BLUE_300)),ft.TextSpan("条说说", ft.TextStyle(size=20))]),
                        ft.Text(f"有", size=20, spans=[ft.TextSpan(f" {leaves.__len__() } ", ft.TextStyle(weight=ft.FontWeight.BOLD,color=ft.colors.BLUE_300)),ft.TextSpan("条留言", ft.TextStyle(size=20))]),
                        ft.Text(f"有", size=20,spans=[ft.TextSpan(f" {friends.__len__() } ", ft.TextStyle(weight=ft.FontWeight.BOLD,color=ft.colors.BLUE_300)),ft.TextSpan("个人与你空间有过交互", ft.TextStyle(size=20))]),
                        ft.Text(f"最早的说说发布在", size=20, spans=[ft.TextSpan(f" {user_says[user_says.__len__() - 1].time if user_says.__len__() > 0 else '无'} ", ft.TextStyle(weight=ft.FontWeight.BOLD,color=ft.colors.BLUE_300)),ft.TextSpan("，那个时候的你有这么多烦恼嘛", ft.TextStyle(size=20))]),
                        ft.Text(f"和你交互最多的人是", size=20, spans=[ft.TextSpan(f" @{most_interactive_user[0][0][0] if most_interactive_user.__len__() > 0 else '无'} ", ft.TextStyle(weight=ft.FontWeight.BOLD,color=ft.colors.BLUE_300)),ft.TextSpan("现在的她/他怎么样了呢", ft.TextStyle(size=20))]),
                    ],
                    spacing=10,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                padding=20,
            ),
            height=300,
            col=8
        )


        hitokoto, source = get_hitokoto()
        # 发布的第一条说说
        first_post = ft.Container(
            content=ft.Column(
                [
                    ft.Text("你发布的第一条说说是：", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=ft.ResponsiveRow(
                            controls=[
                                ft.Text(f"{user_says[user_says.__len__() - 1].time if user_says.__len__() > 0 else '无'}", size=14),
                                ft.Text(f"{user_says[user_says.__len__() - 1].content if user_says.__len__() > 0 else '无'}", size=20)
                            ]
                        ),
                        padding=10,
                        border_radius=ft.border_radius.all(5),
                        # bgcolor=ft.colors.GREY_100,
                        expand=True,
                    ),
                    ft.Text(f"一言: {hitokoto}\n出自: {source}", size=14)
                ],
            ),
            col=8,
            expand=True,
        )
        
        # 好友交互排行榜
        friend_action_info = ft.Card(
            content=ft.Container(
                content = ft.Column(
                    controls=[
                        ft.Text("好友交互排行榜", size=18, weight=ft.FontWeight.BOLD),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                padding=10,
                alignment=ft.alignment.center
            ),
            col=4,
            expand=True
        )

        for index, item in enumerate(most_interactive_user):
            friend_action_info.content.content.controls.append(
                ft.Row(
                    controls=[
                        ft.Text(f"{index + 1}.", size=14),
                        ft.Image(src=f'http://q1.qlogo.cn/g?b=qq&nk={item[0][1]}&s=100', width=40, height=40, border_radius=100),
                        ft.Text(f"@{item[0][0]} 交互{item[1]}次", size=14)
                    ]
                )
            )
            page.update()

        # 布局排列
        return ft.Column(
                    [
                        ft.ResponsiveRow(
                            controls=[
                                user_info,
                                interaction_info,
                            ]
                        ),
                        ft.ResponsiveRow(
                            controls=[
                                first_post,
                                friend_action_info
                            ],
                            expand=True
                        )
                    ],
                    spacing=20,
                    expand=True,
                )


    # 用户信息
    user_info = ft.Container(
        content=ft.Column(
            controls=[
                ft.Image(src="https://raw.gitmirror.com/LibraHp/GetQzonehistory/refs/heads/gui/assets/logo.jpg", width=80, height=80, border_radius=100),  # Replace with actual avatar URL
                ft.Text("LibraHp", size=20, weight="bold")
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment="center"
        ),
        width=200,
        padding=20
    )


    # 左侧标签页
    tabs = ft.Column(
        controls=[
            ft.ElevatedButton("获取内容", on_click=change_route, data="GetContent", width=page.width),
            ft.ElevatedButton("说说列表", on_click=change_route, data="User", width=page.width, disabled=True),
            ft.ElevatedButton("留言列表", on_click=change_route, data="Leave", width=page.width, disabled=True),
            ft.ElevatedButton("好友列表", on_click=change_route, data="Friends", width=page.width, disabled=True),
            ft.ElevatedButton("转发列表", on_click=change_route, data="Forward", width=page.width, disabled=True),
            ft.ElevatedButton("其他列表", on_click=change_route, data="Other", width=page.width, disabled=True),
            ft.ElevatedButton("照片墙", on_click=change_route, data="Pictures", width=page.width, disabled=True),
            ft.ElevatedButton("退出当前账号登录", on_click=change_route, data="Logout", width=page.width),
            ft.TextButton("Powered by LibraHp", url="https://github.com/LibraHp", data="Github", width=page.width)
        ],
        alignment="center",
        spacing=10
    )

    # 左侧标签容器
    left_panel = ft.Container(
        content=ft.Column(
            controls=[user_info, tabs],
            spacing=20,
            horizontal_alignment="center",
            scroll=ft.ScrollMode.HIDDEN,
        ),
        alignment=ft.alignment.center,
        col=2,
        # bgcolor="#ffffff",
        border_radius=10,
        padding=10
    )

    try:
        home_content_md = requests.get("https://githubraw.com//LibraHp/GetQzonehistory/gui/README.md",timeout=3).text
    except:
        home_content_md = "获取公告失败，直接点击右侧获取内容即可正常获取"
    # 路由容器
    content_area = ft.Container(
        content=ft.Column(
            controls=[
                ft.Markdown(
                    value=home_content_md,
                    selectable=True,
                    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                    on_tap_link=lambda e: page.launch_url(e.data)
                ),
            ],
            expand=True,
            scroll=ft.ScrollMode.HIDDEN
        ),
        # bgcolor="#ffffff",
        expand=True,
        padding=20,
        border_radius=10,
        col=10
    )

    # 主布局
    main_layout = ft.ResponsiveRow(
        controls=[left_panel, content_area],
        expand=True,
        alignment="start"
    )

    log_list = ft.Text(ref=log_info_ref,size=12, color="blue")
    page.add(main_layout)
    page.add(log_list)
    log("开始运行...","success")


if __name__ == "__main__":
    ft.app(target=main)
