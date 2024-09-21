import flet as ft
import requests
import base64
import re
import time
from datetime import datetime
import json
import threading
from bs4 import BeautifulSoup

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
    if len(time_str) == 5:  # 格式为 HH:MM
        return datetime.combine(today, datetime.strptime(time_str, "%H:%M").time())
    elif "年" in time_str:  # 包含“年”的格式
        return datetime.strptime(time_str, "%Y年%m月%d日 %H:%M")
    elif "月" in time_str:  # 包含“月”的格式
        return datetime.strptime(time_str, "%m月%d日 %H:%M").replace(year=today.year)
    return None


class User:
    def __init__(self, uin, username):
        self.uin = uin
        self.avatar_url = f'http://q1.qlogo.cn/g?b=qq&nk={uin}&s=100'
        self.username = username
        self.link = f'https://user.qzone.qq.com/{uin}/'
    

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


def create_card(img_url, title, subtitle):
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        # 如果img_url为空 显示https://picsum.photos/200
                        # leading=ft.Image(src=img_url, border_radius=100),
                        title=ft.Text(title),
                        subtitle=ft.Text(subtitle),
                    ),
                    # ft.Row(
                    #     [ft.TextButton("购票"), ft.TextButton("试听")],
                    #     alignment=ft.MainAxisAlignment.END,
                    # ),
                ]
            ),
            expand=True,
            padding=10,
        )
    )


