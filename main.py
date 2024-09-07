from bs4 import BeautifulSoup
from tqdm import trange,tqdm
import pandas as pd
import signal
import configparser
import os
import re
import requests
import json
from PIL import Image
import qrcode
from pyzbar.pyzbar import decode
import time

config = configparser.ConfigParser()
config.read('./config.ini')
temp_path = config.get('File', 'temp')
user_path = config.get('File', 'user')
result_path = config.get('File', 'result')


def init_flooder():
    # 初始化temp文件夹
    if not os.path.exists(temp_path):
        os.makedirs(temp_path)
        print(f"Created directory: {temp_path}")

    # 初始化user文件夹
    if not os.path.exists(user_path):
        os.makedirs(user_path)
        print(f"Created directory: {user_path}")

    # 初始化result文件夹
    if not os.path.exists(result_path):
        os.makedirs(result_path)
        print(f"Created directory: {result_path}")


def read_files_in_folder():
    # 获取文件夹下的所有文件
    files = os.listdir(user_path)
    # 如果文件夹为空
    if not files:
        return None
    # 输出文件列表
    print("已登录用户列表:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")

    # 选择文件
    while True:
        try:
            choice = int(input("请选择要登录的用户序号，重新登录输入0: "))
            if 1 <= choice <= len(files):
                break
            elif choice == 0:
                return None
            else:
                print("无效的选择，请重新输入。")
        except ValueError:
            print("无效的选择，请重新输入。")

    # 读取选择的文件
    selected_file = files[choice - 1]
    file_path = os.path.join(user_path, selected_file)
    with open(file_path, 'r') as file:
        content = file.read()

    return content


# 信号处理函数
def signal_handler(signal, frame):
    # 在手动结束程序时保存已有的数据
    if len(texts) > 0:
        save_data()
    exit(0)


def save_data():
    df = pd.DataFrame(texts, columns=['时间', '内容'])
    df.to_excel(result_path + uin + '.xlsx', index=False)
    print('导出成功，请查看 ' + result_path + uin + '.xlsx')


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
        r = requests.get(url)
        qrsig = requests.utils.dict_from_cookiejar(r.cookies).get('qrsig')

        with open(temp_path + 'QR.png', 'wb') as f:
            f.write(r.content)

        im = Image.open(temp_path + 'QR.png')
        im = im.resize((350, 350))
        print(time.strftime('%H:%M:%S'), '登录二维码获取成功')

        # 解码二维码
        decoded_objects = decode(im)
        for obj in decoded_objects:
            qr = qrcode.QRCode()
            qr.add_data(obj.data.decode('utf-8'))
            # invert=True白底黑块,有些app不识别黑底白块.
            qr.print_ascii(invert=True)

        return qrsig

    except Exception as e:
        print(e)


def save_user(cookies):
    with open(user_path + cookies.get('uin'), 'w') as f:
        f.write(str(cookies))


def cookie():
    init_flooder()
    select_user = read_files_in_folder()
    if select_user:
        return eval(select_user)
    # 获取 QQ空间 cookie
    qrsig = QR()
    ptqrtoken = ptqrToken(qrsig)

    while True:
        url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara' \
              '%3Dizone&ptqrtoken=' + str(ptqrtoken) + '&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-' \
              + str(time.time()) + '&js_ver=20032614&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&'
        cookies = {'qrsig': qrsig}
        try:
            r = requests.get(url, cookies=cookies)
            if '二维码未失效' in r.text:
                # print(time.strftime('%H:%M:%S'), '二维码未失效')
                pass
            elif '二维码认证中' in r.text:
                print(time.strftime('%H:%M:%S'), '二维码认证中')
            elif '二维码已失效' in r.text:
                print(time.strftime('%H:%M:%S'), '二维码已失效')
            else:
                print(time.strftime('%H:%M:%S'), '登录成功')
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
                    p_skey = requests.utils.dict_from_cookiejar(r.cookies).get('p_skey')
                    save_user(target_cookies)
                    break

                except Exception as e:
                    print(e)

        except Exception as e:
            print(e)

        time.sleep(3)

    return target_cookies


# 登陆后获取到的cookies
cookies = cookie()
# 获取g_tk
g_tk = bkn(cookies.get('p_skey'))
# 获取uin
uin = re.sub(r'o0*', '', cookies.get('uin'))
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


# 获取历史消息列表
def get_message(start, count):
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
    response = requests.get('https://user.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds2_html_pav_all',
                            params=params, cookies=cookies, headers=headers)
    return response


def get_login_user_info():
    response = requests.get('https://r.qzone.qq.com/fcg-bin/cgi_get_portrait.fcg?g_tk=' + str(g_tk) + '&uins=' + uin,
                            headers=headers, cookies=cookies)
    info = response.content.decode('GBK')
    info = info.strip().lstrip('portraitCallBack(').rstrip(');')
    info = json.loads(info)
    return info


def get_message_count():
    # 初始的总量范围
    lower_bound = 0
    upper_bound = 100000  # 假设最大总量为1000000
    total = upper_bound // 2  # 初始的总量为上下界的中间值
    with tqdm(desc="正在获取消息列表数量...", total=17, unit='页') as pbar:
        while lower_bound <= upper_bound:
            response = get_message(total, 100)
            if "li" in response.text:
                # 请求成功，总量应该在当前总量的右侧
                lower_bound = total + 1
            else:
                # 请求失败，总量应该在当前总量的左侧
                upper_bound = total - 1
            total = (lower_bound + upper_bound) // 2  # 更新总量为新的中间值
            pbar.update(1)
    return total


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


if __name__ == '__main__':
    try:
        user_info = get_login_user_info()
        user_nickname = user_info[uin][6]
        print(f"用户<{uin}>,<{user_nickname}>登录成功")
    except Exception as e:
        print(f"登录失败:请重新登录,错误信息:{str(e)}")
        exit(0)
    texts = []
    count = get_message_count()
    try:
        # 注册信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        for i in trange(int(count / 100) + 1, desc='Progress', unit='100条'):
            message = get_message(i * 100, 100).content.decode('utf-8')
            html = process_old_html(message)
            if "li" not in html:
                break
            soup = BeautifulSoup(html, 'html.parser')
            for element in soup.find_all('li', class_='f-single f-s-s'):
                time = None
                text = None
                time_element = element.find('div', class_='info-detail')
                text_element = element.find('p', class_='txt-box-title ellipsis-one')
                if time_element is not None and text_element is not None:
                    time = time_element.get_text().replace('\xa0', ' ')
                    text = text_element.get_text().replace('\xa0', ' ')
                    if text not in [sublist[1] for sublist in texts]:
                        texts.append([time, text])

        if len(texts) > 0:
            save_data()
    except Exception as e:
        print(f"发生异常: {str(e)}")
        if len(texts) > 0:
            save_data()
