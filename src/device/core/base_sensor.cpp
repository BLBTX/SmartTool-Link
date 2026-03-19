#include "base_sensor.h"

#include <utility>

namespace smarttool {

BaseSensor::BaseSensor(std::string name, std::string unit)
    : name_(std::move(name)), unit_(std::move(unit)) {}

BaseSensor::~BaseSensor() = default;

const std::string& BaseSensor::name() const {
    return name_;
}

const std::string& BaseSensor::unit() const {
    return unit_;
}

}  // namespace smarttool
