import json
import os
import re
import sys
import time

import requests

from util import LoginUtil

WORKDIR = "./resource/fetch-all/"
MESSAGE_SAMPLE = 'msg-one.json'
MESSAGE_ALL = 'msg-all.json'


# 获取所有可见的未删除的说说+高清图片（包含2014年之前）
def get_visible_msg_list():
    # 1. 获取说说总条数
    try:
        msgSample = read_txt_file(MESSAGE_SAMPLE)
    except FileNotFoundError as e:
        print("样本缓存未找到，开始请求获取样本")
        qqResponse = get_msg_list(1)
        print("创建缓存文件并写入")
        write_txt_file(MESSAGE_SAMPLE, qqResponse)
        msgSample = read_txt_file(MESSAGE_SAMPLE)

    try:
        json_dict = json.loads(msgSample)
        totalCount = json_dict['total']
        print(f'你的未删除说说总条数{totalCount}')
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        sys.exit(1)

    # 2. 获取所有说说数据
    print('开始不分页获取所有未删除说说')
    try:
        msgAll = read_txt_file(MESSAGE_ALL)
    except FileNotFoundError as e:
        print("缓存未找到，开始请求获取所有未删除说说")
        qqResponse = get_msg_list(totalCount)
        write_txt_file(MESSAGE_ALL, qqResponse)
        msgAll = read_txt_file(MESSAGE_ALL)

    try:
        json_dict = json.loads(msgAll)
        msgList = json_dict['msglist']
        print(f'已获取到数据的说说总条数{len(msgList)}')
    except json.JSONDecodeError as e:
        print(f"JSON解析错误: {e}")
        sys.exit(1)

    # 3. 解析原始JSON写成Markdown
    markdown_content = ''
    for item in msgList:

        myWord = item['content'] if item['content'] else ""
        myCurrentQQName = item['name']
        myCreateTime = format_timestamp(item['created_time'])
        myCurrentSourceName = '\n来自 ' + item['source_name'] if item['source_name'] else ""

        # 如果有图片
        markdown_pictures = ""
        if 'pic' in item:
            for index, myPic in enumerate(item['pic']):
                myPicUrl = myPic['url1']
                myPicFileName = f"{item['tid']}{index}.jpeg"
                get_image(myPicUrl, myPicFileName)
                markdown_pictures += f"![{myPicFileName}](./{myPicFileName})"

        markdown_content += f"## {myCurrentQQName} {myCreateTime}  \n{myWord} {markdown_pictures} \n{myCurrentSourceName}"

        # 有转发的内容
        if 'rt_tid' in item:
            rt_tid = item['rt_tid']
            rtContent = item['rt_con']['content']
            rtQQName = item['rt_uinname']
            rt_uin = item['rt_uin']
            markdown_content += f"\n> {rtQQName} - {rt_uin} : {rtContent}"

        # 有人评论
        if 'commentlist' in item:
            markdown_content += f"\n💬 **{len(item['commentlist'])}条评论回复**\n"
            for index, commentToMe in enumerate(item['commentlist']):
                commentContent = commentToMe['content']
                commentCreateTime = commentToMe['createTime2']
                commentQQName = commentToMe['name']
                commentQQNumber = commentToMe['uin']
                markdown_content += f"- {commentQQName}({commentQQNumber}) : {commentContent} - {commentCreateTime}\n"

        # append write
        markdown_content += "\n\n"

    # write markdown to file
    write_txt_file("所有可见说说.md", markdown_content)


def get_msg_list(num):
    url = 'https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6'
    cookies = LoginUtil.cookie()
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


def write_txt_file(file_name, data):
    if not os.path.exists(WORKDIR):
        os.makedirs(WORKDIR)
    base_path_file_name = os.path.join(WORKDIR, file_name)
    with open(base_path_file_name, 'w', encoding='utf-8') as file:
        file.write(data)


def read_txt_file(file_name):
    base_path_file_name = os.path.join(WORKDIR, file_name)
    if os.path.exists(base_path_file_name):
        print("读取缓存文件")
        with open(base_path_file_name, 'r', encoding='utf-8') as file:
            return file.read()
    else:
        raise FileNotFoundError(f"文件 {base_path_file_name} 不存在")


def format_timestamp(timestamp):
    time_struct = time.localtime(timestamp)
    formatted_time = time.strftime("%Y年%m月%d日 %H:%M:%S", time_struct)
    return formatted_time


def get_image(url, img_name):
    headers = {
        'sec-ch-ua': '"Not;A=Brand";v="24", "Chromium";v="128"',
        'Referer': 'https://user.qzone.qq.com/',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'sec-ch-ua-platform': '"Linux"',
    }

    # 发起GET请求
    response = requests.get(url, headers=headers)

    # 检查请求是否成功
    if response.status_code == 200:
        # 保存图片到本地
        file_path = os.path.join(WORKDIR, img_name)
        with open(file_path, 'wb') as file:
            file.write(response.content)
        print('图片下载成功')
    else:
        print(f'请求失败，状态码：{response.status_code}')


if __name__ == '__main__':
    get_visible_msg_list()
