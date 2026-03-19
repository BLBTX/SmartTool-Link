#ifndef SMARTTOOL_DEVICE_SENSORS_TEMPERATURE_SENSOR_H
#define SMARTTOOL_DEVICE_SENSORS_TEMPERATURE_SENSOR_H

#include "../core/base_sensor.h"

namespace smarttool {

class TemperatureSensor : public BaseSensor {
public:
    TemperatureSensor();
    double sample(std::size_t tick) const override;
};

}  // namespace smarttool

#endif
