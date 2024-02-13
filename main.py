import util.RequestUtil as Request
# import util.ConfigUtil as Config
import os

if __name__ == '__main__':
    message = Request.get_message(0, 10)
    print(message.text)
