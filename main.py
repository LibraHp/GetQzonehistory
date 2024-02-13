from bs4 import BeautifulSoup
from tqdm import trange
import util.RequestUtil as Request
import util.ToolsUtil as Tools
import util.ConfigUtil as Config
import pandas as pd

if __name__ == '__main__':
    user_info = Request.get_login_user_info()
    user_nickname = user_info[Request.uin][6]
    print(f"用户<{Request.uin}>,<{user_nickname}>登录成功")
    texts = []
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
    # 创建一个DataFrame对象
    df = pd.DataFrame(texts, columns=['内容'])

    # 导出为Excel
    df.to_excel(Config.result_path + Request.uin + '.xlsx', index=False)
    print('导出成功,请查看 ' + Config.result_path + Request.uin + '.xlsx')
