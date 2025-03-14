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
from selenium.webdriver.support.wait import WebDriverWait

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

username = config['bank']['username']
login_arma = config['bank']['login']
password_arma = config['bank']['password']
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
good_channel_id = int(config['telegram']['good_channel_id'])
bad_channel_id = int(config['telegram']['bad_channel_id'])
bot_token = config['telegram']['bot_token']
client = telethon.TelegramClient(None, api_id, api_hash,
                                 system_version="4.16.30-vxCUSTOM")

options = Options()
pref = {'download.default_directory': os.getcwd()}
options.add_experimental_option('prefs', pref)
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\11')
driver = webdriver.Chrome(options=options)
driver.get('https://cryptocards.ws')

cryptocards_window = driver.window_handles[0]
driver.execute_script("window.open('https://ibank.amra-bank.com/web_banking/protected/welcome.jsf');")
arma_window = driver.window_handles[1]
last_phone = ''

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


async def main_arma(phone, amount):
    global last_phone
    driver.switch_to.window(arma_window)
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
    element = WebDriverWait(driver, 100).until(
        EC.presence_of_element_located((By.ID, 'buttonsComponent:sendBtn'))
    )
    if phone in last_phone:
        time.sleep(90)
    element.click()  # Отправление оплаты
    time.sleep(10)
    driver.refresh()
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
        return None
    except Exception:
        l = 1
        while True:
            if l == 10:
                await client.send_message(bad_channel_id, f'⏳Документ слишком долго загружался⏳')
                return None
            try:
                driver.find_element(By.CLASS_NAME, 'statusExecuted-img')
                driver.find_element(By.XPATH,
                                    '/html/body/div[1]/div[1]/div[3]/div/div[1]/form[2]/span[2]/input[2]').click()  # скачивание чека
                file_name = await send_file()
                driver.find_element(By.XPATH, '/html/body/div[1]/div[1]/div[2]/a[1]').click()
                return file_name
            except Exception:
                time.sleep(6)
                l += 1
                driver.refresh()


async def activate_arma():
    driver.switch_to.window(arma_window)
    try:
        n = driver.find_element(By.CLASS_NAME, "loginForm-input")
        if n.get_attribute("value"):
            pass
        else:
            n.send_keys(login_arma)
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


async def activate_cryptocards():
    await client.send_message(good_channel_id, 'Начинаю обработку платежа')
    driver.switch_to.window(cryptocards_window)
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
    await client.send_message(good_channel_id, text)
    time.sleep(1)
    await client.send_message(good_channel_id, '+')


async def analyse(lst, number, min_course, page):
    elems = lst.find_elements(By.TAG_NAME, 'tr')[1:]
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
            print(261, e)
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


async def find_accept(number):
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


async def cryptocards():
    await client.start(bot_token=bot_token)
    await activate_cryptocards()
    await activate_arma()
    driver.switch_to.window(cryptocards_window)
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
            print(318, e)
        if number:
            try:
                await go_to_page(page)
                driver.refresh()
                accept = await find_accept(number)
                overlay = driver.find_element(By.CSS_SELECTOR,
                                              "a.item[href='/devices']")  # Селектор перекрывающего элемента
                driver.execute_script("arguments[0].remove();", overlay)
                accept.click()
                WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'yes'))).click()
                time.sleep(5)
                transfer = driver.find_elements(By.CLASS_NAME,
                                                'transfer')[-1]
                transfer.find_element(By.CLASS_NAME, 'select ').click()
                WebDriverWait(transfer, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'select__option'))).click()
                inputs = transfer.find_elements(By.CLASS_NAME, 'input')
                phone = inputs[1].find_element(By.TAG_NAME, 'input').get_attribute('value').replace('-', '').replace(
                    '(', '').replace(')', '').replace(' ', '')
                summa = inputs[2].find_element(By.TAG_NAME, 'input').get_attribute('value').replace(' ', '')
                """Отправка чека"""
                if transfer.find_element(By.CLASS_NAME, 'id').text == number:
                    await send_message(number=number, course=round(min_course, 2), phone=phone, summa=summa)
                    receipt_name = await main_arma(phone=phone, amount=summa)
                    driver.switch_to.window(cryptocards_window)
                    if receipt_name:
                        receipt = transfer.find_element(By.CLASS_NAME, 'receipt')
                        input_receipt = receipt.find_element(By.TAG_NAME, 'input')
                        input_receipt.send_keys(os.getcwd() + f"/{receipt_name}")
                    else:
                        await client.send_message(bad_channel_id,
                                                  'Мы слишком долго ждали файл, или файл с ошибкой. Программа завершает совю работу')
                        sys.exit(0)
                else:
                    await client.send_message(good_channel_id, '❌❌❌')
            except Exception as e:
                print(355, e)
        time.sleep(sleep_time)
        driver.refresh()
        time.sleep(2)
        await go_to_page('1')


asyncio.run(cryptocards())
