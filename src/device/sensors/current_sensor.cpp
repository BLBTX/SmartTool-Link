#include "current_sensor.h"

#include <cmath>

namespace smarttool {

CurrentSensor::CurrentSensor() : BaseSensor("current", "A") {}

double CurrentSensor::sample(std::size_t tick) const {
    return 8.0 + std::cos(static_cast<double>(tick) * 0.4) * 1.2;
}

}  // namespace smarttool
