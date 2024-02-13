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
    # 如果文件夹为空
    if not files:
        return None
    # 输出文件列表
    print("已登录用户列表:")
    for i, file in enumerate(files):
        print(f"{i + 1}. {file}")

    # 选择文件
    while True:
        try:
            choice = int(input("请选择要登录的用户序号: "))
            if 1 <= choice <= len(files):
                break
            else:
                print("无效的选择，请重新输入。")
        except ValueError:
            print("无效的选择，请重新输入。")

    # 读取选择的文件
    selected_file = files[choice - 1]
    file_path = os.path.join(user_path, selected_file)
    with open(file_path, 'r') as file:
        content = file.read()

    return content

