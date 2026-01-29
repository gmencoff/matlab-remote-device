#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include <thread>
#include <queue>
#include <mutex>
#include <atomic>
#include <chrono>
#include <string>
#include <random>

namespace py = pybind11;

struct Command {
    std::string id;
    double ts;
    std::string name;
    int value;
    std::string type;
};

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
            std::mt19937 rng{std::random_device{}()};
            std::uniform_int_distribution<int> dist(100, 1000);
            int counter = 0;

            while (running_) {
                std::this_thread::sleep_for(std::chrono::seconds(5));

                Command cmd;
                cmd.id = "cmd_" + std::to_string(counter++);
                cmd.ts = now();
                cmd.name = "rx_buffer_size";
                cmd.value = dist(rng);
                cmd.type = "property";

                enqueue(cmd);
            }
        });
    }

    void stop() {
        if (!running_) return;
        running_ = false;
        if (worker_.joinable())
            worker_.join();
    }

    void enqueue(const Command& cmd) {
        std::lock_guard<std::mutex> lock(mu_);
        queue_.push(cmd);
    }

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
        d["name"] = cmd.name;
        d["value"] = cmd.value;
        d["type"] = cmd.type;
        return d;
    }

private:
    double now() const {
        using clock = std::chrono::system_clock;
        return std::chrono::duration<double>(
            clock::now().time_since_epoch()
        ).count();
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
        .def("poll", &CommandQueue::poll);
}
