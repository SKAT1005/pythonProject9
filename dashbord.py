import asyncio
import configparser
import glob
import io
import os
import telebot
import time

from PIL import Image
from selenium.webdriver import ActionChains
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait


config = configparser.ConfigParser()
config.read('dashbord.ini', encoding='utf-8')

api_id = int(config['telegram']['api_id'])
api_hash = config['telegram']['api_hash']
channel_id = int(config['telegram']['channel_id'])
bot_token = config['telegram']['bot_token']


gate_data = config['gate']['data'].split(',')
sleep_time = int(config['gate']['sleep_time'])
username = config['gate']['username']

last_message_id = [0]

options = Options()
options.add_argument('--allow-profiles-outside-user-dir')
options.add_argument('--enable-profile-shortcut-manager')
options.add_argument(fr'user-data-dir=C:\Users\{username}\AppData\Local\Google\Chrome\User Data\12')
driver = webdriver.Chrome(options=options)
driver.get('https://panel.gate.cx')

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


async def gate(login, password):
    try:
        driver.find_element(By.CLASS_NAME, 'YQUVu')
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        inputs[0].send_keys(login)
        inputs[1].send_keys(password)
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
    driver.find_element(By.CLASS_NAME, 'logout-button').click()
async def main():
    client = telebot.TeleBot(bot_token)
    for i in gate_data:
        login, password, name = i.split()
        await gate(login=login, password=password)
        client.send_photo(channel_id, open('122.png', 'rb'), caption=name)
        os.remove('122.png')
        time.sleep(sleep_time)
    client.send_message(channel_id, '==============')


while True:
    asyncio.run(main())
