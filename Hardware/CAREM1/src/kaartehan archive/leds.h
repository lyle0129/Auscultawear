#ifndef LEDS_H
#define LEDS_H

#include <zephyr/drivers/gpio.h>

extern const struct gpio_dt_spec red_led;
extern const struct gpio_dt_spec green_led;
extern const struct gpio_dt_spec blue_led;

void led_init(void);
void led_on(const struct gpio_dt_spec *led);
void led_off(const struct gpio_dt_spec *led);

#endif // LEDS_H