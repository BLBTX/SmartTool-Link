#ifndef SMARTTOOL_DEVICE_SENSORS_CURRENT_SENSOR_H
#define SMARTTOOL_DEVICE_SENSORS_CURRENT_SENSOR_H

#include "../core/base_sensor.h"

namespace smarttool {

class CurrentSensor : public BaseSensor {
public:
    CurrentSensor();
    double sample(std::size_t tick) const override;
};

}  // namespace smarttool

#endif
