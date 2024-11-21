import configparser

import telethon

config = configparser.ConfigParser()
config.read('config.ini')

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id = int(config['telegram']['channel_id'])
phone = config['telegram']['phone']

client = telethon.TelegramClient('212122131', api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")
client.start(phone=phone, password='19097007')