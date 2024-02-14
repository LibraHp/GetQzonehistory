from bs4 import BeautifulSoup
from tqdm import trange
import util.RequestUtil as Request
import util.ToolsUtil as Tools
import util.ConfigUtil as Config
import pandas as pd
import signal


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


if __name__ == '__main__':
    try:
        user_info = Request.get_login_user_info()
        user_nickname = user_info[Request.uin][6]
        print(f"用户<{Request.uin}>,<{user_nickname}>登录成功")
    except Exception as e:
        print(f"登录失败:请重新登录,错误信息:{str(e)}")
        exit(0)
    texts = []

    try:
        # 注册信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        for i in trange(1000, desc='Progress', unit='100条'):
            message = Request.get_message(i * 100, 100).content.decode('utf-8')
            html = Tools.process_old_html(message)
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
                if text not in [sublist[1] for sublist in texts] and time is not None and text is not None:
                    texts.append([time, text])

        if len(texts) > 0:
            save_data()
    except Exception as e:
        print(f"发生异常: {str(e)}")
        if len(texts) > 0:
            save_data()
