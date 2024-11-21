import asyncio
import configparser
import glob
import io
import os
import time

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

config = configparser.ConfigParser()
config.read('config.ini')

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id = int(config['telegram']['channel_id'])
username = config['google']['username']
login = config['google']['login']
password = config['google']['password']

client = telethon.TelegramClient('user', api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")
last_message_id = [0]

options = Options()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\12')
driver = webdriver.Chrome(options=options)

driver.get("https://ibank.amra-bank.com/web_banking/protected/welcome.jsf")
try:
    n = driver.find_element(By.CLASS_NAME, "loginForm-input")
    time.sleep(2)
    if n.get_attribute("value"):
        pass
    else:
        n.send_keys(login)
except Exception:
    pass
try:
    driver.find_element(By.CLASS_NAME, "customCheckbox").click()
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
    driver.find_element(By.NAME, "password_common").send_keys(password)
except Exception:
    pass
try:
    driver.find_element(By.NAME, 'sendPasswordText').click()
    sms_code = input('Введите СМС код: ')
    driver.find_element(By.NAME, "otp_type_3_input").send_keys(sms_code)
except Exception:
    pass
try:
    capcha = WebDriverWait(driver, 5).until(
        EC.presence_of_element_located((By.ID, 'g_553142662880465'))
    )
    n = input('Введи капчу: ')
    capcha.send_keys(n)
except Exception:
    pass
driver.find_element(By.NAME, "loginButton").click()


async def get_data():
    lsl = await client.get_messages(channel_id, 2)
    n = []
    for i in lsl:
        n.append(i)

    if n[0].text == '+':
        message = n[1]
        text = message.text.split('\n\n')
        try:
            phone = text[0][2:]
            amount = int(text[1])
            return phone, amount
        except Exception:
            return None, None
    return None, None


async def send_file(n):
    while True:
        if glob.glob("*.pdf"):
            break
        time.sleep(1)
    for file in glob.glob("*.pdf"):
        await client.send_file(channel_id, file, caption=n)

        driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
        amount = driver.find_element(By.XPATH,
                                     '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[1]').text + driver.find_element(
            By.XPATH, '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[2]').text
        await client.send_message(channel_id, f'Остаток: {amount} рублей')
        os.remove(file)
        break


async def main():
    await client.connect()
    while True:
        phone, amount = await get_data()
        if phone and amount:
            t_bank = driver.find_element(By.XPATH,
                                         '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/div[2]/span[2]/a/div')  # Переход в тинькоф
            t_bank.click()
            driver.find_element(By.XPATH,
                                '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/table/tbody/tr[3]/td[2]/input').send_keys(
                amount)  # Ввод суммы
            driver.find_element(By.XPATH,
                                '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/span[3]/table/tbody/tr/td[2]/div/div[1]/span/input').send_keys(
                str(phone))  # Ввод телефона для отправки
            driver.find_element(By.XPATH,
                                '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/span[5]/span[1]/label').click()  # Согласие с инфой
            driver.find_element(By.XPATH,
                                '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/span[7]/input[2]').click()  # Переход далее
            element = WebDriverWait(driver, 100).until(
                EC.presence_of_element_located((By.ID, 'buttonsComponent:sendBtn'))
            )
            element.click()  # Отправление оплаты
            time.sleep(10)
            driver.refresh()
            driver.find_element(By.XPATH,
                                '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/span/table/tbody/tr[1]').click()  # Переход в чек
            try:
                driver.find_element(By.CLASS_NAME, 'statusRejected-img')
                n = driver.find_element(By.CLASS_NAME, 'statusRejected').text
                n = f'❌{n}❌'
                driver.find_element(By.XPATH,
                                    '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
                await send_file(n)
            except Exception:
                l = 1
                while True:
                    if l == 10:
                        await client.send_message(channel_id, f'⏳Документ слишком долго загружался⏳')
                        break
                    try:
                        driver.find_element(By.CLASS_NAME, 'statusExecuted-img')
                        n = '✅Документ загружен удачно✅'
                        driver.find_element(By.XPATH,
                                            '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
                        await send_file(n)
                        break
                    except Exception:
                        time.sleep(6)
                        l += 1
                        driver.refresh()
        else:
            driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
            time.sleep(5)


asyncio.run(main())
