#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <thread>
#include <queue>
#include <mutex>
#include <condition_variable>
#include <atomic>
#include <chrono>
#include <string>

namespace py = pybind11;

class CommandQueue {
public:
    CommandQueue() : running_(false) {}

    ~CommandQueue() {
        stop();
    }

    void start() {
        if (running_) return;
        running_ = true;

        worker_ = std::thread([this]() {
            int counter = 0;
            while (running_) {
                std::this_thread::sleep_for(std::chrono::seconds(5));
                enqueue("command_" + std::to_string(counter++));
            }
        });
    }

    void stop() {
        if (!running_) return;
        running_ = false;
        if (worker_.joinable())
            worker_.join();
    }

    // Called by C++ producer
    void enqueue(const std::string& cmd) {
        std::lock_guard<std::mutex> lock(mu_);
        queue_.push(cmd);
    }

    // Called by Python
    py::object poll() {
        std::lock_guard<std::mutex> lock(mu_);
        if (queue_.empty()) {
            return py::none();
        }
        auto cmd = queue_.front();
        queue_.pop();
        return py::str(cmd);
    }

private:
    std::queue<std::string> queue_;
    std::mutex mu_;
    std::atomic<bool> running_;
    std::thread worker_;
};

PYBIND11_MODULE(cppbridge, m) {
    py::class_<CommandQueue>(m, "CommandQueue")
        .def(py::init<>())
        .def("start", &CommandQueue::start)
        .def("stop", &CommandQueue::stop)
        .def("poll", &CommandQueue::poll);
}
