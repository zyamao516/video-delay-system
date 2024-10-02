import numpy as np
import cv2
import time
import threading
import curses

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
    def __init__(self, delay: float, frame_rate: float, camera_index: int):
        self.delay = delay
        self.frame_refresh_period = 1.0 / frame_rate
        self.last_update_time = time.perf_counter()
        self.frame_node = None
        self.camera_index = camera_index

    def set_delay(self, delay: float):
        self.delay = delay

    def set_frame_rate(self, frame_rate: float):
        self.frame_refresh_period = 1.0 / frame_rate

    def set_camera_index(self, camera_index: int):
        self.camera_index = camera_index

def terminate(captures, terminate_event):
    terminate_event.set()
    for capture in captures:
        if capture.isOpened():
            capture.release()
    cv2.destroyAllWindows()
    curses.endwin()
    exit()

def get_webcam_index():
    available_cameras = []
    for camera_index in range(10):
        cap = cv2.VideoCapture(camera_index)
        if cap.isOpened():
            available_cameras.append(camera_index)
            cap.release()
        else:
            print("\033[A\033[2K\033[A\033[2K",end="")

    return available_cameras

def capture_frames(displays, frame_buffer, frame_interval, terminate_event, captures):
    while not terminate_event.is_set():
        start_time = time.perf_counter()
        
        for display in displays:
            if display.camera_index is not None:
                capture = captures[display.camera_index]
                ret, frame = capture.read()
                if not ret:
                    print(f'Error: Unable to read frame from camera {display.camera_index}')
                    terminate(captures, terminate_event)

                now = time.perf_counter()
                frame_buffer.add_to_tail(frame, now)

        sleep_time = frame_interval - (time.perf_counter() - start_time)
        if sleep_time > 0:
            time.sleep(sleep_time)

        while (time.perf_counter() - start_time) < frame_interval:
            pass

def display_frames(frame_buffer, displays, terminate_event):
    screenshot_counter = 0
    while not terminate_event.is_set() and displays:
        now = time.perf_counter()

        for display in displays:
            if now - display.last_update_time >= display.frame_refresh_period:
                while display.frame_node and display.frame_node.time_stamp + display.delay < now:
                    if display.frame_node.next_node is not None:
                        display.frame_node = display.frame_node.next_node
                    else:
                        break
                if display.frame_node:
                    cv2.imshow(f'Display {display.delay}s delay (Camera {display.camera_index})', display.frame_node.value)
                    display.last_update_time = now

        while frame_buffer.head_node and frame_buffer.head_node != displays[-1].frame_node:
            frame_buffer.remove_head()

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            terminate_event.set()
            break
        elif key == ord('s'):
            combined_image = None
            for display in displays:
                if combined_image is None:
                    combined_image = display.frame_node.value
                else:
                    combined_image = np.hstack((combined_image, display.frame_node.value))
            screenshot_counter += 1
            screenshot_name = f'combined_screenshot_{screenshot_counter}.png'
            cv2.imwrite(screenshot_name, combined_image)
            print(f'Combined screenshot saved as {screenshot_name}')
        elif key == ord('t'):
            time_diffs = []
            with open('display_time_differences.txt', 'w') as f:
                for display in displays:
                    time_diffs.append(now - display.frame_node.time_stamp if display.frame_node else 0)
                f.write(f'{time_diffs}\n')
            print('Display time differences saved to display_time_differences.txt')

