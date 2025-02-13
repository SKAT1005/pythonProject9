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
config.read('gate.ini', encoding='utf-8')

username = config['arma']['username']
login_arma = config['arma']['login']
password_arma = config['arma']['password']

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
driver.execute_script("window.open('https://ibank.amra-bank.com/web_banking/protected/welcome.jsf');")
arma_window = driver.window_handles[1]


async def send_file(n=1):
    while True:
        if glob.glob("*.pdf"):
            break
        time.sleep(1)
    for file in glob.glob("*.pdf"):
        if n == 1:
            await client.send_file(good_channel_id, file, caption='✅Документ загружен удачно✅')
            return file
        else:
            await client.send_file(bad_channel_id, file, caption=f'❌{n}❌')
            return file


async def main_arma_sber(phone, amount):
    driver.switch_to.window(arma_window)
    driver.get('https://ibank.amra-bank.com/web_banking/protected/doc/payment/new/CATEGORY_EK_2/RCPT_EK_1822')
    WebDriverWait(driver, 50).until(EC.presence_of_element_located((By.NAME, 'AMOUNT'))).send_keys(amount)  # Ввод суммы
    phone_input = driver.find_element(By.ID, 'TABLE:0:record_masked')
    phone_input.clear()
    phone_input.send_keys(str(phone)[2:])  # Ввод телефона для отправки
    choose = driver.find_element(By.ID, 'dropdown_TABLE:1:enum1')
    choose.click()
    sber = choose.find_element(By.CLASS_NAME, 'select-list').find_elements(By.TAG_NAME, 'a')[1]
    sber.click()
    driver.find_element(By.CLASS_NAME, 'customCheckbox').click()  # Согласие с инфой

    WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID, 'j_id_5z_c1:nextBtn'))).click()  # Переход далее
    WebDriverWait(driver, 50).until(
        EC.presence_of_element_located((By.ID, 'buttonsComponent:sendBtn'))).click()
    time.sleep(2)
    driver.find_element(By.XPATH,
                        '/html/body/div[1]/div[1]/div[3]/div/div[1]/form/span/table/tbody/tr[1]').click()  # Переход в чек
    for file in glob.glob("*.pdf"):
        os.remove(file)
    try:
        driver.find_element(By.CLASS_NAME, 'statusRejected-img')
        n = driver.find_element(By.CLASS_NAME, 'statusRejected').text
        driver.find_element(By.XPATH,
                            '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
        await send_file(n)
        await client.send_message(bad_channel_id, f'❌{n}❌')
        sys.exit(0)
    except Exception as e:
        l = 1
        while True:
            if l == 60:
                await client.send_message(bad_channel_id, f'⏳Документ слишком долго загружался⏳')
                sys.exit(0)
            try:
                driver.find_element(By.CLASS_NAME, 'statusExecuted-img')
                driver.find_element(By.XPATH,
                                    '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
                file_name = await send_file()
                driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
                return file_name
            except Exception as e:
                time.sleep(10)
                l += 1
                driver.refresh()


async def activate_arma():
    driver.switch_to.window(arma_window)
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


async def activate_gates():
    driver.switch_to.window(gate_window)
    try:
        driver.find_element(By.CLASS_NAME, 'YQUVu')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        inputs[0].send_keys(login_gate)
        inputs[1].send_keys(password_gate)
        driver.find_element(By.CLASS_NAME, 'ewUpxh').click()
    except Exception:
        pass
    time.sleep(2)
    driver.get('https://panel.gate.cx/requests?page=1')


async def send_message(number, phone, summa, course):
    text = f'{phone}\n\n' \
           f'{summa}\n\n' \
           f'Номер сделки: {number}\n' \
           f'Курс: {course}\n' \
           f'{bot_text}'
    await client.send_message(good_channel_id, text)
    time.sleep(1)
    await client.send_message(good_channel_id, '+')


async def gate():
    await client.start(bot_token=bot_token)
    await activate_gates()
    await activate_arma()
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
                    driver.switch_to.window(arma_window)
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
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-dUHDFv'))).text
                        summa = int(WebDriverWait(cell[2], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-dUHDFv'))).text[:-2])
                        phone = WebDriverWait(cell[3], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-dUHDFv'))).text.replace(' ', '')
                        dollar = float(WebDriverWait(cell[4], 20).until(
                            EC.presence_of_element_located((By.CLASS_NAME, 'sc-dUHDFv'))).text[:-5])
                        cource = round(summa/dollar, 2)
                        history = open('history.txt', 'r').readlines()
                        if f'{number}\n' in history or number == last_number:
                            await client.send_message(bad_channel_id, 'Номер сделки повторился')
                            sys.exit(0)
                        else:
                            last_number = number
                            file = open('history.txt', 'a')
                            file.write(f'{number}\n')
                            file.close()
                        await send_message(number=number, course=cource, phone=phone, summa=summa)
                        receipt_name = await main_arma_sber(phone=phone, amount=summa)
                        driver.switch_to.window(gate_window)
                        buttons = elem.find_elements(By.TAG_NAME, 'button')
                        buttons[0].click()
                        modal = driver.find_element(By.CLASS_NAME, 'huZpmV')
                        input_receipt = modal.find_element(By.TAG_NAME, 'input')
                        input_receipt.send_keys(os.getcwd() + f"/{receipt_name}")
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
