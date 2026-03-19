#ifndef SMARTTOOL_COMM_SERIALIZER_TELEMETRY_MESSAGE_H
#define SMARTTOOL_COMM_SERIALIZER_TELEMETRY_MESSAGE_H

#include <cstddef>
#include <map>
#include <string>

namespace smarttool {

struct TelemetryMessage {
    std::string device_id;
    std::size_t tick = 0;
    std::string timestamp;
    std::map<std::string, double> metrics;

    // Serializes the telemetry snapshot into a JSON payload for transport.
    std::string to_json() const;

private:
    static std::string escape_json(const std::string& value);
};

}  // namespace smarttool

#endif
