import multiprocessing as mp
import time

class Node:
    def __init__(self, value, time_stamp=0, next_node=None, prev_node=None):
        self.value = value
        self.time_stamp = time_stamp
        self.next_node = next_node
        self.prev_node = prev_node

class SharedDoublyLinkedList:
    def __init__(self, manager):
        self.head_node = manager.list([None])
        self.tail_node = manager.list([None])
        self.count = manager.Value('i', 0)
        self.lock = manager.Lock()

    def add_to_tail(self, new_value, time_stamp):
        new_tail = Node(new_value, time_stamp)
        with self.lock:
            if self.tail_node[0] is None:
                self.head_node[0] = new_tail
                self.tail_node[0] = new_tail
            else:
                self.tail_node[0].next_node = new_tail
                new_tail.prev_node = self.tail_node[0]
                self.tail_node[0] = new_tail
            self.count.value += 1
        print(f"Added to tail: {new_value}, count: {self.count.value}")

    def remove_head(self):
        with self.lock:
            if self.head_node[0] is None:
                return None
            removed_head = self.head_node[0]
            self.head_node[0] = self.head_node[0].next_node
            if self.head_node[0] is not None:
                self.head_node[0].prev_node = None
            if removed_head == self.tail_node[0]:
                self.tail_node[0] = None
            self.count.value -= 1
            print(f"Removed head: {removed_head.value if removed_head else 'None'}, count: {self.count.value}")
            return removed_head

    def get_count(self):
        return self.count.value

def producer(shared_list, n):
    for i in range(n):
        shared_list.add_to_tail(i, time.time())
        time.sleep(0.01)  # Simulate some delay
    # Add sentinel value to signal the consumer to exit
    shared_list.add_to_tail(None, time.time())
    print("Producer finished")

def consumer(shared_list):
    while True:
        node = shared_list.remove_head()
        if node is None:
            time.sleep(0.01)  # Wait a bit before trying again
            continue
        if node.value is None:
            break
        print(f"Consumed: {node.value}")
    print("Consumer finished")

if __name__ == "__main__":
    num_items = 10  # Reduced number of items for debugging
    manager = mp.Manager()
    shared_list = SharedDoublyLinkedList(manager)

    print("Starting producer process")
    producer_process = mp.Process(target=producer, args=(shared_list, num_items))
    producer_process.start()

    print("Starting consumer process")
    consumer_process = mp.Process(target=consumer, args=(shared_list,))
    consumer_process.start()

    # Wait for both processes to finish
    producer_process.join()
    print("Producer process finished")
    
    consumer_process.join()
    print("Consumer process finished")

