import asyncio
import configparser
import glob
import io
import os
import sys
import threading
import time

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from telethon import events

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id = int(config['telegram']['channel_id'])
bot_token = config['telegram']['bot_token']

username = config['arma']['username']
login = config['bank']['login']
password = config['bank']['password']

# session_number = config['google']['session_number']

client = telethon.TelegramClient(None, api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")
last_message_id = [0]

options = Options()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\12')
driver = webdriver.Chrome(options=options)

driver.get("https://ibank.amra-bank.com/web_banking/protected/welcome.jsf")
async def activate_arma():
    try:
        n = driver.find_element(By.CLASS_NAME, "loginForm-input")
        if n.get_attribute("value"):
            n.clear()
        n.send_keys(login)
    except Exception as e:
        pass
    try:
        driver.find_element(By.CLASS_NAME, "loginForm-button").click()
    except Exception as e:
        pass
    try:
        driver.find_element(By.CLASS_NAME, "paddL10").click()
    except Exception as e:
        pass
    try:
        driver.find_element(By.NAME, "compName").send_keys('text_pk')
    except Exception as e:
        pass
    try:
        driver.find_element(By.NAME, "password_common").send_keys(password)
    except Exception as e:
        pass
    try:
        driver.find_element(By.NAME, 'sendPasswordText').click()
        sms_code = input('Введите СМС код: ')
        driver.find_element(By.NAME, "otp_type_3_input").send_keys(sms_code)
    except Exception as e:
        pass
    try:
        capcha = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.ID, 'g_553142662880465'))
        )
        n = input('Введи капчу: ')
        capcha.send_keys(n)
    except Exception as e:
        pass
    driver.find_element(By.NAME, "loginButton").click()

action = True
last_message = ''


@client.on(events.NewMessage(chats=[channel_id]))
async def get_data(event):
    global action, last_message
    text = event.raw_text
    if text == '*':
        action = False
        amount = await get_balance()
        action = True
        await client.send_message(channel_id, f'Остаток: {amount} рублей')
    elif text == '+' and last_message:
        text = last_message.split('\n\n')
        try:
            phone = text[0][2:]
            amount = int(text[1])
            balance = float(await get_balance())
            if amount <= balance:
                action = False
                await client.send_message(channel_id, 'Начинаю обработку платежа')
                await main_arma(phone, amount)
            else:
                await client.send_message(channel_id, f'На балансе недостаточно средств. Текущий баланс: {balance}')
        except Exception:
            pass
    else:
        last_message = text


async def get_balance():
    driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
    amount = driver.find_element(By.XPATH,
                                 '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[1]').text + driver.find_element(
        By.XPATH, '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[2]').text
    return float(amount.replace(' ', ''))


async def send_file(n=1):
    while True:
        if glob.glob("*.pdf"):
            break
        time.sleep(1)
    for file in glob.glob("*.pdf"):
        if n == 1:
            await client.send_file(channel_id, file, caption='✅Документ загружен удачно✅')
            return file
        else:
            await client.send_file(channel_id, file, caption=f'❌{n}❌')
            return file


async def main_arma(phone, amount):
    global last_phone
    t_bank = driver.find_element(By.XPATH,
                                 '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/div[2]/span[2]/a/div')  # Переход в тинькоф
    t_bank.click()
    driver.find_element(By.NAME,
                        'AMOUNT').send_keys(
        amount)  # Ввод суммы
    phone_input = driver.find_element(By.ID,
                                      'TABLE:0:record_masked')
    phone_input.clear()
    phone_input.send_keys(
        str(phone)[2:])  # Ввод телефона для отправки
    driver.find_element(By.CLASS_NAME,
                        'customCheckbox').click()  # Согласие с инфой
    WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID,
                                        'j_id_5z_c1:nextBtn'))).click()  # Переход далее
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.ID, 'buttonsComponent:sendBtn'))
    ).click()
    time.sleep(2)
    driver.find_element(By.XPATH,
                        '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/span/table/tbody/tr[1]').click()  # Переход в чек
    for file in glob.glob("*.pdf"):
        os.remove(file)
    last_phone = phone
    try:
        driver.find_element(By.CLASS_NAME, 'statusRejected-img')
        n = driver.find_element(By.CLASS_NAME, 'statusRejected').text
        driver.find_element(By.XPATH,
                            '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
        await send_file(n)
        sys.exit(0)
    except Exception as e:
        l = 1
        while True:
            if l == 20:
                await client.send_message(channel_id, f'⏳Документ слишком долго загружался⏳')
                sys.exit(0)
            try:
                driver.find_element(By.CLASS_NAME, 'statusExecuted-img')
                driver.find_element(By.XPATH,
                                    '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
                file_name = await send_file()
                driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
                return file_name
            except Exception as e:
                time.sleep(6)
                l += 1
                driver.refresh()


async def star_bot():
    await activate_arma()
    await client.start(bot_token=bot_token)
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(star_bot())
