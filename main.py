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
    df = pd.DataFrame(texts, columns=['内容'])
    df.to_excel(Config.result_path + Request.uin + '.xlsx', index=False)
    print('导出成功，请查看 ' + Config.result_path + Request.uin + '.xlsx')


if __name__ == '__main__':
    user_info = Request.get_login_user_info()
    user_nickname = user_info[Request.uin][6]
    print(f"用户<{Request.uin}>,<{user_nickname}>登录成功")
    texts = []

    try:
        # 注册信号处理函数
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        for i in trange(1000, desc='Progress', unit='iteration'):
            message = Request.get_message(i * 100, 100).content.decode('utf-8')
            html = Tools.process_old_html(message)
            if "li" not in html:
                break
            soup = BeautifulSoup(html, 'html.parser')
            for element in soup.find_all('p', class_='txt-box-title ellipsis-one'):
                text = element.get_text().replace('\xa0', ' ')
                if text not in texts:
                    texts.append(text)

        if len(texts) > 0:
            save_data()
    except Exception as e:
        print(f"发生异常: {str(e)}")
        if len(texts) > 0:
            save_data()
