import asyncio
import configparser
import glob
import os
import sys
import time

from PIL import Image
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from telethon import events

config = configparser.ConfigParser()
config.read('amobile_and_gate.ini', encoding='utf-8')

username = config['amobile']['username']
amobile_data = config['amobile']['amobile_data'].split(', ')
url = config['amobile']['url']
min_balance = int(config['amobile']['min_balance'])
main_phone = config['amobile']['main_phone']

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id = int(config['telegram']['channel_id'])
bot_token = config['telegram']['bot_token']
client = telethon.TelegramClient(None, api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")

options = Options()
pref = {'download.default_directory': os.getcwd()}
options.add_experimental_option('prefs', pref)
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')


async def main_amobile(amount, driver):
    driver.get(url)
    phone_input = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID,
                                        'payment_input_phone')))
    phone_input.clear()
    for i in main_phone:
        phone_input.send_keys(i)
    amount_input = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID,
                                        'payment_input_amount')))
    amount_input.clear()
    amount_input.send_keys(amount)
    driver.find_element(By.NAME, 'button').click()
    try:
        WebDriverWait(driver, 50).until(
            EC.presence_of_element_located((By.CLASS_NAME,
                                            'js-payment-confirm-btn'))).click()
    except Exception:
        await client.send_message(channel_id, 'Ошибка с отправкой чека')
        sys.exit(0)
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CLASS_NAME,
                                        'swal2-confirm'))).click()


async def get_balance(driver):
    amount = driver.find_elements(By.CLASS_NAME, 'card_ballance')[1].text
    return int(amount.split('.')[0]) // 1000 * 1000


async def activate_amobile(login, password, driver):
    driver.find_element(By.CLASS_NAME, 'sign-in-btn').click()
    try:
        for i in login:
            driver.find_element(By.ID, 'sign-in__phone').send_keys(i)
        driver.find_element(By.CLASS_NAME, 'submit-btn').click()
        time.sleep(3)
        driver.find_element(By.ID, "sign-up__sms").send_keys(password)
        driver.find_element(By.CLASS_NAME, 'submit-btn').click()
    except Exception as e:
        pass


@client.on(events.NewMessage(chats=[channel_id]))
async def get_data(event):
    global action, last_message
    text = event.raw_text
    if text == 'сделать перевод':
        driver = webdriver.Chrome(options=options)
        driver.get('https://dengi.a-mobile.biz')
        summ = 0
        await client.send_message(channel_id, 'Начинаю совершать переводы')
        for account in amobile_data:
            try:
                login, password = account.split()
                await activate_amobile(login, password, driver)
                balance = await get_balance(driver)
                if balance > min_balance:
                    summ += balance - min_balance
                    await main_amobile(balance - min_balance, driver)
                driver.find_element(By.CLASS_NAME, 'logout_btn').click()
            except Exception:
                pass
            time.sleep(5)
        await client.send_message(channel_id, f'Все переводы успешно сделаны. Всего переведено {summ} рублей')
        driver.quit()


async def star_bot():
    await client.start(bot_token=bot_token)
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(star_bot())