def menu(stdscr, displays, terminate_event, captures):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    current_display = 0
    while not terminate_event.is_set():
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(0, 0, "Display Configuration Menu", curses.A_BOLD)
        stdscr.attroff(curses.color_pair(4))

        for idx, display in enumerate(displays):
            if idx == current_display:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx * 2 + 2, 0, f"Display {idx + 1} - Delay: {display.delay}s, Frame Rate: {1.0 / display.frame_refresh_period:.2f}fps, Camera: {display.camera_index}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(idx * 2 + 2, 0, f"Display {idx + 1} - Delay: {display.delay}s, Frame Rate: {1.0 / display.frame_refresh_period:.2f}fps, Camera: {display.camera_index}")
                stdscr.attroff(curses.color_pair(3))

        if current_display == len(displays):
            stdscr.attron(curses.color_pair(1))
        else:
            stdscr.attron(curses.color_pair(5))
        stdscr.addstr(len(displays) * 2 + 2, 0, "Add Display")
        stdscr.attroff(curses.color_pair(5))

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(height - 2, 0, "Use TAB to navigate, SHIFT+TAB to go back, ENTER to modify/add, Q to quit.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()

        if key == ord('\t'):
            current_display = (current_display + 1) % (len(displays) + 1)
        elif key == curses.KEY_BTAB:
            current_display = (current_display - 1) % (len(displays) + 1)
        elif key == ord('\n'):
            if current_display == len(displays):
                add_display(stdscr, displays, captures)
            else:
                modify_display(stdscr, displays[current_display], terminate_event, captures)
        elif key == ord('q'):
            terminate_event.set()

def add_display(stdscr, displays, captures):
    curses.curs_set(1)
    curses.echo()
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter delay for new display (seconds): ", curses.color_pair(3))
    stdscr.refresh()

    try:
        delay = float(stdscr.getstr(1, 0).decode('utf-8'))
        if delay < 0:
            raise ValueError("Delay must be a non-negative value.")
        stdscr.addstr(2, 0, "Enter frame rate for new display (fps): ", curses.color_pair(3))
        stdscr.refresh()
        frame_rate = float(stdscr.getstr(3, 0).decode('utf-8'))
        camera_index = curses.wrapper(camera_selection_menu, captures)
        max_camera_fps = 30  # Replace with actual camera FPS if needed
        if frame_rate <= 0 or frame_rate > max_camera_fps:
            raise ValueError(f"Frame rate must be a positive value and not exceed {max_camera_fps} fps.")
        new_display = CaptureDisplay(delay, frame_rate, camera_index)
        new_display.frame_node = displays[0].frame_node if displays else None
        displays.append(new_display)
    except ValueError as e:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(6, 0, f"Invalid input: {e}. Press any key to continue.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.getch()

    curses.noecho()
    curses.curs_set(0)

def modify_display(stdscr, display, terminate_event, captures):
    curses.curs_set(1)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    options = ["Delay", "Frame Rate", "Camera", "Remove Display"]
    current_option = 0

    while not terminate_event.is_set():
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(0, 0, f"Modifying Display - Delay: {display.delay}s, Frame Rate: {1.0 / display.frame_refresh_period:.2f}fps, Camera: {display.camera_index}", curses.A_BOLD)
        stdscr.attroff(curses.color_pair(4))

        for idx, option in enumerate(options):
            if idx == current_option:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(2 + idx * 2, 0, f"{option}: ", curses.A_BOLD)
                if option == "Delay":
                    stdscr.addstr(2 + idx * 2, 12, f"{display.delay}s")
                elif option == "Frame Rate":
                    stdscr.addstr(2 + idx * 2, 12, f"{1.0 / display.frame_refresh_period:.2f}fps")
                elif option == "Camera":
                    stdscr.addstr(2 + idx * 2, 12, f"{display.camera_index}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(2 + idx * 2, 0, f"{option}: ")
                if option == "Delay":
                    stdscr.addstr(2 + idx * 2, 12, f"{display.delay}s")
                elif option == "Frame Rate":
                    stdscr.addstr(2 + idx * 2, 12, f"{1.0 / display.frame_refresh_period:.2f}fps")
                elif option == "Camera":
                    stdscr.addstr(2 + idx * 2, 12, f"{display.camera_index}")
                stdscr.attroff(curses.color_pair(3))

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(height - 2, 0, "Use TAB to navigate, ENTER to edit/remove, ESC to go back.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()

        if key == ord('\t'):
            current_option = (current_option + 1) % len(options)
        elif key == curses.KEY_BTAB or key == curses.KEY_UP:
            current_option = (current_option - 1) % len(options)
        elif key == ord('\n'):
            if options[current_option] == "Delay":
                edit_delay(stdscr, display)
            elif options[current_option] == "Frame Rate":
                edit_frame_rate(stdscr, display)
            elif options[current_option] == "Camera":
                edit_camera(stdscr, display, captures)
            elif options[current_option] == "Remove Display":
                remove_display(stdscr, displays, display)
                break
        elif key == 27:  # ESC key
            break

    curses.curs_set(0)

def edit_delay(stdscr, display):
    curses.curs_set(1)
    curses.echo()
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new delay (seconds): ", curses.color_pair(3))
    stdscr.refresh()

    try:
        delay = float(stdscr.getstr(1, 0).decode('utf-8'))
        if delay < 0:
            raise ValueError("Delay must be a non-negative value.")
        cv2.destroyWindow(f'Display {display.delay}s delay (Camera {display.camera_index})')
        display.set_delay(delay)
    except ValueError as e:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(2, 0, f"Invalid input: {e}. Press any key to continue.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.getch()

    curses.noecho()
    curses.curs_set(0)

def edit_frame_rate(stdscr, display):
    curses.curs_set(1)
    curses.echo()
    stdscr.clear()
    stdscr.addstr(0, 0, "Enter new frame rate (fps): ", curses.color_pair(3))
    stdscr.refresh()

    try:
        frame_rate = float(stdscr.getstr(1, 0).decode('utf-8'))
        max_camera_fps = 30  # Replace with actual camera FPS if needed
        if frame_rate <= 0 or frame_rate > max_camera_fps:
            raise ValueError(f"Frame rate must be a positive value and not exceed {max_camera_fps} fps.")
        display.set_frame_rate(frame_rate)
    except ValueError as e:
        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(2, 0, f"Invalid input: {e}. Press any key to continue.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.getch()

    curses.noecho()
    curses.curs_set(0)

def edit_camera(stdscr, display, captures):
    camera_index = curses.wrapper(camera_selection_menu, captures)
    display.set_camera_index(camera_index)

def remove_display(stdscr, displays, display):
    displays.remove(display)
    cv2.destroyWindow(f'Display {display.delay}s delay (Camera {display.camera_index})')

def camera_selection_menu(stdscr, captures):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    current_camera = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(0, 0, "Camera Selection Menu", curses.A_BOLD)
        stdscr.attroff(curses.color_pair(4))

        for idx, camera in enumerate(captures):
            if idx == current_camera:
                stdscr.attron(curses.color_pair(1))
                stdscr.addstr(idx * 2 + 2, 0, f"Camera {idx}")
                stdscr.attroff(curses.color_pair(1))
            else:
                stdscr.attron(curses.color_pair(3))
                stdscr.addstr(idx * 2 + 2, 0, f"Camera {idx}")
                stdscr.attroff(curses.color_pair(3))

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(height - 2, 0, "Use UP/DOWN arrows to navigate, ENTER to select.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_DOWN:
            current_camera = (current_camera + 1) % len(captures)
        elif key == curses.KEY_UP:
            current_camera = (current_camera - 1) % len(captures)
        elif key == ord('\n'):
            return current_camera

def capture_selection_menu(stdscr, available_cameras):
    selected_captures = []
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(4, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(5, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    current_position = 0

    while True:
        stdscr.clear()
        height, width = stdscr.getmaxyx()

        stdscr.attron(curses.color_pair(4))
        stdscr.addstr(0, 0, "Camera Capture Selection Menu", curses.A_BOLD)
        stdscr.attroff(curses.color_pair(4))

        for idx, camera in enumerate(available_cameras):
            if camera in selected_captures:
                stdscr.attron(curses.color_pair(4))
            elif idx == current_position:
                stdscr.attron(curses.color_pair(1))
            else:
                stdscr.attron(curses.color_pair(3))
            stdscr.addstr(idx * 2 + 2, 0, f"Camera {camera}")
            stdscr.attroff(curses.color_pair(4) if camera in selected_captures else curses.color_pair(1) if idx == current_position else curses.color_pair(3))

        stdscr.attron(curses.color_pair(1) if current_position == len(available_cameras) else curses.color_pair(5))
        stdscr.addstr(len(available_cameras) * 2 + 2, 0, "Finished")
        stdscr.attroff(curses.color_pair(1) if current_position == len(available_cameras) else curses.color_pair(5))

        stdscr.attron(curses.color_pair(2))
        stdscr.addstr(height - 2, 0, "Use UP/DOWN arrows to navigate, ENTER to select/deselect, TAB to finish.")
        stdscr.attroff(curses.color_pair(2))
        stdscr.refresh()

        key = stdscr.getch()

        if key == curses.KEY_DOWN:
            current_position = (current_position + 1) % (len(available_cameras) + 1)
        elif key == curses.KEY_UP:
            current_position = (current_position - 1) % (len(available_cameras) + 1)
        elif key == ord('\n'):
            if current_position == len(available_cameras):
                return selected_captures
            elif available_cameras[current_position] in selected_captures:
                selected_captures.remove(available_cameras[current_position])
            else:
                selected_captures.append(available_cameras[current_position])

if __name__ == "__main__":
    available_cameras = get_webcam_index()
    if not available_cameras:
        print("Camera not detected, terminating")
        terminate([], threading.Event())

    selected_captures = curses.wrapper(capture_selection_menu, available_cameras)
    captures = [cv2.VideoCapture(idx) for idx in selected_captures]

    displays = []  # Start with no active displays
    frame_interval = 1.0 / 30

    frame_buffer = DoublyLinkedList()

    terminate_event = threading.Event()

    capture_thread = threading.Thread(target=capture_frames, args=(displays, frame_buffer, frame_interval, terminate_event, captures))
    capture_thread.start()

    menu_thread = threading.Thread(target=curses.wrapper, args=(menu, displays, terminate_event, captures))
    menu_thread.start()

    display_frames(frame_buffer, displays, terminate_event)

    capture_thread.join()
    menu_thread.join()
    terminate(captures, terminate_event)

