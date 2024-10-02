import numpy as np
import cv2
import time

class Node:
    def __init__(self, value, time_stamp=0, next_node=None, prev_node=None):
        self.value = value
        self.time_stamp = time_stamp
        self.next_node = next_node
        self.prev_node = prev_node

    def set_next_node(self, next_node):
        self.next_node = next_node

    def get_next_node(self):
        return self.next_node

    def set_prev_node(self, prev_node):
        self.prev_node = prev_node

    def get_prev_node(self):
        return self.prev_node

    def get_value(self):
        return self.value

class DoublyLinkedList:
    def __init__(self):
        self.head_node = None
        self.tail_node = None

    def get_head(self):
        return self.head_node

    def get_tail(self):
        return self.tail_node

    def add_to_head(self, new_value, time):
        new_head = Node(new_value, time)
        current_head = self.head_node

        if current_head is not None:
            current_head.set_prev_node(new_head)
            new_head.set_next_node(current_head)

        self.head_node = new_head

        if self.tail_node is None:
            self.tail_node = new_head

    def add_to_tail(self, new_value, time):
        new_tail = Node(new_value, time)
        current_tail = self.tail_node

        if current_tail is not None:
            current_tail.set_next_node(new_tail)
            new_tail.set_prev_node(current_tail)

        self.tail_node = new_tail

        if self.head_node is None:
            self.head_node = new_tail

    def remove_head(self):
        removed_head = self.head_node

        if removed_head is None:
            return None

        self.head_node = removed_head.get_next_node()

        if self.head_node is not None:
            self.head_node.set_prev_node(None)

        if removed_head == self.tail_node:
            self.remove_tail()

        return removed_head.get_value()

    def remove_tail(self):
        removed_tail = self.tail_node

        if removed_tail is None:
            return None

        self.tail_node = removed_tail.get_prev_node()

        if self.tail_node is not None:
            self.tail_node.set_next_node(None)

        if removed_tail == self.head_node:
            self.remove_head()

        return removed_tail.get_value()

    def remove_by_value(self, value_to_remove):
        node_to_remove = None
        current_node = self.head_node

        while current_node is not None:
            if current_node.get_value() == value_to_remove:
                node_to_remove = current_node
                break
            current_node = current_node.get_next_node()

        if node_to_remove is None:
            return None

        if node_to_remove == self.head_node:
            self.remove_head()
        elif node_to_remove == self.tail_node:
            self.remove_tail()
        else:
            next_node = node_to_remove.get_next_node()
            prev_node = node_to_remove.get_prev_node()
            next_node.set_prev_node(prev_node)
            prev_node.set_next_node(next_node)

        return node_to_remove

class CaptureDisplay:
    def __init__(self, delay: float, frame_refresh_period: float, frame_node: Node):
        self.delay = delay
        self.frame_refresh_period = frame_refresh_period
        self.frame_node = frame_node
        self.total_delay = delay + frame_refresh_period

    def __str__(self):
        return f"Display with {self.delay} seconds of delay"

def terminate(capture):
    if capture.isOpened():
        capture.release()
        cv2.destroyAllWindows()
    exit()

def get_webcam_index():
    available_camera_index = []
    camera_is_available = False
    for camera_index in range(10):
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            camera_is_available = True
            print(f'Camera index available: {camera_index}')
            available_camera_index.append(camera_index)
            cap.release()
        else:
            print("\033[A\033[2K\033[A\033[2K", end="")

    if not camera_is_available:
        print("Camera not detected, terminating")
        terminate(None)

    print("Enter index to continue or q to quit")

    while True:
        input_index = input("Enter index: ")
        if input_index == 'q':
            terminate(None)
        try:
            index = int(input_index)
            if index not in available_camera_index:
                print("Wrong index, try again")
            else:
                return index
        except ValueError:
            print("Invalid input type, try again")

def main_loop(base_frame_rate: float, capture, frame_buffer, delays, camera_frame_duration):
    frame_duration = 1.0 / base_frame_rate
    last_camera_frame_time = start_time = next_frame_time = time.perf_counter()

    while True:
        ret, frame = capture.read()
        if not ret:
            print('Error: Unable to read frame')
            terminate(capture)
        
        # update frame buffer when new frame is recorded by camera
        now = time.perf_counter()
        if frame_buffer.head_node is None or now - last_camera_frame_time >= camera_frame_duration:      #not np.array_equal(frame, frame_buffer.head_node.get_value())
            frame_buffer.add_to_tail(frame, time.perf_counter())
            last_camera_frame_time = now

        for display in delays:
            if now - display.frame_node.time_stamp < display.frame_refresh_period:
                continue

            cv2.imshow(str(display.delay), display.frame_node.get_value())

            while display.frame_node.time_stamp + display.total_delay < now:
                if display.frame_node.get_next_node() is not None:
                    display.frame_node = display.frame_node.get_next_node()
                break
        
        while(frame_buffer.head_node != delays[len(delays)-1].frame_node):
            frame_buffer.remove_head()
        
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        next_frame_time += frame_duration
        time_to_sleep = next_frame_time - time.perf_counter()

        if time_to_sleep > 0:
            time.sleep(time_to_sleep)
        else:
            next_frame_time = time.perf_counter()

if __name__ == "__main__":
    capture = cv2.VideoCapture(get_webcam_index())
    frame_rate = float(input("Enter the desired frame rate (fps): "))

    defined_delays = [0.0, 2]
    frame_buffer = DoublyLinkedList()

    ret, frame = capture.read()
    if not ret:
        print('Error: Unable to read initial frame')
        terminate(capture)

    frame_buffer.add_to_head(frame, time.perf_counter())
    delays = []

    camera_frame_duration = 1 / capture.get(cv2.CAP_PROP_FPS)

    for delay in defined_delays:
        delays.append(CaptureDisplay(delay, camera_frame_duration, frame_buffer.get_head()))

    main_loop(frame_rate, capture, frame_buffer, delays, camera_frame_duration)
    terminate(capture)

