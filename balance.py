import asyncio
import configparser
import glob
import io
import os
import telebot
import time

from PIL import Image
from selenium.common import TimeoutException
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from telethon import events


config = configparser.ConfigParser()
config.read('balance_config.ini', encoding='utf-8')

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id = int(config['telegram']['channel_id'])
bot_token = config['telegram']['bot_token']


username = config['arma']['username']
accounts = config['arma']['accounts'].split(',')
sleep_time = int(config['arma']['timer'])


gate_login = config['gate']['login']
gate_password = config['gate']['password']

last_message_id = [0]

options = Options()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\12')
driver = webdriver.Chrome(options=options)


def format_number(number):
    """Форматирует число в формате 10.000"""

    if isinstance(number, (int, float)):
        return f"{number:,.0f}".replace(",", " ")
async def get_balance():
    driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
    amount = driver.find_element(By.XPATH,
                                 '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[1]').text + driver.find_element(
        By.XPATH, '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[2]').text
    amount = amount.replace(' ', '').replace('−', '')
    return int(amount.split('.')[0])

async def crop_image(image_path):
    """
    Обрезает изображение.

    Args:
        image_path: Путь к исходному изображению.
        output_path: Путь для сохранения обрезанного изображения.
        x1: Координата x левого верхнего угла области обрезки.
        y1: Координата y левого верхнего угла области обрезки.
        x2: Координата x правого нижнего угла области обрезки.
        y2: Координата y правого нижнего угла области обрезки.
    """
    try:
        img = Image.open(image_path)
        cropped_img = img.crop((1125, 0, img.width, img.height))  # Создаем обрезанную версию
        cropped_img.save(image_path)
    except Exception as e:
        print(f"Ошибка при обработке изображения: {e}")

async def activate_arma(login_arma, password_arma):
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

async def gate():
    driver.get('https://panel.gate.cx')
    try:
        driver.find_element(By.CLASS_NAME, 'YQUVu')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        inputs[0].send_keys(gate_login)
        inputs[1].send_keys(gate_password)
        driver.find_element(By.CLASS_NAME, 'ewUpxh').click()
    except Exception:
        pass
    time.sleep(2)
    driver.get('https://panel.gate.cx/dashboard')
    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, 'canvas'))
    )
    driver.execute_script("arguments[0].scrollIntoView();", canvas)
    actions = ActionChains(driver)
    actions.move_to_element_with_offset(canvas, xoffset=620, yoffset=0).perform()
    canvas.screenshot('122.png')
    await crop_image('122.png')
async def main():
    client = telebot.TeleBot(bot_token)
    while True:
        driver.get("https://ibank.amra-bank.com/web_banking/protected/welcome.jsf")
        text = ''
        summa = 0
        for account in accounts:
            login_arma, password_arma, bank_id = account.split()
            await activate_arma(login_arma, password_arma)
            balance = await get_balance()
            summa += balance
            text += f'{bank_id} - {format_number(balance)}\n'
            driver.find_element(By.CLASS_NAME, 'icon-exit').click()
        text += f'\n {format_number(summa)}'
        client.send_message(int(channel_id), text)
        await gate()
        client.send_photo(channel_id, open('122.png', 'rb'))
        os.remove('122.png')
        time.sleep(sleep_time)


while True:
    asyncio.run(main())
