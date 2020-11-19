import csv
import random

NUM_STORES = 3000
NUM_DAYS = 10000

with open('train-xl.csv', 'w', newline='') as train_csv_file:
    with open('val-xl.csv', 'w', newline='') as val_csv_file:
        train_csv_writer = csv.writer(train_csv_file, quoting=csv.QUOTE_MINIMAL)
        val_csv_writer = csv.writer(val_csv_file, quoting=csv.QUOTE_MINIMAL)
        header_row = ['store_id', 'day_index', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x10', 'sales']
        train_csv_writer.writerow(header_row)
        val_csv_writer.writerow(header_row)
        for store_id in range(NUM_STORES):
            for day_index in range(10000):
                sales = 10000 * random.random()
                row = [store_id, day_index]
                for daily_feature in range(10):
                    row.append(random.randrange(1000))
                row.append(sales)
                if random.random() < 0.1:
                    val_csv_writer.writerow(row)
                else:
                    train_csv_writer.writerow(row)

with open('store.csv', 'w', newline='') as store_csv_file:
    store_csv_writer = csv.writer(store_csv_file, quoting=csv.QUOTE_MINIMAL)
    header_row = ['store_id', 'store_x1', 'store_x2', 'store_x3', 'store_x4', 'store_x5', 'store_x6', 'store_x7', 'store_x8', 'store_x9', 'store_x10']
    store_csv_writer.writerow(header_row)
    for store_id in range(NUM_STORES):
        row = [store_id]
        for daily_feature in range(10):
            row.append(random.randrange(1000))
        store_csv_writer.writerow(row)
