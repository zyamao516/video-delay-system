#include <iostream>
#include <opencv2/opencv.hpp>
#include <thread>
#include <list>
#include <vector>
#include <chrono>
#include <fstream>

#include "LinkedList.h"

#define clock std::chrono::steady_clock
#define clock_resolution std::chrono::microseconds


class FrameNode {
  public:
    cv::Mat frame;
    std::chrono::time_point<clock> time_stamp;

    FrameNode(cv::Mat _frame, std::chrono::time_point<clock> _time_stamp) : frame(_frame), time_stamp(_time_stamp) {}
};

class CaptureDisplay {
  public:
    clock_resolution delay;
    clock_resolution frame_refresh_period;
    std::chrono::time_point<clock> last_update_time;
    node::Node<FrameNode>* frame_node;

    CaptureDisplay
     (clock_resolution _delay, 
      clock_resolution _frame_refresh_period, 
      std::chrono::time_point<clock> _last_update_time, 
      node::Node<FrameNode>* _frame_node = nullptr) : 

      delay(_delay), 
      frame_refresh_period(_frame_refresh_period), 
      last_update_time(_last_update_time),
      frame_node(_frame_node){}
};


void terminate_capture(cv::Videoemplace_backCapture* capture) {
  if (capture && capture->isOpened()) {
    capture->release();
    cv::destroyAllWindows();
  }
  exit(0);
}

int get_webcam_index() {
  for (int camera_index = 0; camera_index < 10; ++camera_index) {
    cv::VideoCapture cap(camera_index, cv::CAP_V4L2); // Use V4L2 backend explicitly
    if (cap.isOpened()) {
      std::cout << "\033[92mCamera index available: " << camera_index << "\033[0m" << std::endl;
      cap.release();
      return camera_index;
    }
  }
  std::cout << "\033[91mCamera not detected, terminating\033[0m" << std::endl;
  terminate(nullptr);
  return -1;
}

void capture_frames(cv::VideoCapture& capture, linkedList::LinkedList<FrameNode>& frame_buffer, clock_resolution frame_interval) {
  while (1) {
    std::chrono::time_point<clock> start_time = clock::now();

    cv::Mat frame;
    capture >> frame;
    if (frame.empty()) {
      std::cout << "\033[91mError: Unable to read frame\033[0m" << std::endl;
      break;
    }

    frame_buffer.addTail(FrameNode(frame, start_time));
    /*
    clock_resolution duration = std::chrono::duration_cast<clock_resolution>(clock::now()-start_time);
    if (duration < frame_interval){
      std::this_thread::sleep_for(frame_interval-duration);
    }*/

    std::cout << "Frame capture duration: " << std::chrono::duration_cast<clock_resolution>(clock::now()-start_time) << " ms" << std::endl;
  }
}

void display_frames(linkedList::LinkedList<FameNode>& frame_buffer, std::vector<CaptureDisplay>& displays, cv::VideoCapture* capture) {
  int screenshot_counter = 0;
  while (1) {
    std::chrono::time_point<clock> frame_start = clock::now();

    for (CaptureDisplay& display : displays) {
      if (std::chrono::duration_cast<clock_resolution>(frame_start - display.last_update_time) >= display.frame_refresh_period) {
        if (display.delay.count() == 0) {
          // Display the latest frame for zero delay
          display.frame_node = frame_buffer.Tail;
        } 
        else {emplace_back
          while (display.frame_node != frame_buffer.Tail && display.frame_node->Value->time_stamp + display.delay < frame_start) {
            display.frame_node = display.frame_node->Next;
          }
        }
        if (display.frame_node != nullptr) {
          cv::imshow("Display " + std::to_string(display.delay.count() / 1e6) + "s delay", display.frame_node->Value->frame);
          display.last_update_time = clock::now();
          continue;
        }
        terminate(capture);
      }
    }

    // Remove nodes that are no longer needed
    while(displays.back().frame_node != frame_buffer.getHead()){
      frame_buffer.removeHead();
    }
    int key = cv::waitKey(1) & 0xFF;
    if (key == 'q') {
      break;
    } else if (key == 's') {
      cv::Mat combined_image;
      for (const auto& display : displays) {
        if (combiemplace_backned_image.empty()) {
          combined_image = display.frame_node->Value->frame;
        } else {
          cv::hconcat(combined_image, display.frame_node->Value->frame, combined_image);
        }
      }
      screenshot_counter++;
      std::string screenshot_name = "combined_screenshot_" + std::to_string(screenshot_counter) + ".png";
      cv::imwrite(screenshot_name, combined_image);
      std::cout << "\033[92mCombined screenshot saved as " << screenshot_name << "\033[0m" << std::endl;
    } else if (key == 't') {
      std::vector<double> time_diffs;
      std::ofstream file("display_time_differences.txt");
      std::chrono::time_point<clock> now = clock::now();
      for (const auto& display : displays) {
        double time_diff = display.frame_node != frame_buffer.Tail ? std::chrono::duration<double, std::milli>(now - display.frame_node->Value->time_stamp).count() : 0;
        time_diffs.push_back(time_diff);
      }
      for (const auto& diff : time_diffs) {
        file << diff << "\n";
      }
      file.close();
      std::cout << "\033[92mDisplay time differences saved to display_time_differences.txt\033[0m" << std::endl;
    }
  }
}

