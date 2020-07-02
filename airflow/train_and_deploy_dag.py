from datetime import timedelta
from airflow import DAG
from airflow.models import Variable
from airflow.operators.python_operator import PythonOperator, BranchPythonOperator
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
    'retries': 0,
    'params': {
        'git_repo': 'https://github.com/determined-ai/determined.git',
        'config': 'examples/official/trial/mnist_pytorch/const.yaml',
        'context': 'examples/official/trial/mnist_pytorch/',
        'det_master': 'DET_MASTER',
        'deploy_name': 'mnist-airflow-prod',
        'deploy_namespace': 'default',
        'deploy_image': 'davidhershey/seldon-mnist:1.3'
    },
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'train_and_deploy_mnist',
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


def make_deploy_decision(**kwargs):
    variable_name = kwargs['params']['deploy_name'] + '-best-metric'
    task_instance = kwargs['task_instance']
    experiment_id = task_instance.xcom_pull(task_ids='train')
    best_metric = task_instance.xcom_pull(task_ids='wait')
    last_best = Variable.get(variable_name, default_var=None)
    if last_best is None or best_metric < float(last_best):
        Variable.set(variable_name, best_metric)
        return 'deploy'
    else:
        return 'failure'


decision = BranchPythonOperator(
        task_id='branching',
        python_callable=make_deploy_decision,
        provide_context=True,
        dag=dag
)


def print_failure(**kwargs):
    det_master = kwargs['params']['det_master']
    task_instance = kwargs['task_instance']
    best_metric = task_instance.xcom_pull(task_ids='wait')
    last_best = Variable.get('mnist_best_eval', default_var=None)
    message = f"Validation metric ({best_metric}) was less than previous best: {last_best}"
    print(message)
    return message


failure = PythonOperator(
    python_callable=print_failure,
    provide_context=True,
    task_id='failure',
    dag=dag,
)

deploy = PythonOperator(
    python_callable=seldon_deploy,
    provide_context=True,
    task_id='deploy',
    dag=dag,
)

train >> wait >> decision
decision >> [deploy, failure]
