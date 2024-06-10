from airflow import DAG
from datetime import datetime, timedelta
from airflow.decorators import task
import requests
import os
import csv


with DAG(
    'coincap_el',
    description='A simple DAG to fetch data from CoinCap Exchanges API and write to a file',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:

    @task
    def fetch_coincap_exchanges():
        url = "https://api.coincap.io/v2/exchanges"
        response = requests.get(url)
        data = response.json()

        exchanges = data['data']
        if exchanges:
            keys = exchanges[0].keys()
            with open(f'{os.getenv("AIRFLOW_HOME")}/dags/files/coincap_exchanges.csv', 'w') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(exchanges)

    fetch_coincap_exchanges()


