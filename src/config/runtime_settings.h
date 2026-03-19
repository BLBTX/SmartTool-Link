#ifndef SMARTTOOL_CONFIG_RUNTIME_SETTINGS_H
#define SMARTTOOL_CONFIG_RUNTIME_SETTINGS_H

#include <string>

namespace smarttool {

struct RuntimeSettings {
    std::string device_id = "tool-001";
    int publish_count = 3;
    int sample_interval_ms = 250;
    std::string broker_uri = "tcp://localhost:1883";
    std::string topic_telemetry = "smarttool/devices/telemetry";
    std::string client_id = "smarttool-link-gateway";
    int qos = 1;
};

// Loads gateway runtime settings from config files with example fallbacks.
RuntimeSettings load_runtime_settings();

}  // namespace smarttool

#endif
