import asyncio
import configparser
import glob
import os
import sys
import time

import telebot
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
sleep_time = int(config['amobile']['sleep_time'])

bot_token = config['telegram']['bot_token']
channel_id = config['telegram']['channel_id']

options = Options()
pref = {'download.default_directory': os.getcwd()}
options.add_experimental_option('prefs', pref)
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')
driver = webdriver.Chrome(options=options)
driver.get('https://panel.gate.cx/')



def format_number(number):
    """Форматирует число в формате 10.000"""

    if isinstance(number, (int, float)):
        return f"{number:,.0f}".replace(",", " ")
def get_balance():
    amount = int(driver.find_elements(By.CLASS_NAME, 'card_ballance')[1].text)
    return amount

def activate_amobile(login, password):
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

def main():
    client = telebot.TeleBot(bot_token)
    while True:
        text = ''
        summa = 0
        for account in amobile_data:
            login_amobile, password_amobile, bank_id = account.split()
            activate_amobile(login_amobile, password_amobile)
            balance = get_balance()
            summa += balance
            text += f'{bank_id} - {format_number(balance)}\n'
            driver.find_element(By.CLASS_NAME, 'logout_btn').click()
            time.sleep(5)
        text += f'\n {format_number(summa)}'
        client.send_message(int(channel_id), text)
        time.sleep(sleep_time)




if __name__ == '__main__':
    main()
