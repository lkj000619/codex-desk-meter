#include "bsp.h"
#include "driver/gpio.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io_additions.h"
#include "esp_lcd_st7701.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_heap_caps.h"
#include "esp_memory_utils.h"
#include "esp_check.h"

#include "st7701_commands.inc"

static uint16_t *pixels;
static esp_lcd_panel_handle_t panel;

esp_err_t bsp_init(void)
{
    // Leave the active-low backlight dark until RGB DMA has a valid framebuffer.
    gpio_set_level(GPIO_NUM_6, 1);
    gpio_config_t backlight = { .pin_bit_mask=1ULL<<6, .mode=GPIO_MODE_OUTPUT };
    ESP_ERROR_CHECK(gpio_config(&backlight));

    spi_line_config_t lines = {
        .cs_io_type=IO_TYPE_GPIO, .cs_gpio_num=GPIO_NUM_0,
        .scl_io_type=IO_TYPE_GPIO, .scl_gpio_num=GPIO_NUM_2,
        .sda_io_type=IO_TYPE_GPIO, .sda_gpio_num=GPIO_NUM_1,
        .io_expander=NULL,
    };
    esp_lcd_panel_io_3wire_spi_config_t io_cfg=ST7701_PANEL_IO_3WIRE_SPI_CONFIG(lines,0);
    esp_lcd_panel_io_handle_t io=NULL;
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_io_3wire_spi(&io_cfg,&io),"bsp","3wire SPI");

    esp_lcd_rgb_panel_config_t rgb={
        .clk_src=LCD_CLK_SRC_DEFAULT, .psram_trans_align=64,
        .bounce_buffer_size_px=10*320, .num_fbs=1,
        .data_width=16, .bits_per_pixel=16,
        .de_gpio_num=40, .pclk_gpio_num=41, .vsync_gpio_num=39, .hsync_gpio_num=38,
        .disp_gpio_num=-1,
        .data_gpio_nums={21,5,45,48,47,14,13,12,11,10,9,17,46,3,8,18},
        .timings={
            .pclk_hz=18000000, .h_res=320, .v_res=820,
            .hsync_back_porch=30, .hsync_front_porch=30, .hsync_pulse_width=6,
            .vsync_back_porch=20, .vsync_front_porch=20, .vsync_pulse_width=40,
        },
        .flags.fb_in_psram=true,
    };
    st7701_vendor_config_t vendor={
        .init_cmds=panel_commands,
        .init_cmds_size=sizeof(panel_commands)/sizeof(panel_commands[0]),
        .rgb_config=&rgb,
        .flags.enable_io_multiplex=1,
    };
    esp_lcd_panel_dev_config_t config={
        .reset_gpio_num=GPIO_NUM_16,
        .rgb_ele_order=LCD_RGB_ELEMENT_ORDER_RGB,
        .bits_per_pixel=16,
        .vendor_config=&vendor,
    };
    ESP_RETURN_ON_ERROR(esp_lcd_new_panel_st7701(io,&config,&panel),"bsp","ST7701");
    // Multiplex constructor already reset/programmed ST7701 and deleted command IO.
    ESP_RETURN_ON_ERROR(esp_lcd_panel_init(panel),"bsp","RGB init");
    ESP_RETURN_ON_ERROR(esp_lcd_rgb_panel_get_frame_buffer(panel,1,(void **)&pixels),"bsp","framebuffer");
    if (!pixels || !esp_ptr_external_ram(pixels)) return ESP_ERR_NO_MEM;
    for (int i=0;i<320*820;i++) pixels[i]=0xF7BE;
    // ST7701 command IO has been deleted with CS inactive; RGB no longer uses GPIO0.
    ESP_RETURN_ON_ERROR(gpio_set_level(GPIO_NUM_0,1),"bsp","CS idle");
    ESP_RETURN_ON_ERROR(gpio_set_direction(GPIO_NUM_0,GPIO_MODE_INPUT),"bsp","BOOT input");
    ESP_RETURN_ON_ERROR(gpio_set_pull_mode(GPIO_NUM_0,GPIO_PULLUP_ONLY),"bsp","BOOT pullup");
    ESP_RETURN_ON_ERROR(gpio_set_level(GPIO_NUM_6,0),"bsp","backlight on");
    return ESP_OK;
}

void bsp_pixel(int x,int y,uint16_t color)
{
    if (pixels && x>=0 && x<820 && y>=0 && y<320)
        pixels[(819-x)*320+y]=color; // logical 90-degree landscape mapping to portrait RGB DMA
}
void bsp_fill(int x,int y,int w,int h,uint16_t color)
{
    if (w<=0 || h<=0) return;
    for(int yy=y;yy<y+h;yy++) for(int xx=x;xx<x+w;xx++) bsp_pixel(xx,yy,color);
}
int bsp_boot_level(void) { return gpio_get_level(GPIO_NUM_0); }
