import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from datetime import datetime


def Filter2(url):
    request = requests.get(url)
    text = request.text
    soup = BeautifulSoup(text, 'html.parser')
    body = soup.select('.col-md-12 a')
    links = [a['href'] for a in body if a.has_attr('href')]
    return links[0]


def get_last_date_csv(csv_file):
    filename = f'{csv_file}.csv'
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        if not df.empty:
            df['Датум'] = pd.to_datetime(df['Датум'], errors='coerce')
            last_date = df['Датум'].max()
            if pd.notna(last_date):
                return last_date.strftime("%d.%m.%Y")
    else:
        columns = ['Датум', 'Цена на последна трансакција', 'Мак.', 'Мин.', 'Просечна цена', '%пром.', 'Количина',
                   'Промет во БЕСТ во денари', 'Вкупен промет во денари']
        df = pd.DataFrame(columns=columns)
        df.to_csv(filename, index=False)
    return None


def get_data(csv_file, url, start_date, end_date):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)
    driver.get(url)
    data = []
    start_date_picker = driver.find_element(By.ID, 'FromDate')
    start_date_picker.clear()
    start_date_picker.send_keys(start_date)
    end_date_picker = driver.find_element(By.ID, 'ToDate')
    end_date_picker.clear()
    end_date_picker.send_keys(end_date)
    button = driver.find_element(By.CLASS_NAME, 'btn-primary-sm')
    driver.execute_script('arguments[0].scrollIntoView();', button)
    button.click()
    time.sleep(1)
    request = driver.page_source
    soup = BeautifulSoup(request, 'html.parser')
    body = soup.select('tbody tr')
    for b in body:
        cols = b.find_all('td')
        if len(cols) >= 9:
            data.append({
                "Датум": cols[0].text.strip(),
                "Цена на последна трансакција": cols[1].text.strip(),
                "Мак.": cols[2].text.strip(),
                "Мин.": cols[3].text.strip(),
                "Просечна цена": cols[4].text.strip(),
                "%пром.": cols[5].text.strip(),
                "Количина": cols[6].text.strip(),
                "Промет во БЕСТ во денари": cols[7].text.strip(),
                "Вкупен промет во денари": cols[8].text.strip(),
            })
    driver.quit()
    return data
