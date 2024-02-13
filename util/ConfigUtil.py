import configparser

config = configparser.ConfigParser()
config.read('./resource/config/config.ini')

temp_path = config.get('File', 'temp')
user_path = config.get('File', 'user')