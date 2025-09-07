#ifndef BLE_NUS_H
#define BLE_NUS_H

#include <zephyr/bluetooth/bluetooth.h>

void ble_nus_init(void);

extern bool ble_connected;

#endif // BLE_NUS_H