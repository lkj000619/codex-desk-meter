#include "board.h"
#include <stdlib.h>
#include <string.h>
#include "esp_heap_caps.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_lcd_panel_ops.h"
#include "driver/gpio.h"
#include "driver/ledc.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG="board";
static esp_lcd_panel_handle_t panel;
static uint16_t *pixels;
static void serial_bit(int v) { gpio_set_level(1,v); gpio_set_level(2,0); esp_rom_delay_us(1); gpio_set_level(2,1); esp_rom_delay_us(1); }
static void serial_byte(uint8_t b) { for(int i=7;i>=0;i--) serial_bit((b>>i)&1); }
static void command(uint8_t cmd,const uint8_t *data,int n,int delay) {
    gpio_set_level(0,0); serial_bit(0); serial_byte(cmd); gpio_set_level(0,1);
    if(n) { gpio_set_level(0,0); serial_bit(1); for(int i=0;i<n;i++) serial_byte(data[i]); gpio_set_level(0,1); }
    if(delay) vTaskDelay(pdMS_TO_TICKS(delay));
}
#define CMD(c,ms,...) do { const uint8_t d[]={__VA_ARGS__}; command(c,d,sizeof(d),ms); } while(0)
static void panel_commands(void) {
    CMD(0xFF,0,0x77,0x01,0x00,0x00,0x13); CMD(0xEF,0,0x08);
    CMD(0xFF,0,0x77,0x01,0x00,0x00,0x10); CMD(0xC0,0,0xE5,0x02); CMD(0xC1,0,0x15,0x0A); CMD(0xC2,0,0x07,0x02); CMD(0xCC,0,0x10);
    CMD(0xB0,0,0x00,0x08,0x51,0x0D,0xCE,0x06,0x00,0x08,0x08,0x24,0x05,0xD0,0x0F,0x6F,0x36,0x1F);
    CMD(0xB1,0,0x00,0x10,0x4F,0x0C,0x11,0x05,0x00,0x07,0x07,0x18,0x02,0xD3,0x11,0x6E,0x34,0x1F);
    CMD(0xFF,0,0x77,0x01,0x00,0x00,0x11); CMD(0xB0,0,0x4D); CMD(0xB1,0,0x37); CMD(0xB2,0,0x87); CMD(0xB3,0,0x80); CMD(0xB5,0,0x4A); CMD(0xB7,0,0x85); CMD(0xB8,0,0x21); CMD(0xB9,0,0x00,0x13); CMD(0xC0,0,0x09); CMD(0xC1,0,0x78); CMD(0xC2,0,0x78); CMD(0xD0,0,0x88);
    CMD(0xE0,100,0x80,0x00,0x02); CMD(0xE1,0,0x0F,0xA0,0x00,0x00,0x10,0xA0,0x00,0x00,0x00,0x60,0x60);
    CMD(0xE2,0,0x30,0x30,0x60,0x60,0x45,0xA0,0x00,0x00,0x46,0xA0,0x00,0x00,0x00);
    CMD(0xE3,0,0x00,0x00,0x33,0x33); CMD(0xE4,0,0x44,0x44); CMD(0xE5,0,0x0F,0x4A,0xA0,0xA0,0x11,0x4A,0xA0,0xA0,0x13,0x4A,0xA0,0xA0,0x15,0x4A,0xA0,0xA0);
    CMD(0xE6,0,0x00,0x00,0x33,0x33); CMD(0xE7,0,0x44,0x44); CMD(0xE8,0,0x10,0x4A,0xA0,0xA0,0x12,0x4A,0xA0,0xA0,0x14,0x4A,0xA0,0xA0,0x16,0x4A,0xA0,0xA0);
    CMD(0xEB,0,0x02,0x00,0x4E,0x4E,0xEE,0x44,0x00); CMD(0xED,0,0xFF,0xFF,0x04,0x56,0x72,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x27,0x65,0x40,0xFF,0xFF); CMD(0xEF,0,0x08,0x08,0x08,0x40,0x3F,0x64);
    CMD(0xFF,0,0x77,0x01,0x00,0x00,0x13); CMD(0xE8,0,0x00,0x0E); CMD(0xFF,0,0x77,0x01,0x00,0x00,0x00);
    command(0x11,NULL,0,120); CMD(0xFF,0,0x77,0x01,0x00,0x00,0x13); CMD(0xE8,10,0x00,0x0C); CMD(0xE8,0,0x00,0x00); CMD(0xFF,0,0x77,0x01,0x00,0x00,0x00); CMD(0x3A,0,0x55); CMD(0x36,0,0x00); CMD(0x35,0,0x00); command(0x29,NULL,0,20);
}
void board_brightness(uint8_t value) { ledc_set_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0,255-value); ledc_update_duty(LEDC_LOW_SPEED_MODE,LEDC_CHANNEL_0); }
bool board_start(void) {
    gpio_config_t io={.pin_bit_mask=(1ULL<<0)|(1ULL<<1)|(1ULL<<2)|(1ULL<<16),.mode=GPIO_MODE_OUTPUT,.pull_up_en=GPIO_PULLUP_ENABLE};
    if(gpio_config(&io)!=ESP_OK) return false;
    gpio_set_level(0,1); gpio_set_level(2,1); gpio_set_level(16,0); vTaskDelay(pdMS_TO_TICKS(20)); gpio_set_level(16,1); vTaskDelay(pdMS_TO_TICKS(120)); panel_commands();
    // CS and BOOT share GPIO0; after panel initialization leave CS high and release the pin.
    io.pin_bit_mask=1ULL<<0; io.mode=GPIO_MODE_INPUT; gpio_config(&io);
    esp_lcd_rgb_panel_config_t c={0};
    c.clk_src=LCD_CLK_SRC_DEFAULT; c.timings.pclk_hz=18000000; c.timings.h_res=320; c.timings.v_res=820;
    c.timings.hsync_back_porch=30; c.timings.hsync_front_porch=30; c.timings.hsync_pulse_width=6;
    c.timings.vsync_back_porch=20; c.timings.vsync_front_porch=20; c.timings.vsync_pulse_width=40;
    c.data_width=16; c.bits_per_pixel=16; c.num_fbs=1; c.flags.fb_in_psram=1; c.psram_trans_align=64;
    c.hsync_gpio_num=38; c.vsync_gpio_num=39; c.de_gpio_num=40; c.pclk_gpio_num=41; c.disp_gpio_num=-1;
    const int data[]={21,5,45,48,47,14,13,12,11,10,9,17,46,3,8,18};
    for(int i=0;i<16;i++) c.data_gpio_nums[i]=data[i];
    if(esp_lcd_new_rgb_panel(&c,&panel)!=ESP_OK || esp_lcd_panel_reset(panel)!=ESP_OK || esp_lcd_panel_init(panel)!=ESP_OK) return false;
    pixels=heap_caps_malloc(320*820*2,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
    if(!pixels) return false;
    memset(pixels,0,320*820*2);
    ledc_timer_config_t timer={.speed_mode=LEDC_LOW_SPEED_MODE,.duty_resolution=LEDC_TIMER_8_BIT,.timer_num=LEDC_TIMER_3,.freq_hz=50000,.clk_cfg=LEDC_AUTO_CLK};
    ledc_channel_config_t channel={.gpio_num=6,.speed_mode=LEDC_LOW_SPEED_MODE,.channel=LEDC_CHANNEL_0,.timer_sel=LEDC_TIMER_3,.duty=255};
    if(ledc_timer_config(&timer)!=ESP_OK || ledc_channel_config(&channel)!=ESP_OK) ESP_LOGW(TAG,"backlight PWM failed");
    board_present(); board_brightness(200); return true;
}
void board_clear(uint16_t color) { for(int i=0;i<320*820;i++) pixels[i]=color; }
void board_rect(int x,int y,int w,int h,uint16_t color) {
    if(!pixels) return;
    for(int yy=y;yy<y+h;yy++) for(int xx=x;xx<x+w;xx++) if(xx>=0&&xx<820&&yy>=0&&yy<320) pixels[xx*320+319-yy]=color;
}
// Compact ASCII glyphs generated from 5x7 column masks. Unsupported characters render as a box.
static const unsigned char font[][5]={
 {0,0,0,0,0},{0,0,95,0,0},{0,7,0,7,0},{20,127,20,127,20},{36,42,127,42,18},{35,19,8,100,98},{54,73,85,34,80},{0,5,3,0,0},{0,28,34,65,0},{0,65,34,28,0},{20,8,62,8,20},{8,8,62,8,8},{0,80,48,0,0},{8,8,8,8,8},{0,96,96,0,0},{32,16,8,4,2},
 {62,81,73,69,62},{0,66,127,64,0},{66,97,81,73,70},{33,65,69,75,49},{24,20,18,127,16},{39,69,69,69,57},{60,74,73,73,48},{1,113,9,5,3},{54,73,73,73,54},{6,73,73,41,30},{0,54,54,0,0},{0,86,54,0,0},{8,20,34,65,0},{20,20,20,20,20},{0,65,34,20,8},{2,1,81,9,6},{50,73,121,65,62},
 {126,17,17,17,126},{127,73,73,73,54},{62,65,65,65,34},{127,65,65,34,28},{127,73,73,73,65},{127,9,9,9,1},{62,65,73,73,122},{127,8,8,8,127},{0,65,127,65,0},{32,64,65,63,1},{127,8,20,34,65},{127,64,64,64,64},{127,2,12,2,127},{127,4,8,16,127},{62,65,65,65,62},{127,9,9,9,6},{62,65,81,33,94},{127,9,25,41,70},{70,73,73,73,49},{1,1,127,1,1},{63,64,64,64,63},{31,32,64,32,31},{63,64,56,64,63},{99,20,8,20,99},{3,4,120,4,3},{97,81,73,69,67},
 {0,127,65,65,0},{2,4,8,16,32},{0,65,65,127,0},{4,2,1,2,4},{64,64,64,64,64},{0,1,2,4,0},
 {32,84,84,84,120},{127,72,68,68,56},{56,68,68,68,32},{56,68,68,72,127},{56,84,84,84,24},{8,126,9,1,2},{12,82,82,82,62},{127,8,4,4,120},{0,68,125,64,0},{32,64,68,61,0},{127,16,40,68,0},{0,65,127,64,0},{124,4,24,4,120},{124,8,4,4,120},{56,68,68,68,56},{124,20,20,20,8},{8,20,20,24,124},{124,8,4,4,8},{72,84,84,84,32},{4,63,68,64,32},{60,64,64,32,124},{28,32,64,32,28},{60,64,48,64,60},{68,40,16,40,68},{12,80,80,80,60},{68,100,84,76,68},{0,8,54,65,0},{0,0,127,0,0},{0,65,54,8,0},{8,4,8,16,8}
};
void board_text(int x,int y,const char *s,uint16_t color,int scale) {
    for(;*s && x<815;s++) { unsigned char ch=(unsigned char)*s; if(ch<32||ch>126) ch='?';
        for(int col=0;col<5;col++) for(int row=0;row<7;row++) if(font[ch-32][col]&(1<<row)) board_rect(x+col*scale,y+row*scale,scale,scale,color);
        x+=6*scale;
    }
}
void board_present(void) { if(panel&&pixels) esp_lcd_panel_draw_bitmap(panel,0,0,320,820,pixels); }
bool board_boot_pressed(void) { return gpio_get_level(0)==0; }
