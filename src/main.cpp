#include <chrono>
#include <iostream>
#include <thread>

#include "config/runtime_settings.h"
#include "device/simulator/device_simulator.h"

// Entry point for the gateway demo.
// Loads runtime config, samples simulated sensors, and publishes telemetry.
int main() {
    try {
        const smarttool::RuntimeSettings settings = smarttool::load_runtime_settings();

        smarttool::MqttPublisher publisher(
            settings.broker_uri,
            settings.topic_telemetry,
            settings.client_id,
            settings.qos);
        publisher.connect();

        smarttool::DeviceSimulator simulator(settings.device_id, std::move(publisher));
        simulator.bootstrap_default_sensors();

        for (int i = 0; i < settings.publish_count; ++i) {
            simulator.publish_once();
            std::this_thread::sleep_for(std::chrono::milliseconds(settings.sample_interval_ms));
        }

        std::cout << "Simulation completed." << std::endl;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Gateway error: " << error.what() << std::endl;
        return 1;
    }
}
