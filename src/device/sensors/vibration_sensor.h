#ifndef SMARTTOOL_DEVICE_SENSORS_VIBRATION_SENSOR_H
#define SMARTTOOL_DEVICE_SENSORS_VIBRATION_SENSOR_H

#include "../core/base_sensor.h"

namespace smarttool {

class VibrationSensor : public BaseSensor {
public:
    VibrationSensor();
    double sample(std::size_t tick) const override;
};

}  // namespace smarttool

#endif