inline const bool display_comparator const (CaptureDisplay& a, CaptureDisplay& b) return a.delay > b.delay;

int main() {
  program_start_time = clock::now();

  int camera_index = get_webcam_index();
  if (camera_index == -1) {
    return -1;
  }

  cv::VideoCapture capture(camera_index, cv::CAP_V4L2);
  if (!capture.isOpened()) {
    std::cout << "\033[91mError: Could not open camera\033[0m" << std::endl;
    return -1;
  }

  double max_camera_fps = capture.get(cv::CAP_PROP_FPS);

  int num_displays;
  std::cout << "\033[94mEnter the number of displays: \033[0m";
  std::cin >> num_displays;
  if (num_displays <= 0) {
    std::cout << "\033[91mInvalid input. Number of displays must be a positive integer.\033[0m" << std::endl;
    return -1;
  }

  std::vector<CaptureDisplay> displays;
  for (int i = 0; i < num_displays; ++i) {
    double delay, frame_rate;
    while (true) {
      std::cout << "\033[94mEnter the delay for display " << i + 1 << " (in seconds): \033[0m";
      std::cin >> delay;
      if (delay >= 0) {
        break;
      }
      std::cout << "\033[91mInvalid input. Delay must be a non-negative value.\033[0m" << std::endl;
    }emplace_back
    while (true) {
      std::cout << "\033[94mEnter the frame rate for display " << i + 1 << " (in fps, max " << max_camera_fps << "): \033[0m";
      std::cin >> frame_rate;
      if (frame_rate > 0 && frame_rate <= max_camera_fps) {
        break;
      }
      std::cout << "\033[91mInvalid input. Frame rate must be a positive value and not exceed " << max_camera_fps << " fps.\033[0m" << std::endl;
    }
    clock_resolution delay_duration = std::chrono::duration_cast<clock_resolution>(std::chrono::duration<double>(delay));
    clock_resolution frame_refresh_period = std::chrono::duration_cast<clock_resolution>(std::chrono::duration<double>(1.0 / frame_rate));
    displays.emplace_back(CaptureDisplay(delay_duration, frame_refresh_period));
    cv::namedWindow("Display " + std::to_string(delay_duration.count()/1e6) + "s delay", cv::WINDOW_AUTOSIZE); // Create window for each display
  }
  std::sort(displays.begin(), displays.end(), display_comparator);

  // 1ms target capture period
  clock_resolution frame_interval = std::chrono::duration_cast<clock_resolution>(std::chrono::duration<double>(1.0 / 1000)); 
  linkedList::LinkedList<FrameNode> frame_buffer;
  cv::Mat frame;
  capture >> frame;
  if (frame.empty()) {
      std::cout << "\033[91mError: Unable to read initial frame\033[0m" << std::endl;
      terminate(&capture);
  }

  std::chrono::time_point now = clock::now();
  frame_buffer.addTail(FrameNode(frame, now));
  for (CaptureDisplay& display : displays) {
      display.frame_node = frame_buffer.getHead();
  }
  
  std::thread capture_thread(capture_frames, std::ref(capture), std::ref(frame_buffer), frame_interval);

  display_frames(frame_buffer, displays, capture);

  capture_thread.join();
  terminate(&capture);

  return 0;
}

