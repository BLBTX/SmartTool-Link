#include "temperature_sensor.h"

#include <cmath>

namespace smarttool {

TemperatureSensor::TemperatureSensor() : BaseSensor("temperature", "C") {}

double TemperatureSensor::sample(std::size_t tick) const {
    return 42.0 + std::sin(static_cast<double>(tick) * 0.35) * 6.5;
}

}  // namespace smarttool
