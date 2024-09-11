import platform
import subprocess
from bs4 import BeautifulSoup
from tqdm import trange
import util.RequestUtil as Request
import util.ToolsUtil as Tools
import util.ConfigUtil as Config
import pandas as pd
import signal
import os
import re
from tqdm import trange,tqdm
import requests
import time

# 信号处理函数
def signal_handler(signal, frame):
    # 在手动结束程序时保存已有的数据
    if len(texts) > 0:
        save_data()
    exit(0)



def save_data():
    df = pd.DataFrame(texts, columns=['时间', '内容'])
    df.to_excel(Config.result_path + Request.uin + '.xlsx', index=False)
    print('导出成功，请查看 ' + Config.result_path + Request.uin + '.xlsx')

def save_data():
    user_save_path = Config.result_path + Request.uin + '/'
    pic_save_path = user_save_path + 'pic/'
    if not os.path.exists(user_save_path):
        os.makedirs(user_save_path)
        print(f"Created directory: {user_save_path}")
    if not os.path.exists(pic_save_path):
        os.makedirs(pic_save_path)
        print(f"Created directory: {pic_save_path}")
    pd.DataFrame(texts, columns=['时间', '内容', '图片链接']).to_excel(user_save_path + Request.uin + '_全部列表.xlsx', index=False)
    pd.DataFrame(all_friends, columns=['昵称', 'QQ', '空间主页']).to_excel(user_save_path + Request.uin + '_好友列表.xlsx', index=False)
    for item in tqdm(texts, desc="处理消息列表", unit="item"):
        item_text = item[1]
        item_pic_link = item[2]
        if item_pic_link is not None and len(item_pic_link) > 0 and 'http' in item_pic_link:
            # 保存图片
            pic_name = re.sub(r'[\\/:*?"<>|]', '_', item_text) + '.jpg'
                # 去除文件名中的空格
            pic_name = pic_name.replace(' ', '')
    
            # 限制文件名长度
            if len(pic_name) > 40:
                pic_name = pic_name[:40] + '.jpg'
            # pic_name = pic_name.split('：')[1] + '.jpg'
            response = requests.get(item_pic_link)
            if response.status_code == 200:
                with open(pic_save_path + pic_name, 'wb') as f:
                    f.write(response.content)
        if user_nickname in item_text:
            if '留言' in item_text:
                leave_message.append(item)
            elif '转发' in item_text:
                forward_message.append(item)
            else:
                user_message.append(item)
        else:
            other_message.append(item)
    pd.DataFrame(user_message, columns=['时间', '内容', '图片链接']).to_excel(user_save_path + Request.uin + '_说说列表.xlsx', index=False)
    pd.DataFrame(forward_message, columns=['时间', '内容', '图片链接']).to_excel(user_save_path + Request.uin + '_转发列表.xlsx', index=False)
    pd.DataFrame(leave_message, columns=['时间', '内容', '图片链接']).to_excel(user_save_path + Request.uin + '_留言列表.xlsx', index=False)
    pd.DataFrame(other_message, columns=['时间', '内容', '图片链接']).to_excel(user_save_path + Request.uin + '_其他列表.xlsx', index=False)
    print('\033[36m' + '导出成功，请查看 ' + user_save_path + Request.uin + ' 文件夹内容' + '\033[0m')
    print('\033[32m' + '共有 ' + str(len(texts)) + ' 条消息' + '\033[0m')
    print('\033[36m' + '最早的一条说说发布在' + texts[texts.__len__() - 1][0] + '\033[0m')
    print('\033[32m' + '好友列表共有 ' + str(len(all_friends)) + ' 个好友' + '\033[0m')
    print('\033[36m' + '说说列表共有 ' + str(len(user_message)) + ' 条说说' + '\033[0m')
    print('\033[32m' + '转发列表共有 ' + str(len(forward_message)) + ' 条转发' + '\033[0m')
    print('\033[36m' + '留言列表共有 ' + str(len(leave_message)) + ' 条留言' + '\033[0m')
    print('\033[32m' + '其他列表共有 ' + str(len(other_message)) + ' 条内容' + '\033[0m')
    print('\033[36m' + '图片列表共有 ' + str(len(os.listdir(pic_save_path))) + ' 张图片' + '\033[0m')
    current_directory = os.getcwd()
    # os.startfile(current_directory + user_save_path[1:])
    open_file(current_directory + user_save_path[1:])
    os.system('pause')
    
def open_file(file_path):
    # 检查操作系统
    if platform.system() == 'Windows':
        # Windows 系统使用 os.startfile
        os.startfile(file_path)
    elif platform.system() == 'Darwin':
        # macOS 系统使用 subprocess 和 open 命令
        subprocess.run(['open', file_path])
    elif platform.system() == 'Linux':
        # Linux 系统使用 subprocess 和 xdg-open 命令
        subprocess.run(['xdg-open', file_path])
    else:
        print(f"Unsupported OS: {platform.system()}")


if __name__ == '__main__':
    try:
        user_info = Request.get_login_user_info()
        user_nickname = user_info[Request.uin][6]
        print(f"用户<{Request.uin}>,<{user_nickname}>登录成功")
    except Exception as e:
        print(f"登录失败:请重新登录,错误信息:{str(e)}")
        exit(0)
    texts = []
    all_friends = []
    other_message = []
    user_message = []
    leave_message = []
    forward_message = []
    count = Request.get_message_count()
    try:
        # 注册信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        for i in trange(int(count / 100) + 1, desc='Progress', unit='100条'):
            message = Request.get_message(i * 100, 100).content.decode('utf-8')
            time.sleep(0.2)
            html = Tools.process_old_html(message)
            if "li" not in html:
                continue
            soup = BeautifulSoup(html, 'html.parser')
            for element in soup.find_all('li', class_='f-single f-s-s'):
                put_time = None
                text = None
                img = None
                friend_element = element.find('a', class_='f-name q_namecard')
                # 获取好友昵称和QQ
                if friend_element is not None:
                    friend_name = friend_element.get_text()
                    friend_qq = friend_element.get('link')[9:]
                    friend_link = friend_element.get('href')
                    if friend_qq not in [sublist[1] for sublist in all_friends]:
                        all_friends.append([friend_name, friend_qq, friend_link])
                time_element = element.find('div', class_='info-detail')
                text_element = element.find('p', class_='txt-box-title ellipsis-one')
                img_element = element.find('a', class_='img-item')
                if time_element is not None and text_element is not None:
                    put_time = time_element.get_text().replace('\xa0', ' ')
                    text = text_element.get_text().replace('\xa0', ' ')
                    if img_element is not None:
                        img = img_element.find('img').get('src')
                    if text not in [sublist[1] for sublist in texts]:
                        texts.append([put_time, text, img])

        if len(texts) > 0:
            save_data()
    except Exception as e:
        print(f"发生异常: {str(e)}")
        if len(texts) > 0:
            save_data()