#include "cdm_rtc.h"

#include "cdm_receiver.h"

#include <sys/time.h>

#include "driver/i2c.h"
#include "esp_err.h"
#include "esp_log.h"

#define RTC_PORT I2C_NUM_0
#define RTC_SDA GPIO_NUM_15
#define RTC_SCL GPIO_NUM_7
#define RTC_ADDRESS 0x51
#define RTC_TIME_REGISTER 0x04

static const char *TAG = "cdm_rtc";
static bool rtc_bus_ready;

static uint8_t decimal_to_bcd(int value) {
    return (uint8_t)(((value / 10) << 4) | (value % 10));
}

bool cdm_rtc_read(int64_t *epoch_out) {
    if (!rtc_bus_ready || epoch_out == NULL) return false;
    uint8_t address = RTC_TIME_REGISTER;
    uint8_t registers[7] = {0};
    if (i2c_master_write_read_device(RTC_PORT, RTC_ADDRESS, &address, 1, registers, sizeof(registers), pdMS_TO_TICKS(100)) != ESP_OK) return false;
    uint8_t second, minute, hour, day, weekday, month, year;
    if ((registers[0] & 0x80u) != 0 ||
        !cdm_bcd_to_decimal(registers[0] & 0x7Fu, 59, &second) ||
        !cdm_bcd_to_decimal(registers[1] & 0x7Fu, 59, &minute) ||
        !cdm_bcd_to_decimal(registers[2] & 0x3Fu, 23, &hour) ||
        !cdm_bcd_to_decimal(registers[3] & 0x3Fu, 31, &day) ||
        !cdm_bcd_to_decimal(registers[4] & 0x07u, 6, &weekday) ||
        !cdm_bcd_to_decimal(registers[5] & 0x1Fu, 12, &month) ||
        !cdm_bcd_to_decimal(registers[6], 99, &year)) return false;
    (void)weekday;
    if (month < 1 || day < 1) return false;
    CdmCalendar calendar = {.year = 2000 + year, .month = month, .day = day,
                            .hour = hour, .minute = minute, .second = second};
    // Round-trip through the common UTC converter validates the date fields.
    int64_t days = 0;
    int y = calendar.year - (calendar.month <= 2);
    int era = y / 400;
    unsigned yoe = (unsigned)(y - era * 400);
    unsigned mp = (unsigned)calendar.month + (calendar.month > 2 ? (unsigned)-3 : 9u);
    unsigned doy = (153u * mp + 2u) / 5u + (unsigned)calendar.day - 1u;
    unsigned doe = yoe * 365u + yoe / 4u - yoe / 100u + doy;
    days = (int64_t)era * 146097 + doe - 719468;
    int64_t epoch = days * 86400 + calendar.hour * 3600 + calendar.minute * 60 + calendar.second;
    CdmCalendar check;
    if (!cdm_epoch_to_utc(epoch, &check) || check.year != calendar.year || check.month != calendar.month || check.day != calendar.day) return false;
    *epoch_out = epoch;
    return true;
}

bool cdm_rtc_sync(int64_t epoch) {
    CdmCalendar calendar;
    if (!rtc_bus_ready || !cdm_epoch_to_utc(epoch, &calendar) || calendar.year < 2024 || calendar.year > 2099) return false;
    int y = calendar.year - (calendar.month <= 2);
    int era = y / 400;
    unsigned yoe = (unsigned)(y - era * 400);
    unsigned mp = (unsigned)calendar.month + (calendar.month > 2 ? (unsigned)-3 : 9u);
    unsigned doy = (153u * mp + 2u) / 5u + (unsigned)calendar.day - 1u;
    unsigned doe = yoe * 365u + yoe / 4u - yoe / 100u + doy;
    int64_t days = (int64_t)era * 146097 + doe - 719468;
    int weekday = (int)((days + 4) % 7);
    if (weekday < 0) weekday += 7;
    uint8_t bytes[] = {RTC_TIME_REGISTER, decimal_to_bcd(calendar.second), decimal_to_bcd(calendar.minute),
        decimal_to_bcd(calendar.hour), decimal_to_bcd(calendar.day), decimal_to_bcd(weekday),
        decimal_to_bcd(calendar.month), decimal_to_bcd(calendar.year % 100)};
    if (i2c_master_write_to_device(RTC_PORT, RTC_ADDRESS, bytes, sizeof(bytes), pdMS_TO_TICKS(100)) != ESP_OK) return false;
    struct timeval tv = {.tv_sec = epoch, .tv_usec = 0};
    settimeofday(&tv, NULL);
    return true;
}

bool cdm_rtc_init(int64_t *epoch_out) {
    if (!rtc_bus_ready) {
        i2c_config_t config = {
            .mode = I2C_MODE_MASTER,
            .sda_io_num = RTC_SDA,
            .scl_io_num = RTC_SCL,
            .sda_pullup_en = GPIO_PULLUP_ENABLE,
            .scl_pullup_en = GPIO_PULLUP_ENABLE,
            .master.clk_speed = 100000,
            .clk_flags = 0,
        };
        if (i2c_param_config(RTC_PORT, &config) != ESP_OK) return false;
        esp_err_t result = i2c_driver_install(RTC_PORT, I2C_MODE_MASTER, 0, 0, 0);
        if (result != ESP_OK && result != ESP_ERR_INVALID_STATE) return false;
        rtc_bus_ready = true;
    }
    int64_t epoch;
    if (!cdm_rtc_read(&epoch) || epoch < 1704067200) return false;
    struct timeval tv = {.tv_sec = epoch, .tv_usec = 0};
    settimeofday(&tv, NULL);
    if (epoch_out != NULL) *epoch_out = epoch;
    ESP_LOGI(TAG, "holdover clock restored from PCF85063");
    return true;
}
