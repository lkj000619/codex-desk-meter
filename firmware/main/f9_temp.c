#include "f9_temp.h"
#include "driver/temperature_sensor.h"

static temperature_sensor_handle_t sensor;

void f9_temp_init(void)
{
    temperature_sensor_config_t config=TEMPERATURE_SENSOR_CONFIG_DEFAULT(10,80);
    if (temperature_sensor_install(&config,&sensor)!=ESP_OK) sensor=NULL;
    if (sensor && temperature_sensor_enable(sensor)!=ESP_OK) {
        temperature_sensor_uninstall(sensor);
        sensor=NULL;
    }
}
bool f9_temp_read(float *celsius)
{ return sensor && celsius && temperature_sensor_get_celsius(sensor,celsius)==ESP_OK; }
