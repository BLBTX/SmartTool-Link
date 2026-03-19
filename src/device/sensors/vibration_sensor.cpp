#include "vibration_sensor.h"

#include <cmath>

namespace smarttool {

VibrationSensor::VibrationSensor() : BaseSensor("vibration", "mm_s") {}

double VibrationSensor::sample(std::size_t tick) const {
    return 2.3 + std::abs(std::sin(static_cast<double>(tick) * 0.6)) * 1.8;
}

}  // namespace smarttool
