import re
import requests
import json


def qzone_login():
    cookies = {
        'ptui_loginuin': '1941163264',
        'RK': 'nzPEtRXmWI',
        'ptcz': '4b478c47ddfaf994cad9c3eeb6099336c6302fdde27eb31949fd0d8502e7aed6',
        'pgv_pvid': '249131564',
        'qz_screen': '1707x960',
        'QZ_FE_WEBP_SUPPORT': '1',
        'cpu_performance_v8': '1',
        '_qpsvr_localtk': '0.0676035804419064',
        'pgv_info': 'ssid=s3673858535',
        'uin': 'o1941163264',
        'p_uin': 'o1941163264',
        'pt4_token': 'QUuDx3v5A1fbS9y1V-bgUZvp4AXSGeEt2897lTJUpgc_',
        'p_skey': '-RBLfzmoS*kIv9TQZMXaVjOEPuHcxMPsAQdhB6uSOdg_',
        'Loading': 'Yes',
        '1941163264_todaycount': '0',
        '1941163264_totalcount': '20087',
        '__Q_w_s__QZN_TodoMsgCnt': '1',
        '__layoutStat': '12',
    }

    headers = {
        'authority': 'user.qzone.qq.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        # Requests sorts cookies= alphabetically
        # 'cookie': 'ptui_loginuin=1941163264; RK=nzPEtRXmWI; ptcz=4b478c47ddfaf994cad9c3eeb6099336c6302fdde27eb31949fd0d8502e7aed6; pgv_pvid=249131564; qz_screen=1707x960; QZ_FE_WEBP_SUPPORT=1; cpu_performance_v8=1; _qpsvr_localtk=0.0676035804419064; pgv_info=ssid=s3673858535; uin=o1941163264; p_uin=o1941163264; pt4_token=QUuDx3v5A1fbS9y1V-bgUZvp4AXSGeEt2897lTJUpgc_; p_skey=-RBLfzmoS*kIv9TQZMXaVjOEPuHcxMPsAQdhB6uSOdg_; Loading=Yes; 1941163264_todaycount=0; 1941163264_totalcount=20087; __Q_w_s__QZN_TodoMsgCnt=1; __layoutStat=12',
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
        'uin': '1941163264',
        'begin_time': '0',
        'end_time': '0',
        'getappnotification': '1',
        'getnotifi': '1',
        'has_get_key': '0',
        'offset': '15731',
        'set': '0',
        'count': '10',
        'useutf8': '1',
        'outputhtmlfeed': '1',
        'grz': '0.791498607065434',
        'scope': '1',
        'g_tk': [
            '1928892726',
            '1928892726',
        ],
    }

    response = requests.get('https://user.qzone.qq.com/proxy/domain/ic2.qzone.qq.com/cgi-bin/feeds/feeds2_html_pav_all',
                            params=params, cookies=cookies, headers=headers)
    return response


response = qzone_login()
json_str = response.text.strip().lstrip('_Callback(').rstrip(');')
# 将属性值的单引号替换为双引号
output_str = re.sub(r"'([^']*)'", r'"\1"', json_str)
print(output_str)
output_str = re.sub(r'(\w+)(:)', r'"\1"\2', output_str)
# 移除多余的换行和制表符
output_str = output_str.replace('\n', '').replace('\t', '').replace(' ', '')
print(output_str)

