#include <zephyr/kernel.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include <math.h>
#include "imu.h"

LOG_MODULE_REGISTER(imu_module);

#define STACK_SIZE 2048
#define IMU_THREAD_PRIORITY 5
#define MOTION_THRESHOLD 15

K_THREAD_STACK_DEFINE(imu_thread_stack, STACK_SIZE);
static struct k_thread imu_thread_data;

static struct sensor_value accel_x_out, accel_y_out, accel_z_out;
volatile size_t IMU_index = 0;
volatile bool imu_recording = false;
int16_t imu_buf[1000] = {0};
int motion_flag = 0;

static const struct device *lsm6dsl_dev = DEVICE_DT_GET_ONE(st_lsm6dsl);

static void lsm6dsl_trigger_handler(const struct device *dev, const struct sensor_trigger *trig)
{
    sensor_sample_fetch_chan(dev, SENSOR_CHAN_ACCEL_XYZ);
    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_X, &accel_x_out);
    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_Y, &accel_y_out);
    sensor_channel_get(dev, SENSOR_CHAN_ACCEL_Z, &accel_z_out);
}

static void imu_thread(void *arg1, void *arg2, void *arg3)
{
    struct sensor_trigger trig;
    struct sensor_value odr_attr;

    if (!device_is_ready(lsm6dsl_dev)) {
        printk("IMU not ready.\n");
        return;
    }

    odr_attr.val1 = 104;
    odr_attr.val2 = 0;
    sensor_attr_set(lsm6dsl_dev, SENSOR_CHAN_ACCEL_XYZ, SENSOR_ATTR_SAMPLING_FREQUENCY, &odr_attr);

    trig.type = SENSOR_TRIG_DATA_READY;
    trig.chan = SENSOR_CHAN_ACCEL_XYZ;

    if (sensor_trigger_set(lsm6dsl_dev, &trig, lsm6dsl_trigger_handler) != 0) {
        printk("Failed to set IMU trigger\n");
        return;
    }

    while (1) {
        double ax = sensor_value_to_double(&accel_x_out);
        double ay = sensor_value_to_double(&accel_y_out);
        double az = sensor_value_to_double(&accel_z_out);
        double motion = sqrt(ax * ax + ay * ay + az * az);

        if (motion > MOTION_THRESHOLD) {
            motion_flag = 1;
        }

        if (IMU_index < 1000 && imu_recording) {
            imu_buf[IMU_index++] = (int16_t)(motion * 100);
        } else if (IMU_index >= 1000) {
            imu_recording = false;
        }

        k_sleep(K_MSEC(10));
    }
}

void start_imu_thread(void)
{
    k_thread_create(&imu_thread_data, imu_thread_stack,
                    K_THREAD_STACK_SIZEOF(imu_thread_stack),
                    imu_thread, NULL, NULL, NULL,
                    IMU_THREAD_PRIORITY, 0, K_NO_WAIT);
}

void stream_imu_data(void)
{
    size_t total_samples = IMU_index;
    size_t offset = 0;
    while (offset < total_samples) {
        size_t send_size = MIN(100, total_samples - offset);

        int err;
        do {
            err = bt_nus_send(NULL, (uint8_t *)&imu_buf[offset], send_size * sizeof(imu_buf[0]));
            if (err == -ENOMEM) {
                k_sleep(K_MSEC(10));
            } else if (err < 0) {
                return;
            }
        } while (err == -ENOMEM);

        offset += send_size;
        k_sleep(K_MSEC(1));
    }

    const char *footer_msg = "finished\n";
    bt_nus_send(NULL, footer_msg, strlen(footer_msg));
}
