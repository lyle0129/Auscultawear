#ifndef IMU_H
#define IMU_H

#include <zephyr/device.h>

void start_imu_thread(void);
void stream_imu_data(void);

extern volatile size_t IMU_index;
extern volatile bool imu_recording;
extern int16_t imu_buf[1000];
extern int motion_flag;

#endif // IMU_H