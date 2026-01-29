#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <thread>
#include <queue>
#include <mutex>
#include <atomic>
#include <chrono>
#include <string>
#include <random>
#include <iostream>

namespace py = pybind11;

struct Command {
    std::string id;
    double ts;          // seconds since epoch
    std::string type;   // "property"
    std::string name;   // "rx_buffer_size"
    int value;          // 100..1000
};

class CommandQueue {
public:
    CommandQueue() : running_(false) {}

    ~CommandQueue() {
        stop();
    }

    // Starts a background thread that enqueues one command every 5 seconds.
    void start() {
        if (running_) return;
        running_ = true;

        worker_ = std::thread([this]() {
            std::mt19937 rng{std::random_device{}()};
            std::uniform_int_distribution<int> dist(100, 1000);
            int counter = 0;

            while (running_) {
                std::this_thread::sleep_for(std::chrono::seconds(5));

                Command cmd;
                cmd.id = "cmd_" + std::to_string(counter++);
                cmd.ts = now_seconds();
                cmd.type = "property";
                cmd.name = "rx_buffer_size";
                cmd.value = dist(rng);

                enqueue_(cmd);
            }
        });
    }

    // Stops the background thread (if running).
    void stop() {
        if (!running_) return;
        running_ = false;

        if (worker_.joinable()) {
            worker_.join();
        }
    }

    // Polls one command from the queue.
    // Returns a Python dict if available; otherwise returns None.
    py::object poll() {
        std::lock_guard<std::mutex> lock(mu_);
        if (queue_.empty()) {
            return py::none();
        }

        Command cmd = queue_.front();
        queue_.pop();

        py::dict d;
        d["id"] = cmd.id;
        d["ts"] = cmd.ts;
        d["type"] = cmd.type;
        d["name"] = cmd.name;
        d["value"] = cmd.value;
        return d;
    }

    // Called by Python after processing a command.
    // ack is expected to be:
    // {
    //   "deviceId": "string",
    //   "commandId": "string",
    //   "response": dict
    // }
    void acknowledge(py::dict ack) {
        std::string deviceId = py::str(ack["deviceId"]);
        std::string commandId = py::str(ack["commandId"]);
        py::dict response = py::cast<py::dict>(ack["response"]);

        std::cout << "[ACK]\n";
        std::cout << "  deviceId: " << deviceId << "\n";
        std::cout << "  commandId: " << commandId << "\n";
        std::cout << "  response:\n";

        for (auto item : response) {
            std::string key = py::str(item.first);
            std::string val = py::str(item.second);
            std::cout << "    " << key << ": " << val << "\n";
        }

        std::cout << std::flush;
    }

private:
    static double now_seconds() {
        using clock = std::chrono::system_clock;
        return std::chrono::duration<double>(
            clock::now().time_since_epoch()
        ).count();
    }

    void enqueue_(const Command& cmd) {
        std::lock_guard<std::mutex> lock(mu_);
        queue_.push(cmd);
    }

    std::queue<Command> queue_;
    std::mutex mu_;
    std::atomic<bool> running_;
    std::thread worker_;
};

PYBIND11_MODULE(cppbridge, m) {
    py::class_<CommandQueue>(m, "CommandQueue")
        .def(py::init<>())
        .def("start", &CommandQueue::start)
        .def("stop", &CommandQueue::stop)
        .def("poll", &CommandQueue::poll)
        .def("acknowledge", &CommandQueue::acknowledge);
}
