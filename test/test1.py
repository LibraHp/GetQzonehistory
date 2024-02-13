import requests
from PIL import Image
import time
import re
import os

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

        with open(r'.\QR.png', 'wb') as f:
            f.write(r.content)

        im = Image.open(r'.\QR.png')
        im = im.resize((350, 350))
        print(time.strftime('%H:%M:%S'), '登录二维码获取成功')
        im.show()

        return qrsig

    except Exception as e:
        print(e)


def cookie():
    if os.path.exists('cookies.txt'):
        with open('cookies.txt', 'r') as file:
            cookies = file.read()
            return eval(cookies)
    # 获取 QQ空间 cookie
    qrsig = QR()
    ptqrtoken = ptqrToken(qrsig)

    while True:
        url = 'https://ssl.ptlogin2.qq.com/ptqrlogin?u1=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&ptqrtoken=' + str(
            ptqrtoken) + '&ptredirect=0&h=1&t=1&g=1&from_ui=1&ptlang=2052&action=0-0-' + str(
            time.time()) + '&js_ver=20032614&js_type=1&login_sig=&pt_uistyle=40&aid=549000912&daid=5&'
        cookies = {'qrsig': qrsig}

        try:
            r = requests.get(url, cookies=cookies)

            if '二维码未失效' in r.text:
                print(time.strftime('%H:%M:%S'), '二维码未失效')

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
                url = 'https://ptlogin2.qzone.qq.com/check_sig?pttype=1&uin=' + uin + '&service=ptqrlogin&nodirect=0&ptsigx=' + sigx + '&s_url=https%3A%2F%2Fqzs.qq.com%2Fqzone%2Fv5%2Floginsucc.html%3Fpara%3Dizone&f_url=&ptlang=2052&ptredirect=100&aid=549000912&daid=5&j_later=0&low_login_hour=0&regmaster=0&pt_login_type=3&pt_aid=0&pt_aaid=16&pt_light=0&pt_3rd_aid=0'

                try:
                    r = requests.get(url, cookies=cookies, allow_redirects=False)
                    targetCookies = requests.utils.dict_from_cookiejar(r.cookies)
                    # 存储cookies到本地
                    with open(r'.\cookies.txt', 'w') as f:
                        f.write(str(targetCookies))
                    pSkey = requests.utils.dict_from_cookiejar(r.cookies).get('p_skey')
                    break

                except Exception as e:
                    print(e)

        except Exception as e:
            print(e)

        time.sleep(3)

    return targetCookies


def get_message():
    cookies = cookie()
    g_tk = bkn(cookies.get('p_skey'))
    # 去掉uin首位的o
    uin = cookies.get('uin')[1:]
    print(cookies)
    headers = {
        'authority': 'user.qzone.qq.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
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
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0',
    }
    params = {
        'uin': uin,
        'begin_time': '0',
        'end_time': '0',
        'getappnotification': '1',
        'getnotifi': '1',
        'has_get_key': '0',
        'offset': '0',
        'set': '0',
        'count': '10',
        'useutf8': '1',
        'outputhtmlfeed': '1',
        'scope': '1',
        'g_tk': [
            g_tk,
            g_tk,
        ],
    }
    response = requests.get('https://user.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds2_html_pav_all',
                            params=params, cookies=cookies, headers=headers)
    return response


if __name__ == '__main__':
    message = get_message().text
    json_str = message.strip().lstrip('_Callback(').rstrip(');')
    print(json_str)
