import asyncio
import configparser
import glob
import os
import sys
import time
from timeit import default_repeat

from PIL import Image
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

config = configparser.ConfigParser()
config.read('amobile_and_gate.ini', encoding='utf-8')

username = config['amobile']['username']
login_amobile = config['amobile']['login']
password_amobile = config['amobile']['password']
t_bank_url = config['amobile']['t_bank_url']
sber_bank_url = config['amobile']['sber_bank_url']

login_gate = config['gate']['login']
password_gate = config['gate']['password']
sleep_time = int(config['gate']['wait_time'])

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

gate_window = driver.window_handles[0]
driver.execute_script("window.open('https://dengi.a-mobile.biz/');")
amobile_window = driver.window_handles[1]
last_phone = ''




async def main_amobile(phone, amount, bank):
    global last_phone
    driver.switch_to.window(amobile_window)
    if bank == 'T-Банк (Тинькофф)':
        driver.get(t_bank_url)
    elif bank == 'Сбербанк':
        driver.get(sber_bank_url)
    else:
        await client.send_message(bad_channel_id, 'Неверный банк')
        sys.exit(0)
    phone_input = WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID,
                                        'payment_input_phone')))
    phone_input.clear()
    for i in phone:
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
        if 'ошибка внешней системы' in driver.find_element(By.ID, 'swal2-content').text.lower():
            modal = driver.find_element(By.CLASS_NAME, 'swal2-modal')
            modal.screenshot('receipt.png')
            return False
        await client.send_message(bad_channel_id, 'Ошибка с отправкой чека')
        sys.exit(0)
    WebDriverWait(driver, 120).until(
        EC.presence_of_element_located((By.CLASS_NAME,
                                        'swal2-confirm'))).click()
    for file in glob.glob("*.png"):
        os.remove(file)
    last_phone = phone
    element = driver.find_element(By.CLASS_NAME, 'paymnent-success-footer')
    first = element.find_element(By.TAG_NAME, 'a')
    second = element.find_element(By.TAG_NAME, 'ul')
    driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", first)
    driver.execute_script("""var element = arguments[0];element.parentNode.removeChild(element);""", second)
    receipt = driver.find_element(By.CLASS_NAME, 'payment-success-content')
    driver.execute_script("arguments[0].scrollIntoView();", receipt)
    while True:
        receipt.screenshot('receipt.png')
        img = Image.open('receipt.png')
        img = img.convert("RGB")  # Convert to RGB, handling potential errors

        pixel_color = img.getpixel((80, 60))
        if pixel_color != (247,247,247):
            os.remove('receipt.png')
            time.sleep(2)
        else:
            await client.send_file(good_channel_id, open('receipt.png', 'rb'))
            return True


async def activate_amobile():
    driver.switch_to.window(amobile_window)
    driver.find_element(By.CLASS_NAME, 'sign-in-btn').click()
    try:
        for i in login_amobile:
            driver.find_element(By.ID, 'sign-in__phone').send_keys(i)
        driver.find_element(By.CLASS_NAME, 'submit-btn').click()
        time.sleep(3)
        driver.find_element(By.ID, "sign-up__sms").send_keys(password_amobile)
        driver.find_element(By.CLASS_NAME, 'submit-btn').click()
    except Exception as e:
        pass


async def activate_gates():
    driver.switch_to.window(gate_window)
    try:
        driver.find_element(By.CLASS_NAME, 'YQUVu')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        inputs[0].send_keys(login_gate)
        inputs[1].send_keys(password_gate)
        driver.find_element(By.CLASS_NAME, 'ewUpxh').click()
    except Exception as e:
        with open('error.txt', 'a') as file:
            file.write(f'{e}\n')
    time.sleep(2)
    driver.get('https://panel.gate.cx/requests?page=1')


async def send_message(number, phone, summa, course, bank):
    text = f'{phone}\n\n' \
           f'{summa}\n\n' \
           f'Номер сделки: {number}\n' \
           f'Курс: {course}\n' \
           f'{bot_text}\n' \
           f'{bank}'
    await client.send_message(good_channel_id, text)
    time.sleep(1)
    await client.send_message(good_channel_id, '+')


