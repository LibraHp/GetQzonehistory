import util.RequestUtil as Request


# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    message = Request.get_message(0, 10)
    print(message.text)

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
