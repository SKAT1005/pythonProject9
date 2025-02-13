import asyncio
import configparser
import glob
import os
import sys
import time

from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select
from selenium.webdriver.support.wait import WebDriverWait

config = configparser.ConfigParser()
config.read('history_check.ini', encoding='utf-8')

username = config['arma']['username']
login_arma = config['arma']['login']
password_arma = config['arma']['password']
sleep_time = config['arma']['sleep_time']
channels = config['arma']['channels'].split()

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
good_channel_id = int(config['telegram']['good_channel_id'])
bad_channel_id = int(config['telegram']['bad_channel_id'])

client = telethon.TelegramClient('Client', api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")

options = Options()
pref = {'download.default_directory': os.getcwd()}
options.add_experimental_option('prefs', pref)
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')
driver = webdriver.Chrome(options=options)
driver.get('https://ibank.amra-bank.com/web_banking/protected/welcome.jsf')


async def activate_arma():
    try:
        n = driver.find_element(By.CLASS_NAME, "loginForm-input")
        if n.get_attribute("value"):
            n.clear()
        n.send_keys(login_arma)
    except Exception:
        pass
    try:
        driver.find_element(By.CLASS_NAME, "loginForm-button").click()
    except Exception:
        pass
    try:
        driver.find_element(By.CLASS_NAME, "paddL10").click()
    except Exception:
        pass
    try:
        driver.find_element(By.NAME, "compName").send_keys('text_pk')
    except Exception:
        pass
    try:
        driver.find_element(By.NAME, "password_common").send_keys(password_arma)
    except Exception:
        pass
    try:
        driver.find_element(By.NAME, 'sendPasswordText').click()
        sms_code = input('Введите СМС код: ')
        driver.find_element(By.NAME, "otp_type_3_input").send_keys(sms_code)
    except Exception:
        pass
    try:
        capcha = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, 'g_553142662880465'))
        )
        n = input('Введи капчу: ')
        capcha.send_keys(n)
    except Exception:
        pass
    driver.find_element(By.NAME, "loginButton").click()


async def check_message(phone, amount):
    n = False
    for channel in channels:
        messages = await client.get_messages(int(channel), 9)
        for message in messages:
            message = message.text.split('\n\n')
            if len(message) > 2:
                ph = message[0]
                am = message[1]
                if ph == phone and am == amount:
                    n = True
                    break
        if n:
            break
    if n:
        await client.send_message(good_channel_id, '+')
    else:
        await client.send_message(bad_channel_id, f'Нет сделки по номеру {phone} на сумму {amount}')


async def main():
    await client.start()
    await activate_arma()
    while True:
        driver.get('https://ibank.amra-bank.com/web_banking/protected/history')
        phones = driver.find_elements(By.CLASS_NAME, 'paddR8')[:2]
        amounts = driver.find_elements(By.CLASS_NAME, 'amountBox')[:2]
        for i in range(len(phones)):
            phone = phones[i].text.split()[-1]
            amount = amounts[i].find_element(By.TAG_NAME, 'span').find_element(By.TAG_NAME, 'span')
            amount = amount.text.replace(' ', '')
            await check_message(phone=phone, amount=amount)
        time.sleep(int(sleep_time))


asyncio.run(main())