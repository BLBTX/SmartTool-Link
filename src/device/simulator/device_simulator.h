#ifndef SMARTTOOL_DEVICE_SIMULATOR_DEVICE_SIMULATOR_H
#define SMARTTOOL_DEVICE_SIMULATOR_DEVICE_SIMULATOR_H

#include <cstddef>
#include <memory>
#include <string>
#include <vector>

#include "../../comm/mqtt/mqtt_publisher.h"
#include "../../comm/serializer/telemetry_message.h"
#include "../core/base_sensor.h"

namespace smarttool {

class DeviceSimulator {
public:
    DeviceSimulator(std::string device_id, MqttPublisher publisher);

    // Registers the default sensor set used by the demo device.
    void bootstrap_default_sensors();

    // Collects one telemetry snapshot from all active sensors.
    TelemetryMessage sample();

    // Samples the device and publishes the resulting payload.
    void publish_once();

private:
    std::string make_timestamp() const;

    std::string device_id_;
    std::vector<std::unique_ptr<BaseSensor>> sensors_;
    MqttPublisher publisher_;
    std::size_t tick_;
};

}  // namespace smarttool

#endif
