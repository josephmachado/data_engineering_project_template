import csv
import os
from datetime import datetime, timedelta

import polars as pl
import requests
from cuallee import Check, CheckLevel

from airflow import DAG
from airflow.decorators import task
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator

with DAG(
    'coincap_elt',
    description='A simple DAG to fetch data \
    from CoinCap Exchanges API and write to a file',
    schedule_interval=timedelta(days=1),
    start_date=datetime(2023, 1, 1),
    catchup=False,
) as dag:

    url = "https://api.coincap.io/v2/exchanges"
    file_path = f'{os.getenv("AIRFLOW_HOME")}/data/coincap_exchanges.csv'

    @task
    def fetch_coincap_exchanges(url, file_path):
        response = requests.get(url)
        data = response.json()
        exchanges = data['data']
        if exchanges:
            keys = exchanges[0].keys()
            with open(file_path, 'w') as f:
                dict_writer = csv.DictWriter(f, fieldnames=keys)
                dict_writer.writeheader()
                dict_writer.writerows(exchanges)

    def check_completeness(pl_df, column_name):
        check = Check(CheckLevel.ERROR, "Completeness")
        validation_results_df = check.is_complete(column_name).validate(pl_df)
        return validation_results_df["status"].to_list()

    @task.branch
    def check_data_quality(validation_results):
        if "FAIL" not in validation_results:
            return ['generate_dashboard']
        return ['stop_pipeline']

    check_data_quality_instance = check_data_quality(
        check_completeness(pl.read_csv(file_path), "name")
    )

    stop_pipeline = DummyOperator(task_id='stop_pipeline')

    markdown_path = f'{os.getenv("AIRFLOW_HOME")}/visualization/'
    q_cmd = (
        f'cd {markdown_path} && quarto render {markdown_path}/dashboard.qmd'
    )
    gen_dashboard = BashOperator(
        task_id="generate_dashboard", bash_command=q_cmd
    )

    (
        fetch_coincap_exchanges(url, file_path)
        >> check_data_quality_instance
        >> gen_dashboard
    )
    check_data_quality_instance >> stop_pipeline
