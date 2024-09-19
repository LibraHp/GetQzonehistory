import flet as ft
import requests
import base64
import re
import time

is_finsh = False

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

        return base64_image, qrsig

    except Exception as e:
        print(e)
        return None, None


def create_card(img_url, title, subtitle):
    return ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.ListTile(
                        # 如果img_url为空 显示https://picsum.photos/200
                        leading=ft.Image(src=img_url, border_radius=100),
                        title=ft.Text(title),
                        subtitle=ft.Text(subtitle),
                    ),
                    ft.Row(
                        [ft.TextButton("购票"), ft.TextButton("试听")],
                        alignment=ft.MainAxisAlignment.END,
                    ),
                ]
            ),
            width=400,
            padding=10,
        )
    )

def main(page: ft.Page):
    page.window.center()
    page.title = "QQ空间历史内容获取 v1.0 Powered by LibraHp"
    page.horizontal_alignment = "start"
    page.vertical_alignment = "center"
    page.window.resizable = False
    page.padding = 20
    page.bgcolor = "#f0f0f0"

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

        page.update()

    # 获取内容页面
    def create_get_content_page():
        base64_image, qrsig = QR()
        
        # 更新二维码状态的函数（模拟，需实际实现逻辑）
        def update_qr_code_status(e):
            ptqrtoken = ptqrToken(qrsig)
            url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara' \
              '%3Dizone&ptqrtoken=' + str(ptqrtoken) + '&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-' \
              + str(time.time()) + '&js_ver=20032614&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&'
            cookies = {'qrsig': qrsig}
            try:
                r = requests.get(url, cookies=cookies)
                print(r.text)
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
                        print(target_cookies)
                        p_skey = requests.utils.dict_from_cookiejar(r.cookies).get('p_skey')
                        is_finsh = True
                        page.update()
                    except Exception as e:
                        print(e)
            except Exception as e:
                print(e)

            page.update()

        # 获取新的二维码的函数（模拟，需实际实现逻辑）
        def refresh_qr_code(e):
            base64_image, qrsig = QR()
            # 刷新已渲染的图片
            qr_image.src_base64 = base64_image
            qr_status.value = "二维码状态：等待扫描"  # 重置状态为等待扫描
            page.update()

        qr_image = ft.Image(src_base64=base64_image, width=200, height=200)
        qr_status = ft.Text("二维码状态：等待扫描", size=16, color="green")

        # 返回一个包含二维码和状态更新的布局
        return ft.Column(
            controls=[
                ft.Text("请使用手机QQ扫码登录", size=24, weight="bold"),
                qr_image,  # 展示二维码
                qr_status,  # 展示二维码状态
                ft.Row(
                    [
                        ft.ElevatedButton("刷新二维码", on_click=refresh_qr_code),
                        ft.ElevatedButton("更新状态", on_click=update_qr_code_status),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
            ],
            alignment="center",
            horizontal_alignment="center",
            expand=True,
        )

    # 用户信息
    user_info = ft.Container(
        content=ft.Column(
            controls=[
                ft.Image(src="https://picsum.photos/200", width=80, height=80, border_radius=100),  # Replace with actual avatar URL
                ft.Text("Username", size=20, weight="bold")
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
            ft.ElevatedButton("说说列表", on_click=change_route, data="User", width=200, disabled=not is_finsh),
            ft.ElevatedButton("留言列表", on_click=change_route, data="Leave", width=200, disabled=not is_finsh),
            ft.ElevatedButton("好友列表", on_click=change_route, data="Friends", width=200, disabled=not is_finsh),
            ft.ElevatedButton("转发列表", on_click=change_route, data="Forward", width=200, disabled=not is_finsh),
            ft.ElevatedButton("其他列表", on_click=change_route, data="Other", width=200, disabled=not is_finsh),
            ft.ElevatedButton("图片列表", on_click=change_route, data="Pictures", width=200, disabled=not is_finsh),
            ft.Column(
                controls=[
                    ft.TextButton("Powered by LibraHp", url="https://github.com/LibraHp"),
                    ft.TextButton("Bilibili @高数带我飞", url="https://space.bilibili.com/1117414477"),
                    ft.Text("程序完全免费且开源！", size=12, color="red", text_align="center")
                ],
                alignment="center",
                horizontal_alignment="center",
                width=200
            )
        ],
        scroll=True,
        alignment="start",
        spacing=10
    )

    # 左侧标签容器
    left_panel = ft.Container(
        content=ft.Column(
            controls=[user_info, tabs],
            spacing=30,
            horizontal_alignment="start"
        ),
        width=220,
        bgcolor="#ffffff",
        border_radius=10,
        padding=10
    )

    try:
        home_content_md = requests.get("https://raw.githubusercontent.com/LibraHp/GetQzonehistory/main/README.MD").text
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
            scroll=True
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

    page.add(main_layout)


if __name__ == "__main__":
    ft.app(target=main)
