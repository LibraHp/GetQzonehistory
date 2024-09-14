import json
import os
import re
import sys
import time

import requests
from tqdm import tqdm

from util import RequestUtil as Request
from util import LoginUtil
from util import ToolsUtil as Tool

WORKDIR = "./resource/fetch-all/"
USER_QZONE_INFO = 'user_qzone_info.json'
QZONE_MOMENTS_ALL = 'qzone_moments_all.json'


# 获取所有可见的未删除的说说+高清图片（包含2014年之前）
def get_visible_moments_list():
    # 1. 获取说说总条数
    user_qzone_info = Tool.read_txt_file(WORKDIR, USER_QZONE_INFO)
    if not user_qzone_info:
        # 样本缓存未找到，开始请求获取样本
        qq_userinfo_response = get_user_qzone_info(1)
        Tool.write_txt_file(WORKDIR, USER_QZONE_INFO, qq_userinfo_response)
        user_qzone_info = Tool.read_txt_file(WORKDIR, USER_QZONE_INFO)
    if not Tool.is_valid_json(user_qzone_info):
        print("获取QQ空间信息失败")
        return None
    json_dict = json.loads(user_qzone_info)
    totalMomentsCount = json_dict['total']
    print(f'你的未删除说说总条数{totalMomentsCount}')

    # 当前未删除说说总数为0, 直接返回
    if totalMomentsCount == 0:
        return None

    # 2. 获取所有说说数据
    print("开始获取所有未删除说说")
    qzone_moments_all = Tool.read_txt_file(WORKDIR, QZONE_MOMENTS_ALL)
    if not qzone_moments_all:
        # 缓存未找到，开始请求获取所有未删除说说
        qq_userinfo_response = get_user_qzone_info(totalMomentsCount)
        Tool.write_txt_file(WORKDIR, QZONE_MOMENTS_ALL, qq_userinfo_response)
        qzone_moments_all = Tool.read_txt_file(WORKDIR, QZONE_MOMENTS_ALL)

    if not Tool.is_valid_json(qzone_moments_all):
        print("获取QQ空间说说失败")
        return None
    json_dict = json.loads(qzone_moments_all)
    qzone_moments_list = json_dict['msglist']
    print(f'已获取到数据的说说总条数{len(qzone_moments_list)}')

    # 3. 添加说说列表
    texts = []
    for item in tqdm(qzone_moments_list, desc="获取未删除说说", unit="条"):
        content = item['content'] if item['content'] else ""
        nickname = item['name']
        create_time = Tool.format_timestamp(item['created_time'])
        pictures = ""
        # 如果有图片
        if 'pic' in item:
            for index, picture in enumerate(item['pic']):
                pictures += picture['url1'] + ","
        # 去除最后一个逗号
        pictures = pictures[:-1] if pictures != "" else pictures
        comments = []
        if 'commentlist' in item:
            for index, commentToMe in enumerate(item['commentlist']):
                comment_content = commentToMe['content']
                comment_create_time = commentToMe['createTime2']
                comment_nickname = commentToMe['name']
                comment_uin = commentToMe['uin']
                # 时间，内容，昵称，QQ号
                comments.append([comment_create_time, comment_content, comment_nickname, comment_uin])

        # 格式：时间、内容、图片链接、转发内容、评论内容
        texts.append([create_time, f"{nickname} ：{content}", pictures, comments])
    return texts


# 获取用户QQ空间相关信息
def get_user_qzone_info(num):
    url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6'
    cookies = Request.cookies
    g_tk = LoginUtil.bkn(cookies.get('p_skey'))
    qqNumber = re.sub(r'o0*', '', cookies.get('uin'))
    skey = cookies.get('skey')
    p_uin = cookies.get('p_uin')
    pt4_token = cookies.get('pt4_token')
    p_skey = cookies.get('p_skey')
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'cookie': f'uin={p_uin};skey={skey};p_uin={p_uin};pt4_token={pt4_token};p_skey={p_skey}',
        'priority': 'u=1, i',
        'referer': f'https://user.qzone.qq.com/{qqNumber}/main',
        'sec-ch-ua': '"Not;A=Brand";v="24", "Chromium";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
    }

    params = {
        'uin': f'{qqNumber}',
        'ftype': '0',
        'sort': '0',
        'pos': '0',
        'num': f'{num}',
        'replynum': '100',
        'g_tk': f'{g_tk}',
        'callback': '_preloadCallback',
        'code_version': '1',
        'format': 'jsonp',
        'need_private_comment': '1'
    }
    try:
        response = requests.get(url, headers=headers, params=params)
    except Exception as e:
        print(e)
    rawResponse = response.text
    # 使用正则表达式去掉 _preloadCallback()，并提取其中的 JSON 数据
    raw_txt = re.sub(r'^_preloadCallback\((.*)\);?$', r'\1', rawResponse, flags=re.S)
    # 再转一次是为了去掉响应值本身自带的转义符http:\/\/ 
    json_dict = json.loads(raw_txt)
    if json_dict['code'] != 0:
        print(f"错误 {json_dict['message']}")
        sys.exit(1)
    return json.dumps(json_dict, indent=2, ensure_ascii=False)


if __name__ == '__main__':
    get_visible_moments_list()
