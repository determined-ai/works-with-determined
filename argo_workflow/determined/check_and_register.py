import argparse
import logging
import subprocess
import re

from determined.experimental import Determined

logging.basicConfig(level=logging.INFO)


def get_validation_metric(checkpoint):
    metrics = checkpoint.validation['metrics']
    config = checkpoint.experiment_config
    searcher = config['searcher']
    smaller_is_better = bool(searcher['smaller_is_better'])
    metric_name = searcher['metric']
    if 'validation_metrics' in metrics:
        metric = metrics['validation_metrics'][metric_name]
    else:
        metric = metrics['validationMetrics'][metric_name]
    return (metric, smaller_is_better)


def main():
    parser = argparse.ArgumentParser(description='Run Determined Example')
    parser.add_argument('experiment_id', type=str, help='path to context directory')
    parser.add_argument('model_name', type=str, help='path to context directory')
    args = parser.parse_args()

    checkpoint = Determined().get_experiment(args.experiment_id).top_checkpoint()
    metric, smaller_is_better = get_validation_metric(checkpoint)

    models = Determined().get_models(name=args.model_name)
    model = None
    for m in models:
        if m.name == args.model_name:
            model = m
            break
    if not model:
        print(f'Registering new Model: {args.model_name}')
        model = Determined().create_model(args.model_name)
        model.register_version(checkpoint.uuid)
        better = True
    else:
        latest_version = model.get_version()
        if latest_version is None:
            print(f'Registering new version: {args.model_name}')
            model.register_version(checkpoint.uuid)
            better = True
        else:
            old_metric, _ = get_validation_metric(latest_version)
            if smaller_is_better:
                if metric < old_metric:
                    print(f'Registering new version: {args.model_name}')
                    model.register_version(checkpoint.uuid)
                    better = True
                else:
                    better = False
            else:
                if metric > old_metric:
                    print(f'Registering new version: {args.model_name}')
                    model.register_version(checkpoint.uuid)
                    better = True
                else:
                    better = False

    if not better:
        print('Previous model version was better, logging...')
    # Write experiment id to output file
    with open('/tmp/decision.txt', 'w') as f:
        if better:
            f.write('yes')
        else:
            f.write('no')

if __name__ == '__main__':
    main()
