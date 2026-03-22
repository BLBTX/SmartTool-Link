#include "mqtt_publisher.h"

#include <cstdlib>
#include <cstdio>
#include <ctime>
#include <fstream>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <utility>

#if defined(_WIN32)
#include <process.h>
#endif

#if SMARTTOOL_HAS_PAHO_MQTT
#include <mqtt/client.h>
#endif

namespace smarttool {

namespace {

struct BrokerEndpoint {
    std::string host;
    std::string port;
};

bool file_exists(const std::string& path) {
    std::ifstream file(path.c_str());
    return file.good();
}

BrokerEndpoint parse_broker_uri(const std::string& broker_uri) {
    // Normalize broker URIs into host/port pairs for both native MQTT and the
    // CLI fallback publisher.
    std::string address = broker_uri;
    const std::size_t scheme_pos = address.find("://");
    if (scheme_pos != std::string::npos) {
        address = address.substr(scheme_pos + 3);
    }

    const std::size_t path_pos = address.find('/');
    if (path_pos != std::string::npos) {
        address = address.substr(0, path_pos);
    }

    BrokerEndpoint endpoint;
    endpoint.host = address;
    endpoint.port = "1883";

    const std::size_t colon_pos = address.rfind(':');
    if (colon_pos != std::string::npos) {
        endpoint.host = address.substr(0, colon_pos);
        endpoint.port = address.substr(colon_pos + 1);
    }

    if (endpoint.host.empty()) {
        endpoint.host = "localhost";
    }

    return endpoint;
}

std::string resolve_temp_directory() {
#if defined(_WIN32)
    const char* temp_dir = std::getenv("TEMP");
    if (temp_dir != nullptr && temp_dir[0] != '\0') {
        return std::string(temp_dir);
    }
    return ".";
#else
    const char* temp_dir = std::getenv("TMPDIR");
    if (temp_dir != nullptr && temp_dir[0] != '\0') {
        return std::string(temp_dir);
    }
    return "/tmp";
#endif
}

std::string join_path(const std::string& left, const std::string& right) {
    if (left.empty()) {
        return right;
    }
    const char separator =
#if defined(_WIN32)
        '\\';
#else
        '/';
#endif
    if (left.back() == separator) {
        return left + right;
    }
    return left + separator + right;
}

std::string build_payload_file_path() {
    const auto stamp = static_cast<long long>(std::time(nullptr));
    return join_path(resolve_temp_directory(), "smarttool_payload_" + std::to_string(stamp) + ".json");
}

std::string quote_argument(const std::string& value) {
    return std::string("\"") + value + "\"";
}

std::string resolve_mosquitto_pub_path() {
    const char* override_path = std::getenv("SMARTTOOL_MOSQUITTO_PUB");
    if (override_path != nullptr && override_path[0] != '\0') {
        return std::string(override_path);
    }

#if defined(_WIN32)
    const std::string common_paths[] = {
        "C:\\Program Files\\Mosquitto\\mosquitto_pub.exe",
        "C:\\Program Files (x86)\\Mosquitto\\mosquitto_pub.exe",
    };
    for (const auto& candidate : common_paths) {
        if (file_exists(candidate)) {
            return candidate;
        }
    }
    return "mosquitto_pub.exe";
#else
    return "mosquitto_pub";
#endif
}

bool publish_with_mosquitto_cli(
    const std::string& executable,
    const std::string& broker_uri,
    const std::string& topic,
    int qos,
    const std::string& payload) {
    // Fallback path for environments where the native Paho dependency is not
    // available yet but we still want a runnable end-to-end demo.
    const BrokerEndpoint endpoint = parse_broker_uri(broker_uri);
    const std::string payload_file = build_payload_file_path();

    {
        std::ofstream stream(payload_file.c_str(), std::ios::binary);
        if (!stream.good()) {
            return false;
        }
        stream << payload;
    }

    std::ostringstream command;
#if defined(_WIN32)
    const std::string qos_value = std::to_string(qos);
    const char* arguments[] = {
        "mosquitto_pub",
        "-h",
        endpoint.host.c_str(),
        "-p",
        endpoint.port.c_str(),
        "-t",
        topic.c_str(),
        "-q",
        qos_value.c_str(),
        "-f",
        payload_file.c_str(),
        nullptr,
    };
    const intptr_t exit_code = _spawnv(_P_WAIT, executable.c_str(), arguments);
#else
    command << quote_argument(executable)
            << " -h " << quote_argument(endpoint.host)
            << " -p " << quote_argument(endpoint.port)
            << " -t " << quote_argument(topic)
            << " -q " << qos
            << " -f " << quote_argument(payload_file);
    const int exit_code = std::system(command.str().c_str());
#endif

    std::remove(payload_file.c_str());
    return exit_code == 0;
}

}  // namespace

class MqttPublisher::MqttClientHandle {
public:
#if SMARTTOOL_HAS_PAHO_MQTT
    MqttClientHandle(const std::string& broker_uri, const std::string& client_id)
        : client(broker_uri, client_id) {}

    mqtt::client client;
#else
    MqttClientHandle() = default;
#endif
};

MqttPublisher::MqttPublisher(std::string broker_uri, std::string topic, std::string client_id, int qos)
    : broker_uri_(std::move(broker_uri)),
      topic_(std::move(topic)),
      client_id_(std::move(client_id)),
      qos_(qos),
      connected_(false),
      client_(nullptr) {}

MqttPublisher::~MqttPublisher() {
#if SMARTTOOL_HAS_PAHO_MQTT
    if (connected_ && client_) {
        try {
            client_->client.disconnect();
        } catch (...) {
        }
    }
#endif
}

MqttPublisher::MqttPublisher(MqttPublisher&& other) noexcept = default;

MqttPublisher& MqttPublisher::operator=(MqttPublisher&& other) noexcept = default;

void MqttPublisher::connect() {
    // Establish the publishing path once at startup so the simulator can push
    // telemetry repeatedly without reconnecting for every sample.
#if SMARTTOOL_HAS_PAHO_MQTT
    try {
        client_.reset(new MqttClientHandle(broker_uri_, client_id_));
        mqtt::connect_options options;
        options.set_clean_session(true);
        client_->client.connect(options);
        connected_ = true;
        std::cout << "[mqtt] Connected to " << broker_uri_ << " on topic " << topic_ << std::endl;
    } catch (const mqtt::exception& error) {
        throw std::runtime_error(std::string("Failed to connect MQTT client: ") + error.what());
    }
#else
    connected_ = true;
    std::cout << "[mqtt] Connected to " << broker_uri_ << " on topic " << topic_;
    std::cout << " using mosquitto_pub fallback when available" << std::endl;
#endif
}

void MqttPublisher::publish(const std::string& payload) {
    // Publish one JSON telemetry payload through the active MQTT path.
    if (!connected_) {
        throw std::runtime_error("MQTT publisher is not connected.");
    }

#if SMARTTOOL_HAS_PAHO_MQTT
    try {
        auto message = mqtt::make_message(topic_, payload);
        message->set_qos(qos_);
        client_->client.publish(message);
    } catch (const mqtt::exception& error) {
        throw std::runtime_error(std::string("Failed to publish MQTT payload: ") + error.what());
    }
#else
    const std::string executable = resolve_mosquitto_pub_path();
    if (publish_with_mosquitto_cli(executable, broker_uri_, topic_, qos_, payload)) {
        std::cout << "[mqtt] Publish => " << payload << std::endl;
        return;
    }

    std::cout << "[mqtt] CLI publish unavailable, payload follows => " << payload << std::endl;
#endif
}

}  // namespace smarttool
