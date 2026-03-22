#include "device_simulator.h"

#include <chrono>
#include <ctime>
#include <iomanip>
#include <sstream>
#include <utility>

#include "../sensors/current_sensor.h"
#include "../sensors/temperature_sensor.h"
#include "../sensors/vibration_sensor.h"

namespace smarttool {

DeviceSimulator::DeviceSimulator(std::string device_id, MqttPublisher publisher)
    : device_id_(std::move(device_id)), publisher_(std::move(publisher)), tick_(0) {}

void DeviceSimulator::bootstrap_default_sensors() {
    // Register the default demo sensors shown in the project presentation.
    sensors_.emplace_back(new TemperatureSensor());
    sensors_.emplace_back(new VibrationSensor());
    sensors_.emplace_back(new CurrentSensor());
}

TelemetryMessage DeviceSimulator::sample() {
    // Pull one reading from each sensor and package the result as one
    // timestamped telemetry message.
    TelemetryMessage message;
    message.device_id = device_id_;
    message.tick = tick_;
    message.timestamp = make_timestamp();

    for (const auto& sensor : sensors_) {
        message.metrics[sensor->name()] = sensor->sample(tick_);
    }

    ++tick_;
    return message;
}

void DeviceSimulator::publish_once() {
    // Run the full edge-side cycle once: sample sensors, serialize, publish.
    const TelemetryMessage message = sample();
    publisher_.publish(message.to_json());
}

std::string DeviceSimulator::make_timestamp() const {
    // Emit an ISO-8601 UTC timestamp so C++ and Python share one time format.
    const auto now = std::chrono::system_clock::now();
    const std::time_t time_value = std::chrono::system_clock::to_time_t(now);

    std::tm time_info;
    #if defined(_WIN32)
    gmtime_s(&time_info, &time_value);
    #else
    gmtime_r(&time_value, &time_info);
    #endif

    std::ostringstream stream;
    stream << std::put_time(&time_info, "%Y-%m-%dT%H:%M:%SZ");
    return stream.str();
}

}  // namespace smarttool
