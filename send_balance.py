import asyncio
import configparser
import os

from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from telethon import events

config = configparser.ConfigParser()
config.read('send_balance.ini', encoding='utf-8')

username = config['arma']['username']
accounts = config['arma']['accounts'].split(', ')
main_account = config['arma']['main_account']
min_balance = int(config['arma']['min_balance'])

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
bot_token = config['telegram']['bot_token']
channel_id = int(config['telegram']['channel_id'])
client = telethon.TelegramClient(None, api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")

options = Options()
pref = {'download.default_directory': os.getcwd()}
options.add_experimental_option('prefs', pref)
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')


async def send_money(amount, driver):
    driver.get('https://ibank.amra-bank.com/web_banking/protected/doc/intrabank_transfer/new')
    driver.find_element(By.NAME, 'AMOUNT').send_keys(amount)  # Ввод суммы
    driver.find_elements(By.CLASS_NAME, 'customRadio')[1].click()  # Выбор оплаты по номеру
    phone_input = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID, 'RCPT_PHONE_NUMBER:phone')))
    phone_input.clear()
    phone_input.send_keys(str(main_account))  # Ввод телефона для отправки
    driver.find_element(By.CLASS_NAME, 'customCheckbox').click()  # Согласие с инфой
    WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID,
                                        'j_id_5d_ad:nextBtnAjax'))).click()  # Переход далее
    WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.ID, 'j_id_5d_2b1:sendBtn'))).click()


async def get_balance(driver):
    driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
    amount = driver.find_element(By.XPATH,
                                 '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[1]').text + driver.find_element(
        By.XPATH, '/html/body/div[1]/div[1]/div[3]/form/div/div/div/div[1]/span/span[1]/span[2]').text
    amount = amount.replace(' ', '').replace('−', '')
    return int(amount.split('.')[0]) // 1000 * 1000


async def activate_arma(login_arma, password_arma, driver):
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


@client.on(events.NewMessage(chats=[channel_id]))
async def get_data(event):
    global action, last_message
    text = event.raw_text
    if text == 'сделать перевод':
        driver = webdriver.Chrome(options=options)
        driver.get('https://ibank.amra-bank.com/web_banking/protected/welcome.jsf')
        summ = 0
        await client.send_message(channel_id, 'Начинаю совершать переводы')
        for account in accounts:
            try:
                login, password = account.split()
                await activate_arma(login, password, driver)
                balance = await get_balance(driver)
                if balance > min_balance:
                    summ += balance-min_balance
                    await send_money(balance-min_balance, driver)
                driver.find_element(By.CLASS_NAME, 'icon-exit').click()
            except Exception:
                pass
        await client.send_message(channel_id, f'Все переводы успешно сделаны. Всего переведено {summ} рублей')
        driver.quit()

async def star_bot():
    await client.start(bot_token=bot_token)
    await client.run_until_disconnected()


if __name__ == '__main__':
    asyncio.run(star_bot())
