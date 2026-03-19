#include "telemetry_message.h"

#if SMARTTOOL_HAS_NLOHMANN_JSON
#include <nlohmann/json.hpp>
#endif

#include <iomanip>
#include <sstream>

namespace smarttool {

std::string TelemetryMessage::to_json() const {
#if SMARTTOOL_HAS_NLOHMANN_JSON
    nlohmann::json payload;
    payload["device_id"] = device_id;
    payload["tick"] = tick;
    payload["timestamp"] = timestamp;
    payload["metrics"] = metrics;
    return payload.dump();
#else
    std::ostringstream stream;
    stream << "{";
    stream << "\"device_id\":\"" << escape_json(device_id) << "\",";
    stream << "\"tick\":" << tick << ",";
    stream << "\"timestamp\":\"" << escape_json(timestamp) << "\",";
    stream << "\"metrics\":{";

    bool first = true;
    for (const auto& entry : metrics) {
        if (!first) {
            stream << ",";
        }
        first = false;
        stream << "\"" << escape_json(entry.first) << "\":"
               << std::fixed << std::setprecision(3) << entry.second;
    }

    stream << "}}";
    return stream.str();
#endif
}

std::string TelemetryMessage::escape_json(const std::string& value) {
    std::ostringstream stream;
    for (char ch : value) {
        switch (ch) {
            case '\\':
                stream << "\\\\";
                break;
            case '"':
                stream << "\\\"";
                break;
            case '\n':
                stream << "\\n";
                break;
            case '\r':
                stream << "\\r";
                break;
            case '\t':
                stream << "\\t";
                break;
            default:
                stream << ch;
                break;
        }
    }
    return stream.str();
}

}  // namespace smarttool
