from bs4 import BeautifulSoup
from tqdm import trange
import util.RequestUtil as Request
import util.ToolsUtil as Tools
import pandas as pd
if __name__ == '__main__':
    texts = []
    for i in trange(2, desc='Progress', unit='iteration'):
        message = Request.get_message(i*100, 100).content.decode('utf-8')
        html = Tools.process_old_html(message)
        soup = BeautifulSoup(html, 'html.parser')
        for element in soup.find_all('p', class_='txt-box-title ellipsis-one'):
            text = element.get_text().replace('\xa0', ' ')
            if text not in texts:
                texts.append(text)
    # 创建一个DataFrame对象
    df = pd.DataFrame(texts, columns=['内容'])

    # 将DataFrame对象导出为CSV文件，使用UTF-8编码
    df.to_excel('output.xlsx', index=False)
    print(texts)
