import numpy as np
import cv2
import time
import threading

class Node:
    def __init__(self, value, time_stamp=0, next_node=None, prev_node=None):
        self.value = value
        self.time_stamp = time_stamp
        self.next_node = next_node
        self.prev_node = prev_node

class DoublyLinkedList:
    def __init__(self):
        self.head_node = None
        self.tail_node = None
        self.lock = threading.Lock()

    def add_to_tail(self, new_value, time):
        new_tail = Node(new_value, time)
        with self.lock:
            if self.tail_node is None:
                self.head_node = new_tail
                self.tail_node = new_tail
            else:
                self.tail_node.next_node = new_tail
                new_tail.prev_node = self.tail_node
                self.tail_node = new_tail

    def remove_head(self):
        with self.lock:
            if self.head_node is None:
                return None
            removed_head = self.head_node
            self.head_node = self.head_node.next_node
            if self.head_node is not None:
                self.head_node.prev_node = None
            if removed_head == self.tail_node:
                self.tail_node = None
            return removed_head

class CaptureDisplay:
    def __init__(self, delay: float, frame_refresh_period: float, frame_node: Node):
        self.delay = delay
        self.frame_refresh_period = frame_refresh_period
        self.frame_node = frame_node
        self.total_delay = delay + frame_refresh_period

def terminate(capture):
    if capture.isOpened():
        capture.release()
        cv2.destroyAllWindows()
    exit()

def get_webcam_index():
    for camera_index in range(10):
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            print(f'Camera index available: {camera_index}')
            cap.release()
            return camera_index
    print("Camera not detected, terminating")
    terminate(None)

def capture_frames(capture, frame_buffer, frame_interval):
    while True:
        start_time = time.perf_counter()
        
        ret, frame = capture.read()
        if not ret:
            print('Error: Unable to read frame')
            terminate(capture)

        now = time.perf_counter()
        frame_buffer.add_to_tail(frame, now)

        # Sleep for most of the interval
        sleep_time = frame_interval - (time.perf_counter() - start_time)
        if sleep_time > 0:
            time.sleep(sleep_time)

        # Busy-wait for the remaining time to fine-tune precision
        while (time.perf_counter() - start_time) < frame_interval:
            pass

def display_frames(frame_buffer, delays):
    screenshot_counter = 0
    last_display_time = time.perf_counter()
    while True:
        start = time.perf_counter()
        now = time.perf_counter()
        combined_image = None
        for display in delays:
            if now - display.frame_node.time_stamp >= display.frame_refresh_period:
                if combined_image is None:
                    combined_image = display.frame_node.value
                else:
                    combined_image = np.hstack((combined_image, display.frame_node.value))
                cv2.imshow(str(display.delay), display.frame_node.value)
                while display.frame_node.time_stamp + display.total_delay < now:
                    if display.frame_node.next_node is not None:
                        display.frame_node = display.frame_node.next_node
                    else:
                        break

        while frame_buffer.head_node and frame_buffer.head_node != delays[-1].frame_node:
            frame_buffer.remove_head()

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            terminate(capture)
            break
        elif key == ord('s'):
            screenshot_counter += 1
            screenshot_name = f'combined_screenshot_{screenshot_counter}.png'
            cv2.imwrite(screenshot_name, combined_image)
            print(f'Combined screenshot saved as {screenshot_name}')
        elif key == ord('t'):
            time_diffs = []
            
            with open('display_time_differences.txt', 'w') as f:
                for diff in delays:
                    time_diffs.append(now-diff.frame_node.time_stamp)
                f.write(f'{time_diffs}\n')
            print('Display time differences saved to display_time_differences.txt')
        
        end = time.perf_counter()
        #print(1 / (end - start))

if __name__ == "__main__":
    capture = cv2.VideoCapture(get_webcam_index())
    frame_rate = 1000.0  # 1000 fps
    frame_interval = 1.0 / frame_rate  # 1 ms

    defined_delays = [0.0, 0.5, 1.0]  # Example delays in seconds
    frame_buffer = DoublyLinkedList()
    ret, frame = capture.read()
    if not ret:
        print('Error: Unable to read initial frame')
        terminate(capture)

    frame_buffer.add_to_tail(frame, time.perf_counter())
    delays = []

    camera_frame_duration = 1 / capture.get(cv2.CAP_PROP_FPS)

    for delay in defined_delays:
        delays.append(CaptureDisplay(delay, camera_frame_duration, frame_buffer.head_node))

    capture_thread = threading.Thread(target=capture_frames, args=(capture, frame_buffer, frame_interval))
    capture_thread.start()

    display_frames(frame_buffer, delays)

    capture_thread.join()
    terminate(capture)

