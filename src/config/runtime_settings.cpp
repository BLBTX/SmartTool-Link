#include "runtime_settings.h"

#include <fstream>
#include <stdexcept>

#include <nlohmann/json.hpp>

namespace smarttool {

namespace {

std::string resolve_config_path(const std::string& primary, const std::string& fallback) {
    std::ifstream primary_stream(primary.c_str());
    if (primary_stream.good()) {
        return primary;
    }

    std::ifstream fallback_stream(fallback.c_str());
    if (fallback_stream.good()) {
        return fallback;
    }

    throw std::runtime_error("Config file not found: " + primary + " or " + fallback);
}

nlohmann::json load_json_file(const std::string& primary, const std::string& fallback) {
    const std::string path = resolve_config_path(primary, fallback);
    std::ifstream stream(path.c_str());
    if (!stream.good()) {
        throw std::runtime_error("Unable to open config file: " + path);
    }

    nlohmann::json payload;
    stream >> payload;
    return payload;
}

}  // namespace

RuntimeSettings load_runtime_settings() {
    RuntimeSettings settings;

    const nlohmann::json app_config = load_json_file(
        "config/app/app.json",
        "config/app/app.example.json");
    const nlohmann::json mqtt_config = load_json_file(
        "config/mqtt/mqtt.json",
        "config/mqtt/mqtt.example.json");

    settings.device_id = app_config.value("device_id", settings.device_id);
    settings.publish_count = app_config.value("publish_count", settings.publish_count);
    settings.sample_interval_ms = app_config.value("sample_interval_ms", settings.sample_interval_ms);
    settings.broker_uri = mqtt_config.value("broker_uri", settings.broker_uri);
    settings.topic_telemetry = mqtt_config.value("topic_telemetry", settings.topic_telemetry);
    settings.client_id = mqtt_config.value("client_id", settings.client_id);
    settings.qos = mqtt_config.value("qos", settings.qos);

    return settings;
}

}  // namespace smarttool
