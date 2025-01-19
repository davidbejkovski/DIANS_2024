from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
import os
import csv
from datetime import datetime

# Render the 'index.html' page
def index(request):
    return render(request, 'index.html')

# Render the 'main.html' page
def main(request):
    return render(request, 'main.html')

# Handle the request for fetching and processing CSV data
def run_gege(request):
    if request.method == 'POST':
        company = request.POST.get('company')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')

        # Convert start_date and end_date to datetime objects
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid date format.'})

        # List all CSV files in the app/data folder
        csv_folder_path = 'app/data/'
        csv_files = [f for f in os.listdir(csv_folder_path) if f.endswith('.csv')]

        data = []

        # Read data from all CSV files and filter based on company and date range
        for file_name in csv_files:
            csv_file_path = os.path.join(csv_folder_path, file_name)

            with open(csv_file_path, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                for row in csv_reader:
                    try:
                        row_date = datetime.strptime(row['Датум'], '%Y-%m-%d')  # Assuming 'Датум' is in 'YYYY-MM-DD' format
                    except ValueError:
                        continue  # Skip invalid date formats

                    if row['Друштво'] == company and start_date <= row_date <= end_date:
                        data.append(row)

        if not data:
            return JsonResponse({'status': 'error', 'message': 'No data found for the selected filters.'})

        # Calculate moving averages and oscillators for each period type
        moving_averages_daily = calculate_moving_averages(data, 'daily')
        moving_averages_monthly = calculate_moving_averages(data, 'monthly')
        moving_averages_weekly = calculate_moving_averages(data, 'weekly')

        oscillators_daily = calculate_oscillators(data, 'daily')
        oscillators_monthly = calculate_oscillators(data, 'monthly')
        oscillators_weekly = calculate_oscillators(data, 'weekly')

        # Render the results in the HTML table
        return render(request, 'main.html', {
            'data': data,
            'moving_averages_daily': moving_averages_daily,
            'moving_averages_monthly': moving_averages_monthly,
            'moving_averages_weekly': moving_averages_weekly,
            'oscillators_daily': oscillators_daily,
            'oscillators_monthly': oscillators_monthly,
            'oscillators_weekly': oscillators_weekly,
        })
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

# Calculate moving averages for different periods
def calculate_moving_averages(data, period_type):
    if period_type == 'daily':
        return [{"date": row['Датум'], "daily_avg": row['Просечна цена']} for row in data]
    elif period_type == 'weekly':
        return [{"date": row['Датум'], "weekly_avg": row['Просечна цена']} for row in data]
    elif period_type == 'monthly':
        return [{"date": row['Датум'], "monthly_avg": row['Просечна цена']} for row in data]
    return []

# Calculate oscillators for different periods
def calculate_oscillators(data, period_type):
    if period_type == 'daily':
        return [{"date": row['Датум'], "daily_oscillator": row['%пром.']} for row in data]
    elif period_type == 'weekly':
        return [{"date": row['Датум'], "weekly_oscillator": row['%пром.']} for row in data]
    elif period_type == 'monthly':
        return [{"date": row['Датум'], "monthly_oscillator": row['%пром.']} for row in data]
    return []

# Display CSV data as a downloadable file
def display_csv(request):
    company = request.GET.get('company')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return JsonResponse({'status': 'error', 'message': 'Invalid date format.'})

    # Load CSV data
    csv_folder_path = 'app/data/'
    csv_files = [f for f in os.listdir(csv_folder_path) if f.endswith('.csv')]

    data = []
    for file_name in csv_files:
        csv_file_path = os.path.join(csv_folder_path, file_name)
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                try:
                    row_date = datetime.strptime(row['Датум'], '%Y-%m-%d')
                except ValueError:
                    continue

                if row['Друштво'] == company and start_date <= row_date <= end_date:
                    data.append(row)

    if not data:
        return JsonResponse({'status': 'error', 'message': 'No data found for the selected filters.'})

    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filtered_data.csv"'

    writer = csv.writer(response)
    writer.writerow(['Date', 'Company', 'Last Price', 'Min', 'Max', 'Avg Price', 'Promil', 'Quantity', 'Best Turnover', 'Total Turnover'])

    for row in data:
        writer.writerow([
            row['Датум'], row['Друштво'], row['Цена на последна трансакција'], row['Мин.'], row['Мак.'],
            row['Просечна цена'], row['%пром.'], row['Количина'], row['Промет во БЕСТ во денари'], row['Вкупен промет во денари']
        ])

    return response
