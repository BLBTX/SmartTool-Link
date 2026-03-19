cmake_minimum_required(VERSION 3.20)

project(SmartToolLink VERSION 0.1.0 LANGUAGES CXX)

include(FetchContent)

set(CMAKE_CXX_STANDARD 14)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

option(SMARTTOOL_ENABLE_WARNINGS "Enable compiler warnings" ON)
option(SMARTTOOL_FETCH_DEPS "Allow CMake to fetch third-party dependencies" ON)
option(SMARTTOOL_ENABLE_REAL_MQTT "Enable Eclipse Paho MQTT publishing" OFF)

set(SMARTTOOL_HAS_NLOHMANN_JSON 0)
set(SMARTTOOL_HAS_PAHO_MQTT 0)
set(SMARTTOOL_PAHO_CPP_TARGET "")

find_package(nlohmann_json CONFIG QUIET)

if(NOT nlohmann_json_FOUND AND SMARTTOOL_FETCH_DEPS)
    FetchContent_Declare(
        nlohmann_json
        GIT_REPOSITORY https://github.com/nlohmann/json.git
        GIT_TAG v3.11.3
    )
    FetchContent_MakeAvailable(nlohmann_json)
endif()

if(nlohmann_json_FOUND OR TARGET nlohmann_json::nlohmann_json)
    set(SMARTTOOL_HAS_NLOHMANN_JSON 1)
endif()

if(NOT SMARTTOOL_HAS_NLOHMANN_JSON)
    message(FATAL_ERROR "nlohmann_json is required for runtime config and telemetry serialization.")
endif()

if(SMARTTOOL_ENABLE_REAL_MQTT)
    find_package(PahoMqttCpp CONFIG QUIET)

    if(NOT PahoMqttCpp_FOUND AND SMARTTOOL_FETCH_DEPS)
        set(PAHO_BUILD_SHARED OFF CACHE BOOL "" FORCE)
        set(PAHO_BUILD_STATIC ON CACHE BOOL "" FORCE)
        set(PAHO_WITH_SSL OFF CACHE BOOL "" FORCE)
        set(PAHO_HIGH_PERFORMANCE ON CACHE BOOL "" FORCE)
        set(PAHO_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
        set(PAHO_BUILD_TESTS OFF CACHE BOOL "" FORCE)
        set(PAHO_WITH_UNIX_SOCKETS OFF CACHE BOOL "" FORCE)
        set(PAHO_WITH_MQTT_C ON CACHE BOOL "" FORCE)

        FetchContent_Declare(
            paho_mqtt_cpp
            GIT_REPOSITORY https://github.com/eclipse-paho/paho.mqtt.cpp.git
            GIT_TAG v1.4.2
        )
        FetchContent_MakeAvailable(paho_mqtt_cpp)
    endif()

    if(TARGET PahoMqttCpp::paho-mqttpp3)
        set(SMARTTOOL_PAHO_CPP_TARGET PahoMqttCpp::paho-mqttpp3)
    elseif(TARGET paho-mqttpp3)
        set(SMARTTOOL_PAHO_CPP_TARGET paho-mqttpp3)
    elseif(TARGET paho-mqttpp3-static)
        set(SMARTTOOL_PAHO_CPP_TARGET paho-mqttpp3-static)
    elseif(TARGET PahoMqttCpp::paho-mqttpp3-static)
        set(SMARTTOOL_PAHO_CPP_TARGET PahoMqttCpp::paho-mqttpp3-static)
    endif()

    if(NOT SMARTTOOL_PAHO_CPP_TARGET)
        message(FATAL_ERROR "SMARTTOOL_ENABLE_REAL_MQTT=ON requires PahoMqttCpp or SMARTTOOL_FETCH_DEPS=ON to fetch it.")
    endif()

    set(SMARTTOOL_HAS_PAHO_MQTT 1)
endif()

add_executable(smarttool_gateway
    src/main.cpp
    src/config/runtime_settings.cpp
    src/device/core/base_sensor.cpp
    src/device/sensors/temperature_sensor.cpp
    src/device/sensors/vibration_sensor.cpp
    src/device/sensors/current_sensor.cpp
    src/device/simulator/device_simulator.cpp
    src/comm/serializer/telemetry_message.cpp
    src/comm/mqtt/mqtt_publisher.cpp
)

target_include_directories(smarttool_gateway
    PRIVATE
        ${PROJECT_SOURCE_DIR}/src
)

target_compile_definitions(smarttool_gateway
    PRIVATE
        SMARTTOOL_HAS_NLOHMANN_JSON=${SMARTTOOL_HAS_NLOHMANN_JSON}
        SMARTTOOL_HAS_PAHO_MQTT=${SMARTTOOL_HAS_PAHO_MQTT}
)

if(SMARTTOOL_HAS_NLOHMANN_JSON)
    target_link_libraries(smarttool_gateway PRIVATE nlohmann_json::nlohmann_json)
endif()

if(SMARTTOOL_HAS_PAHO_MQTT)
    target_link_libraries(smarttool_gateway PRIVATE ${SMARTTOOL_PAHO_CPP_TARGET})
endif()

if(SMARTTOOL_ENABLE_WARNINGS)
    if(MSVC)
        target_compile_options(smarttool_gateway PRIVATE /W4 /permissive-)
    else()
        target_compile_options(smarttool_gateway PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif()
