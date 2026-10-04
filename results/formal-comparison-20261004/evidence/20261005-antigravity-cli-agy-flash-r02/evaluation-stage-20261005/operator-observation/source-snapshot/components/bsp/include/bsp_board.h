#ifndef BSP_BOARD_H
#define BSP_BOARD_H

#include "driver/gpio.h"
#include <stdint.h>
#include <stdbool.h>

#ifdef __cplusplus
extern "C" {
#endif

/* LCD Hardware Pins */
#define PIN_LCD_SPI_CS     GPIO_NUM_0
#define PIN_LCD_SPI_SCK    GPIO_NUM_2
#define PIN_LCD_SPI_SDO    GPIO_NUM_1

#define PIN_LCD_RGB_DE     GPIO_NUM_40
#define PIN_LCD_RGB_PCLK   GPIO_NUM_41
#define PIN_LCD_RGB_VSYNC  GPIO_NUM_39
#define PIN_LCD_RGB_HSYNC  GPIO_NUM_38
#define PIN_LCD_RGB_RESET  GPIO_NUM_16

/* Backlight PWM */
#define PIN_LCD_BL         GPIO_NUM_6

/* BOOT button (shared with SPI CS after init) */
#define PIN_BOOT_BUTTON    GPIO_NUM_0

/* I2C Pins (QMI8658 IMU & PCF85063 RTC) */
#define PIN_I2C_SCL        GPIO_NUM_7
#define PIN_I2C_SDA        GPIO_NUM_15
#define I2C_ADDR_QMI8658   0x6B
#define I2C_ADDR_PCF85063  0x51

/* UART Pins (USB Serial) */
#define PIN_UART_TX        GPIO_NUM_43
#define PIN_UART_RX        GPIO_NUM_44

#ifdef __cplusplus
}
#endif

#endif /* BSP_BOARD_H */
