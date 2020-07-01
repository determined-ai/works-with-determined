from datetime import timedelta
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.utils.dates import days_ago
from det_airflow.det_operators import clone_and_create_experiment, wait_for_experiment
from seldon_airflow.seldon_operators import seldon_deploy

default_args = {
    'owner': 'david',
    'depends_on_past': False,
    'start_date': days_ago(2),
    'email': ['david@determined.ai'],
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'params': {
        'git_repo': 'https://github.com/determined-ai/determined.git',
        'config': 'examples/official/trial/mnist_pytorch/const.yaml',
        'context': 'examples/official/trial/mnist_pytorch/',
        'det_master': 'DET_MASTER',
        'deploy_name': 'mnist_airflow_prod',
        'deploy_namespace': 'default',
        'deploy_image': 'davidhershey/seldon-mnist:1.3'
    },
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'det_train',
    default_args=default_args,
    description='Train a model with determined',
    schedule_interval=timedelta(days=1),
)

train = PythonOperator(
    python_callable=clone_and_create_experiment,
    task_id='train',
    dag=dag,
    provide_context=True,
)

wait = PythonOperator(
    python_callable=wait_for_experiment,
    provide_context=True,
    task_id='wait',
    dag=dag,
)

deploy = PythonOperator(
    python_callable=seldon_deploy,
    provide_context=True,
    task_id='deploy',
    dag=dag,
)



train >> wait >> deploy
