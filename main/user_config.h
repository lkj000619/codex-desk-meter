#ifndef USER_CONFIG_H
#define USER_CONFIG_H

#include "driver/gpio.h"

/* I2C (QMI8658, PCF85063) */
#define BOARD_I2C_SCL_PIN     GPIO_NUM_7
#define BOARD_I2C_SDA_PIN     GPIO_NUM_15
#define IMU_QMI8658_ADDR      0x6B
#define RTC_PCF85063_ADDR     0x51

/* BOOT Button */
#define BOARD_BOOT_BTN_PIN    GPIO_NUM_0

/* LCD Backlight PWM */
#define BOARD_LCD_BL_PIN      GPIO_NUM_6

/* LCD Resolution */
#define LCD_WIDTH             320
#define LCD_HEIGHT            820

/* LCD 3-wire SPI config pins */
#define LCD_SPI_CS_PIN        GPIO_NUM_0
#define LCD_SPI_SCK_PIN       GPIO_NUM_2
#define LCD_SPI_SDO_PIN       GPIO_NUM_1

/* LCD RGB Panel pins */
#define LCD_RGB_DE_PIN        GPIO_NUM_40
#define LCD_RGB_PCLK_PIN      GPIO_NUM_41
#define LCD_RGB_VSYNC_PIN     GPIO_NUM_39
#define LCD_RGB_HSYNC_PIN     GPIO_NUM_38
#define LCD_RGB_RESET_PIN     GPIO_NUM_16

/* RGB data pins (BGR order) */
#define LCD_RGB_B0_PIN        GPIO_NUM_21
#define LCD_RGB_B1_PIN        GPIO_NUM_5
#define LCD_RGB_B2_PIN        GPIO_NUM_45
#define LCD_RGB_B3_PIN        GPIO_NUM_48
#define LCD_RGB_B4_PIN        GPIO_NUM_47

#define LCD_RGB_G0_PIN        GPIO_NUM_14
#define LCD_RGB_G1_PIN        GPIO_NUM_13
#define LCD_RGB_G2_PIN        GPIO_NUM_12
#define LCD_RGB_G3_PIN        GPIO_NUM_11
#define LCD_RGB_G4_PIN        GPIO_NUM_10
#define LCD_RGB_G5_PIN        GPIO_NUM_9

#define LCD_RGB_R0_PIN        GPIO_NUM_17
#define LCD_RGB_R1_PIN        GPIO_NUM_46
#define LCD_RGB_R2_PIN        GPIO_NUM_3
#define LCD_RGB_R3_PIN        GPIO_NUM_8
#define LCD_RGB_R4_PIN        GPIO_NUM_18

/* Refresh Timers */
#define METER_AUTO_REFRESH_INTERVAL_SEC  60
#define METER_STALE_THRESHOLD_SEC        300

#endif /* USER_CONFIG_H */