async def gate():
    await client.start(bot_token=bot_token)
    await activate_gates()
    await activate_amobile()
    driver.switch_to.window(gate_window)
    last_number = 0
    while True:
        try:
            try:
                panel = WebDriverWait(driver, sleep_time).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'bWtUkw')))
                WebDriverWait(panel, sleep_time).until(
                    EC.presence_of_all_elements_located((By.TAG_NAME, 'span')))[1].click()
                container = WebDriverWait(driver, sleep_time).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'ag-center-cols-container')))
            except Exception as e:
                driver.refresh()
            else:
                try:
                    time.sleep(1)
                    n = WebDriverWait(container, sleep_time).until(
                        EC.presence_of_all_elements_located((By.CLASS_NAME, 'ag-row-not-inline-editing'))
                    )
                except Exception as e:
                    driver.refresh()
                    driver.switch_to.window(amobile_window)
                    driver.refresh()
                    driver.switch_to.window(gate_window)
                    time.sleep(1)
                else:
                    time.sleep(1)
                    elems = container.find_elements(By.CLASS_NAME, 'ag-row-not-inline-editing')
                    for elem in elems[::-1]:
                        buttons = elem.find_elements(By.TAG_NAME, 'button')
                        buttons[0].click()
                        time.sleep(2)
                        cell = elem.find_elements(By.CLASS_NAME, 'ag-cell-not-inline-editing')
                        number = WebDriverWait(cell[0], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-hEwMvu'))).text
                        summa = int(WebDriverWait(cell[2], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-hEwMvu'))).text[:-2])
                        phone = WebDriverWait(cell[3], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-hEwMvu'))).text.replace(' ', '')
                        dollar = float(WebDriverWait(cell[4], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-hEwMvu'))).text[:-5])
                        bank = WebDriverWait(cell[3], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-eFzpJt'))).text
                        cource = round(summa / dollar, 2)
                        history = open('history.txt', 'r').readlines()
                        if f'{number}\n' in history or number == last_number:
                            await client.send_message(bad_channel_id, 'Номер сделки повторился')
                            sys.exit(0)
                        else:
                            last_number = number
                            file = open('history.txt', 'a')
                            file.write(f'{number}\n')
                            file.close()
                        await send_message(number=number, course=cource, phone=phone, summa=summa, bank=bank)
                        status = await main_amobile(phone=phone, amount=summa, bank=bank)
                        driver.switch_to.window(gate_window)
                        buttons = elem.find_elements(By.TAG_NAME, 'button')
                        if status:
                            buttons[0].click()
                            modal = driver.find_element(By.CLASS_NAME, 'huZpmV')
                            input_receipt = modal.find_element(By.TAG_NAME, 'input')
                            input_receipt.send_keys(os.getcwd() + f"/receipt.png")
                            modal.find_element(By.TAG_NAME, 'button').click()
                        else:
                            buttons[1].click()
                            modal = driver.find_element(By.CLASS_NAME, 'huZpmV')
                            modal.find_element(By.CLASS_NAME, 'css-181d4wa-container').click()
                            modal.find_element(By.ID, 'react-select-5-option-7').click()
                            input_receipt = modal.find_element(By.TAG_NAME, 'input')
                            input_receipt.send_keys(os.getcwd() + f"/receipt.png")
                            modal.find_element(By.TAG_NAME, 'button').click()
                        try:
                            WebDriverWait(driver, 120).until(
                                EC.staleness_of(driver.find_element(By.CLASS_NAME, 'huZpmV')))
                        except Exception as e:
                            await client.send_message(bad_channel_id, 'Слишком долгая проверка')
                            sys.exit(0)
                    driver.refresh()
                    time.sleep(2)
        except Exception as e:
            with open('error.txt', 'a') as file:
                file.write(f'{e}\n')
            driver.switch_to.window(gate_window)
            driver.refresh()


asyncio.run(gate())
