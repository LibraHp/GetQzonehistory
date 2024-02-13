import configparser
import os

config = configparser.ConfigParser()
config.read('./resource/config/config.ini')

temp_path = config.get('File', 'temp')
user_path = config.get('File', 'user')


def save_user(cookies):
    with open(user_path + cookies.get('uin'), 'w') as f:
        f.write(str(cookies))


def read_files_in_folder():
    # 获取文件夹下的所有文件
    files = os.listdir(user_path)

    # 输出文件列表
    print("文件列表:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")

    # 选择文件
    choice = int(input("请选择要读取的文件编号: "))

    # 读取选择的文件
    selected_file = files[choice - 1]
    file_path = os.path.join(user_path, selected_file)
    with open(file_path, 'r') as file:
        content = file.read()

    return content

