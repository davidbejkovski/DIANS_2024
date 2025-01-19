import os
import pandas as pd
import requests
import csv
from datetime import datetime, date
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from app.models import StockData
from django.db import transaction
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Utility Functions
def setup_webdriver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run without UI
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def filter_link(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        body = soup.select('.col-md-12 a')
        links = [a['href'] for a in body if a.has_attr('href')]
        return links[0] if links else None
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
        return None

def get_last_date_csv(csv_file):
    directory = os.path.join('app', 'data')
    if not os.path.exists(directory):
        os.makedirs(directory)
    filename = os.path.join(directory, f'{csv_file}.csv')
    if os.path.exists(filename):
        df = pd.read_csv(filename)
        if not df.empty:
            df['Датум'] = pd.to_datetime(df['Датум'], errors='coerce')
            last_date = df['Датум'].max()
            if pd.notna(last_date):
                return last_date.strftime("%d.%m.%Y")
    return None


# Main Data Fetching Functions
def get_data(csv_file, url, start_date, end_date):
    driver = setup_webdriver()
    driver.get(url)
    data = []

    try:
        start_date_picker = driver.find_element(By.ID, 'FromDate')
        start_date_picker.clear()
        start_date_picker.send_keys(start_date)

        end_date_picker = driver.find_element(By.ID, 'ToDate')
        end_date_picker.clear()
        end_date_picker.send_keys(end_date)

        button = driver.find_element(By.CLASS_NAME, 'btn-primary-sm')
        driver.execute_script('arguments[0].scrollIntoView();', button)
        button.click()

        time.sleep(1)  # Adjust based on loading times
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        body = soup.select('tbody tr')

        for row in body:
            cols = row.find_all('td')
            if len(cols) >= 9:
                data.append({
                    "Датум": cols[0].text.strip(),
                    "Цена на последна трансакција": cols[1].text.strip(),
                    "Мак.": cols[2].text.strip(),
                    "Мин.": cols[3].text.strip(),
                    "Просечна цена": cols[4].text.strip(),
                    "%пром.": cols[5].text.strip(),
                    "Количина": cols[6].text.strip(),
                    "Промет во БЕСТ во денари": cols[7].text.strip() + ',00',
                    "Вкупен промет во денари": cols[8].text.strip() + ',00'
                })

    finally:
        driver.quit()

    return data

def process_firm(link, base_url):
    name = filter_link(base_url + link)
    if not name or '#' in name:
        logging.warning(f"Skipping invalid link: {name}")
        return

    parts = name.split('/')
    name = parts[4]
    data = []

    if get_last_date_csv(name) is None:
        start_date = datetime(2014, 1, 1).strftime('%Y-%m-%d')
        end_date = datetime(2014, 12, 31).strftime('%Y-%m-%d')
        data += get_data(name, base_url + filter_link(base_url + link), start_date, end_date)
    else:
        start_date = get_last_date_csv(name)
        year_start = start_date.split('.')
        today = str(date.today())
        year_end = today.split('-')
        end_year = int(year_end[0])
        start_year = int(year_start[2])

        for year in range(start_year, end_year + 1):
            if year == end_year:
                end_date = datetime(year, int(year_end[1]), int(year_end[2])).strftime('%Y-%m-%d')
            else:
                end_date = datetime(year, 12, 31).strftime('%Y-%m-%d')
            start_date = datetime(year, 1, 1).strftime('%Y-%m-%d')
            data += get_data(name, base_url + filter_link(base_url + link), start_date, end_date)

    # Save data to the database with transaction
    with transaction.atomic():
        for row in data:
            try:
                StockData.objects.create(
                    date=row['Датум'],
                    last_transaction_price=row['Цена на последна трансакција'],
                    min_price=row['Мин.'],
                    max_price=row['Мак.'],
                    avg_price=row['Просечна цена'],
                    promil=row['%пром.'],
                    quantity=row['Количина'],
                    best_turnover=row['Промет во БЕСТ во денари'],
                    total_turnover=row['Вкупен промет во денари'],
                    company_name=name  # If name is available, use it here
                )
                logging.info(f"Successfully saved data for {name} on {row['Датум']}")
            except Exception as e:
                logging.error(f"Error saving data for {name} on {row['Датум']}: {e}")

# Django Command
class Command(BaseCommand):
    help = "Scrape data from Macedonian Stock Exchange"

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data scrape...'))
        
        base_url = "https://www.mse.mk"
        url = f"{base_url}/mk/issuers/free-market"
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            body = soup.select("tbody tr a")
            links = [a['href'] for a in body if a.has_attr('href')]

            for link in links:
                self.stdout.write(self.style.SUCCESS(f'Processing firm: {link}'))
                process_firm(link, base_url)

            self.stdout.write(self.style.SUCCESS('Data scrape complete.'))
        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching MSE page: {e}"))
