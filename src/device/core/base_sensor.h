#ifndef SMARTTOOL_DEVICE_CORE_BASE_SENSOR_H
#define SMARTTOOL_DEVICE_CORE_BASE_SENSOR_H

#include <cstddef>
#include <string>

namespace smarttool {

class BaseSensor {
public:
    BaseSensor(std::string name, std::string unit);
    virtual ~BaseSensor();

    const std::string& name() const;
    const std::string& unit() const;

    virtual double sample(std::size_t tick) const = 0;

private:
    std::string name_;
    std::string unit_;
};

}  // namespace smarttool

#endif