def main(page: ft.Page):
    page.window.center()
    page.title = "QQ空间历史内容获取 v1.0 Powered by LibraHp"
    page.horizontal_alignment = "start"
    page.vertical_alignment = "center"
    page.window.resizable = False
    page.padding = ft.padding.only(20,20,20,5)
    page.bgcolor = "#f0f0f0"
    # page.window.icon = "https://picsum.photos/200"
    # 字体使用系统默认字体
    page.theme= ft.Theme(font_family="Microsoft YaHei")
    

    def logout():
        page.session.clear()
        user_info.content.controls[0].src = "assets/logo.jpg"
        user_info.content.controls[1].value = "LibraHp"
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
            print(e)
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
        page.update()
    
    # 路由改变函数
    def change_route(e):
        selected_tab = e.control.data
        if selected_tab == "GetContent":
            content_area.content = create_get_content_page()
        elif selected_tab == "User":
            content_area.content = ft.Text("说说列表", size=30)
        elif selected_tab == "Leave":
            content_area.content = ft.Text("留言列表", size=30)
        elif selected_tab == "Friends":
            content_area.content = ft.Text("好友列表", size=30)
        elif selected_tab == "Forward":
            content_area.content = ft.Text("转发列表", size=30)
        elif selected_tab == "Other":
            content_area.content = ft.Text("其他列表", size=30)
        elif selected_tab == "Pictures":
            content_area.content = ft.Text("图片列表", size=30)
        elif selected_tab == "Logout":
            page.open(dlg_modal)

        page.update()

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
        return progress_bar, login_text

                
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
                        page.snack_bar = ft.SnackBar(ft.Text(f"登录成功,欢迎您 {target_cookies.get('uin')}"),duration=2000)
                        page.snack_bar.open = True
                        get_login_user_info()
                        progress_bar, login_text = show_login_content()
                        create_card_list_view(progress_bar, login_text)
                        # p_skey = requests.utils.dict_from_cookiejar(r.cookies).get('p_skey')
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)

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
                ft.Text("获取空间消息中...", size=24, weight="bold", data='login_text',visible=False),
                ft.ProgressBar(data='login_progress', visible=False),
            ],
            alignment="center",
            horizontal_alignment="center",
            expand=True,
        )
    
    def get_message(start, count):
        cookies = page.session.get("user_cookies")
        g_tk = bkn(cookies['p_skey'])
        uin = re.sub(r'o0*', '', cookies.get('uin'))
        params = {
            'uin': uin,
            'begin_time': '0',
            'end_time': '0',
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
        # 初始的总量范围
        lower_bound = 0
        upper_bound = 10000000  # 假设最大总量为1000000
        total = upper_bound // 2  # 初始的总量为上下界的中间值
        while lower_bound <= upper_bound:
            response = get_message(total, 100)
            if "li" in response.text:
                # 请求成功，总量应该在当前总量的右侧
                lower_bound = total + 1
            else:
                # 请求失败，总量应该在当前总量的左侧
                upper_bound = total - 1
            total = (lower_bound + upper_bound) // 2  # 更新总量为新的中间值
            log(f"获取消息列表数量中... 当前 - Total: {total}")
        return total
    
    def create_card_list_view(progress_bar, login_text):

        # 创建一个空的卡片列表，用于存放所有卡片
        login_text.value = "获取空间消息数量中..."
        page.update()
        count = get_message_count()
        login_text.value = "获取空间消息列表中..."
        page.update()
        for i in range(int(count / 100) + 1):
            message = get_message(i * 100, 100).content.decode('utf-8')
            time.sleep(0.2)
            html = process_old_html(message)
            if "li" not in html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            for element in soup.find_all('li', class_='f-single f-s-s'):
                put_time = None
                text = None
                img = None
                message_type = None
                friend = User()
                comment = Comment()
                res_message = Message()
                friend_element = element.find('a', class_='f-name q_namecard')
                # 获取好友昵称和QQ
                if friend_element is not None:
                    friend_name = friend_element.get_text()
                    friend_qq = friend_element.get('link')[9:]
                    # friend_link = friend_element.get('href')
                    friend.uin = friend_qq
                    friend.username = friend_name
                    comment.user = friend
                    res_message.user = friend
                time_element = element.find('div', class_='info-detail')
                text_element = element.find('p', class_='txt-box-title ellipsis-one')
                img_element = element.find('a', class_='img-item')
                message_type_element = element.find('span', class_='ui-mr10 state')
                if message_type_element is not None:
                    message_type = message_type_element.get_text()
                    res_message.type = message_type
                comment_element = element.find('div', class_='comments-content font-b')
                if comment_element is not None:
                    comment_time_element = comment_element.find('span', class_='ui-mr10 state')
                    comment.time = parse_time_strings(comment_time_element.get_text())
                    comment_text = comment_element.find(text=True, recursive=False).strip()
                    comment.content = comment_text
                    res_message.comment = comment
                if time_element is not None and text_element is not None:
                    put_time = time_element.get_text().replace('\xa0', ' ')
                    put_time = parse_time_strings(put_time)
                    res_message.time = put_time
                    text = text_element.get_text().replace('\xa0', ' ')
                    res_message.content = text
                    log(f'{message_type} - {put_time} - {text}')
                    # log(f"{put_time} - {text}")
                    if img_element is not None:
                        img = img_element.find('img').get('src')
                        img = str(img).replace("/m&ek=1&kp=1", "/s&ek=1&kp=1")
                        img = str(img).replace(r"!/m/", "!/s/")
                        res_message.images = img
                    # if text not in [sublist[1] for sublist in texts]:
                print(res_message)
                progress_bar.value = i / int(count / 100)
                page.update()
        login_text.value = "获取成功！"
        progress_bar.visible = False
        unlock_tabs()
        content_area.content.controls.append(get_message_result())
        page.update()

    def get_message_result():
        return ft.Column(
            controls=[
                ft.Row(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Text("说说共有 " + str(889) + " 条", size=25),
                                padding=20,
                                alignment=ft.alignment.center,
                            ),
                            elevation=5,
                            shape=ft.RoundedRectangleBorder(radius=15),
                            expand=True,
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Text("留言共有 " + str(889) + " 条", size=25),
                                padding=20,
                                alignment=ft.alignment.center,
                            ),
                            elevation=5,
                            shape=ft.RoundedRectangleBorder(radius=15),
                            expand=True,
                        ),
                    ],
                    alignment="center",
                    spacing=20,  # 控制两列卡片之间的间距
                    expand=True,
                ),
                ft.Row(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Text("转发共有 " + str(889) + " 条", size=25),
                                padding=20,
                                alignment=ft.alignment.center,
                            ),
                            elevation=5,
                            shape=ft.RoundedRectangleBorder(radius=15),
                            expand=True,
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Text("图片共有 " + str(889) + " 张", size=25),
                                padding=20,
                                alignment=ft.alignment.center,
                            ),
                            elevation=5,
                            shape=ft.RoundedRectangleBorder(radius=15),
                            expand=True,
                        ),
                    ],
                    alignment="center",
                    spacing=20,
                    expand=True,
                ),
                ft.Row(
                    controls=[
                        ft.Card(
                            content=ft.Container(
                                content=ft.Text("评论共有 " + str(889) + " 条", size=25),
                                padding=20,
                                alignment=ft.alignment.center,
                            ),
                            elevation=5,
                            shape=ft.RoundedRectangleBorder(radius=15),
                            expand=True,
                        ),
                        ft.Card(
                            content=ft.Container(
                                content=ft.Text("好友共有 " + str(889) + " 位", size=25),
                                padding=20,
                                alignment=ft.alignment.center,
                            ),
                            elevation=5,
                            shape=ft.RoundedRectangleBorder(radius=15),
                            expand=True,
                        ),
                    ],
                    alignment="center",
                    spacing=20,
                    expand=True,
                ),
                ft.Row(
                    controls=[
                        ft.Text("最早的说说发布在 2022 年 3 月 20 日 12:00", size=20),
                        ft.Text("程序完全免费，请勿用于商业用途！", size=20),
                    ],
                    alignment="center",
                )
            ],
            alignment="center",
            horizontal_alignment="center",
            spacing=20,  # 控制每行之间的间距
            expand=True,
        )





    # 用户信息
    user_info = ft.Container(
        content=ft.Column(
            controls=[
                ft.Image(src="assets/logo.jpg", width=80, height=80, border_radius=100),  # Replace with actual avatar URL
                ft.Text("LibraHp", size=20, weight="bold")
            ],
            alignment="center",
            horizontal_alignment="center"
        ),
        width=200,
        padding=20
    )


    # 左侧标签页
    tabs = ft.Column(
        controls=[
            ft.ElevatedButton("获取内容", on_click=change_route, data="GetContent", width=200),
            ft.ElevatedButton("说说列表", on_click=change_route, data="User", width=200, disabled=True),
            ft.ElevatedButton("留言列表", on_click=change_route, data="Leave", width=200, disabled=True),
            ft.ElevatedButton("好友列表", on_click=change_route, data="Friends", width=200, disabled=True),
            ft.ElevatedButton("转发列表", on_click=change_route, data="Forward", width=200, disabled=True),
            ft.ElevatedButton("其他列表", on_click=change_route, data="Other", width=200, disabled=True),
            ft.ElevatedButton("图片列表", on_click=change_route, data="Pictures", width=200, disabled=True),
            ft.ElevatedButton("退出当前账号登录", on_click=change_route, data="Logout", width=200),
            ft.TextButton("Powered by LibraHp", url="https://github.com/LibraHp", data="Github", width=200),
        ],
        alignment="start",
        spacing=10
    )

    # 左侧标签容器
    left_panel = ft.Container(
        content=ft.Column(
            controls=[user_info, tabs],
            spacing=20,
            horizontal_alignment="start"
        ),
        width=220,
        bgcolor="#ffffff",
        border_radius=10,
        padding=10
    )

    try:
        home_content_md = requests.get("https://raw.githubusercontent.com/LibraHp/GetQzonehistory/gui/README.md").text
    except:
        home_content_md = "获取失败"
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
        bgcolor="#ffffff",
        expand=True,
        padding=20,
        border_radius=10
    )

    # 主布局
    main_layout = ft.Row(
        controls=[left_panel, content_area],
        expand=True,
        alignment="start"
    )

    def log(message):
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        log_list.value = f"{now} - {message}"
        page.update()

    log_list = ft.Text(size=12, color="blue")
    page.add(main_layout)
    page.add(log_list)
    log("开始运行...")


if __name__ == "__main__":
    ft.app(target=main)
