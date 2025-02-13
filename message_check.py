import asyncio
import configparser
import datetime
import glob
import os
import sys
import time

import requests
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

config = configparser.ConfigParser()
config.read('message_check.ini', encoding='utf-8')

username = config['gate']['username']
login_gate = config['gate']['login']
password_gate = config['gate']['password']
sleep_time = int(config['gate']['wait_time'])
arma_wait_time = int(config['gate']['arma_wait_time'])
max_wait_time = int(config['gate']['max_wait_time'])

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
good_channel_id = int(config['telegram']['good_channel_id'])
bad_channel_id = int(config['telegram']['bad_channel_id'])
bot_token = config['telegram']['bot_token']
client = telethon.TelegramClient(None, api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")
bot_text = config['telegram']['text']

options = Options()
pref = {'download.default_directory': os.getcwd()}
options.add_experimental_option('prefs', pref)
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')
driver = webdriver.Chrome(options=options)
driver.get('https://panel.gate.cx/')


async def activate_gates():
    try:
        driver.find_element(By.CLASS_NAME, 'YQUVu')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        inputs[0].send_keys(login_gate)
        inputs[1].send_keys(password_gate)
        driver.find_element(By.CLASS_NAME, 'ewUpxh').click()
    except Exception:
        pass


async def check_gate():
    try:
        driver.get('https://panel.gate.cx/messages?page=1')
        container = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ag-center-cols-container'))
        )
        elem = WebDriverWait(container, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'ag-row-even'))
        )
        elem = elem.find_elements(By.CLASS_NAME, 'ag-cell')[-2]
        time = elem.text.split(', ')[1].split(':')
        minute = int(time[0]) * 60 + int(time[1])
        now = datetime.datetime.now()
        now_minute = now.hour * 60 + now.minute
        if now_minute - minute > max_wait_time:
            return False, now_minute - minute
        return True, now_minute - minute
    except Exception as e:
        await client.send_message(bad_channel_id, f'Error gate: {e}')
        return 2, 2



async def check_arma():
    try:
        status = requests.get('https://ibank.amra-bank.com/web_banking/protected/welcome.jsf',
                              timeout=arma_wait_time).status_code
        if status != 200:
            return False
        else:
            return True
    except Exception:
        return False


async def main():
    #await client.start(bot_token=bot_token)
    while True:
        await activate_gates()
        gate, minute = await check_gate()
        if gate == 2:
            pass
        elif gate:
            await client.send_message(good_channel_id, f'В гейте все хорошо. {minute} min')
        else:
            await client.send_message(bad_channel_id, f'Ошибка в гейте. {minute} min')
            await client.send_message(good_channel_id, f'Ошибка в гейте. {minute} min')
        if await check_arma():
            await client.send_message(good_channel_id, 'В арме все хорошо')
        else:
            await client.send_message(bad_channel_id, 'Ошибка в арме')
            await client.send_message(good_channel_id, 'Ошибка в арме')
        time.sleep(sleep_time)


asyncio.run(main())
