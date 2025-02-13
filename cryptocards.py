import asyncio
import configparser
import datetime
import glob
import io
import os
import threading
import time

from selenium.common import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import telethon
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
username = config['bank']['username']
# session_number = config['google']['session_number']

login_cryptocards = config['cryptocards']['login']
password_cryptocards = config['cryptocards']['password']
min_cryptocards = config['cryptocards']['min']
max_cryptocards = config['cryptocards']['max']
system_cryptocards = config['cryptocards']['system']
type_cryptocards = config['cryptocards']['type']
sleep_time = int(config['cryptocards']['wait_time'])

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id_2 = int(config['telegram']['channel_id_2'])
bot_token = config['telegram']['bot_token']
client = telethon.TelegramClient(None, api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")

options = Options()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')
driver = webdriver.Chrome(options=options)
driver.get('https://cryptocards.ws')
try:
    login = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/form/div[1]/input')
    login.clear()
    login.send_keys(login_cryptocards)
    password = driver.find_element(By.XPATH, '/html/body/div[1]/div/div[1]/form/div[2]/input')
    password.clear()
    password.send_keys(password_cryptocards)
    enter_button = driver.find_element(By.CLASS_NAME, 'button')
    enter_button.click()
    try:
        capcha = WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/form/div[3]/input'))
        )
        code = input('Введите 2FA код: ')
        capcha.send_keys(code)
        enter_button.click()
    except Exception:
        pass
except Exception:
    pass


WebDriverWait(driver, 2).until(
            EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div/div[1]/div[2]/a[2]'))
        ).click()
filter = WebDriverWait(driver, 50).until(
    EC.presence_of_element_located((By.CLASS_NAME, 'transfersFilter')))
elems = filter.find_elements(By.TAG_NAME, 'input')
system = elems[0]
min = elems[1]
max = elems[2]

types = filter.find_elements(By.CLASS_NAME, 'item')
card = types[0]
sbp = types[1]
account = types[2]

time.sleep(1)
if len(card.get_attribute('class')) > 6:
    card.click()
if len(sbp.get_attribute('class')) > 6:
    sbp.click()
if len(account.get_attribute('class')) > 6:
    account.click()

time.sleep(1)
if 'карта' in type_cryptocards:
    card.click()
if 'сбп' in type_cryptocards:
    sbp.click()
if 'счет' in type_cryptocards:
    account.click()

time.sleep(1)
system.clear()
system.send_keys(system_cryptocards)
min.clear()
min.send_keys(min_cryptocards)
max.clear()
max.send_keys(max_cryptocards)
driver.refresh()


async def send_message(number, phone, summa, course):
    text = f'{phone}\n\n' \
           f'{summa}\n\n' \
           f'Номер сделки: {number}\n' \
           f'Курс: {course}'
    await client.send_message(channel_id_2, text)
    time.sleep(1)
    await client.send_message(channel_id_2, '+')


async def analyse(lst, number, min_course, page):
    elems = lst.find_elements(By.TAG_NAME, 'tr')[1:]
    print(len(elems))
    for elem in elems:
        try:
            n = elem.find_elements(By.TAG_NAME, 'td')
            prise_in_rub = int(n[3].text)
            prise_in_usdt = float(n[4].text)
            l = n[6].text.split('\n')[0][2:]
            profit_in_usdt = float(l)
            course = prise_in_rub / (prise_in_usdt + profit_in_usdt)
            if course < min_course:
                min_course = course
                number = n[0].text.split()[-1]
                page = driver.find_element(By.CLASS_NAME, 'cur').text
        except Exception as e:
            print(132, e)
    return number, min_course, page

async def go_to_page(page):
    page_button = WebDriverWait(driver, 60).until(
        EC.presence_of_element_located((By.CLASS_NAME, 'cur'))
    )
    if page_button.text == page:
        return True
    else:
        page_button.click()
        window = driver.find_element(By.CLASS_NAME, 'inner')
        input = window.find_element(By.TAG_NAME, 'input')
        input.clear()
        input.send_keys(page)
        window.find_element(By.CLASS_NAME, 'yes').click()


async def find_accept(lst, number):
    n = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CLASS_NAME, 'defaultTableWrapper')))
    elems = WebDriverWait(n, 120).until(EC.presence_of_all_elements_located((By.TAG_NAME, 'tr')))[1:]
    for elem in elems:
        try:
            n = elem.find_element(By.TAG_NAME, 'td')
            find_number = n.text.split()[-1]
            if find_number == number:
                return n.find_element(By.CLASS_NAME, 'accept')
        except Exception as e:
            print(e)
            pass
    return None
async def main():
    await client.start(bot_token=bot_token)
    while True:
        time.sleep(2)
        number = None
        page = 1
        min_course = 1000000000

        lst = WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.CLASS_NAME, 'defaultTableWrapper')))
        pagination = driver.find_element(By.CLASS_NAME, 'pagination')
        try:
            while True:
                number, min_course, page = await analyse(lst, number, min_course, page)
                next_page = pagination.find_element(By.CLASS_NAME, 'next')
                pag_class = next_page.get_attribute('class')
                if 'disabled' in pag_class:
                    break
                next_page.click()
                time.sleep(1)
        except Exception as e:
            print(e)
        print(number, min_course, page)
        if number:
            try:
                await go_to_page(page)
                driver.refresh()
                accept = await find_accept(lst, number)
                overlay = driver.find_element(By.CSS_SELECTOR,
                                              "a.item[href='/devices']")  # Селектор перекрывающего элемента
                driver.execute_script("arguments[0].remove();", overlay)
                accept.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'yes'))).click()
                time.sleep(2)
                transfer = driver.find_elements(By.CLASS_NAME,
                                                'transfer')[-1]
                transfer.find_element(By.CLASS_NAME, 'select ').click()
                transfer.find_element(By.CLASS_NAME, 'select__option').click()
                inputs = transfer.find_elements(By.CLASS_NAME, 'input')
                phone = inputs[1].find_element(By.TAG_NAME, 'input').get_attribute('value').replace('-', '').replace(
                    '(', '').replace(')', '').replace(' ', '')
                summa = inputs[2].find_element(By.TAG_NAME, 'input').get_attribute('value').replace(' ', '')
                receipt_name = ''
                """Отправка чека"""
                receipt = transfer.find_element(By.CLASS_NAME, 'receipt')
                input_receipt = receipt.find_element(By.TAG_NAME, 'input')
                input_receipt.send_keys(os.getcwd() + f"/{receipt_name}")
                if transfer.find_element(By.CLASS_NAME, 'id').text == number:
                    await send_message(number=number, course=round(min_course, 2), phone=phone, summa=summa)
                else:
                    await client.send_message(channel_id_2, '❌❌❌')
            except Exception as e:
                print(213, e)
        time.sleep(sleep_time)
        driver.refresh()
        time.sleep(2)
        await go_to_page('1')


asyncio.run(main())
