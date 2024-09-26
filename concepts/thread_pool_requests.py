import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests

def send_batch(batch_id, data_chunk, url):
    """
    Sends a batch of data to the server.

    Args:
        batch_id (int): Identifier for the batch.
        data_chunk (list): The subset of data to send.
        url (str): The server endpoint URL.
    """
    try:
        # Send a POST request with the data chunk as JSON
        response = requests.post(url, json={'batch_id': batch_id, 'data': data_chunk})
        response.raise_for_status()
        print(f"Batch {batch_id} sent successfully with status code {response.status_code}.")
    except requests.exceptions.RequestException as e:
        print(f"Error sending batch {batch_id}: {e}")

def main():
    # Sample data to send
    total_data = [{'id': i, 'value': f'data_{i}'} for i in range(1, 1001)]  # 1000 items

    # Define batch size
    batch_size = 100

    # Split data into batches
    data_batches = [
        total_data[i:i + batch_size]
        for i in range(0, len(total_data), batch_size)
    ]

    # Server URL to send data to
    url = 'http://example.com/api/upload'  # Replace with your server URL

    # Create a thread pool executor
    max_workers = 5  # Number of threads in the pool
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Dictionary to hold future to batch mapping
        future_to_batch = {
            executor.submit(send_batch, idx, batch, url): idx
            for idx, batch in enumerate(data_batches, start=1)
        }

        # Process completed futures
        for future in as_completed(future_to_batch):
            batch_id = future_to_batch[future]
            try:
                future.result()
            except Exception as exc:
                print(f"Batch {batch_id} generated an exception: {exc}")

if __name__ == '__main__':
    main()
