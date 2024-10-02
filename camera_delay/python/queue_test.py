import multiprocessing as mp
import time

def producer(queue, n, encode_times):
    for i in range(n):
        start = time.perf_counter()
        queue.put(i)
        end = time.perf_counter()
        encode_times.append(end - start)
    queue.put(None)  # Signal the consumer to exit
    print("Producer finished")

def consumer(queue, decode_times):
    while True:
        start = time.perf_counter()
        item = queue.get()
        end = time.perf_counter()
        decode_times.append(end - start)
        if item is None:
            break
    print("Consumer finished")

if __name__ == "__main__":
    num_items = 1000  # Reduced number of items for debugging
    manager = mp.Manager()
    queue = mp.Queue()
    encode_times = manager.list()  # Shared list to store encode times
    decode_times = manager.list()  # Shared list to store decode times

    print("Starting producer process")
    producer_process = mp.Process(target=producer, args=(queue, num_items, encode_times))
    producer_process.start()

    print("Starting consumer process")
    consumer_process = mp.Process(target=consumer, args=(queue, decode_times))
    consumer_process.start()

    # Wait for both processes to finish
    producer_process.join()
    print("Producer process finished")
    
    consumer_process.join()
    print("Consumer process finished")

    # Calculate and display average encode and decode times
    average_encode_time = sum(encode_times) / len(encode_times)
    average_decode_time = sum(decode_times) / len(decode_times)
    print(f"Average time to encode (put) to the queue: {average_encode_time:.6f} seconds")
    print(f"Average time to decode (get) from the queue: {average_decode_time:.6f} seconds")

