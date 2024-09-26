from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import time

def send_write_request(batch_data):
    # Simulate writing batch data to the database
    db_write(batch_data)

def batch_data_generator(data_source, batch_size):
    batch = []
    for data in data_source:
        batch.append(data)
        if len(batch) == batch_size:
            yield batch
            batch = []
    if batch:
        yield batch

def main():
    data_source = data_stream()  # Assume this is a generator yielding data items
    batch_size = 100
    max_workers = 5  # Number of threads in the pool

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for batch in batch_data_generator(data_source, batch_size):
            future = executor.submit(send_write_request, batch)
            futures.append(future)

        # Optionally, wait for all batches to complete
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Batch failed with exception: {e}")

if __name__ == "__main__":
    main()
