#ifndef SMARTTOOL_COMM_MQTT_MQTT_PUBLISHER_H
#define SMARTTOOL_COMM_MQTT_MQTT_PUBLISHER_H

#include <memory>
#include <string>

namespace smarttool {

class MqttPublisher {
public:
    MqttPublisher(
        std::string broker_uri,
        std::string topic,
        std::string client_id = "smarttool-link-gateway",
        int qos = 1);

    ~MqttPublisher();
    MqttPublisher(MqttPublisher&& other) noexcept;
    MqttPublisher& operator=(MqttPublisher&& other) noexcept;

    MqttPublisher(const MqttPublisher&) = delete;
    MqttPublisher& operator=(const MqttPublisher&) = delete;

    // Establishes the publisher session against the configured broker endpoint.
    void connect();

    // Sends a serialized telemetry payload to the configured topic.
    void publish(const std::string& payload);

private:
    class MqttClientHandle;

    std::string broker_uri_;
    std::string topic_;
    std::string client_id_;
    int qos_;
    bool connected_;
    std::unique_ptr<MqttClientHandle> client_;
};

}  // namespace smarttool

#endif
