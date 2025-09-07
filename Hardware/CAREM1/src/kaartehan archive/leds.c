#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include "leds.h"

#define RED_LED_NODE DT_ALIAS(led0)
#define GREEN_LED_NODE DT_ALIAS(led1)
#define BLUE_LED_NODE DT_ALIAS(led2)

const struct gpio_dt_spec red_led = GPIO_DT_SPEC_GET(RED_LED_NODE, gpios);
const struct gpio_dt_spec green_led = GPIO_DT_SPEC_GET(GREEN_LED_NODE, gpios);
const struct gpio_dt_spec blue_led = GPIO_DT_SPEC_GET(BLUE_LED_NODE, gpios);

void led_init(void)
{
    gpio_pin_configure_dt(&red_led, GPIO_OUTPUT_ACTIVE);
    gpio_pin_configure_dt(&green_led, GPIO_OUTPUT_ACTIVE);
    gpio_pin_configure_dt(&blue_led, GPIO_OUTPUT_ACTIVE);
}

void led_on(const struct gpio_dt_spec *led)
{
    gpio_pin_set_dt(led, 1);
}

void led_off(const struct gpio_dt_spec *led)
{
    gpio_pin_set_dt(led, 0);
}
