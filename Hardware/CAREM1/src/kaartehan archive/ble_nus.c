#include <zephyr/logging/log.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/services/nus.h>
#include <string.h>
#include <stdio.h>

#include "ble_nus.h"
#include "imu.h"
#include "audio.h"
#include "leds.h"

LOG_MODULE_REGISTER(ble_module);

#define DEVICE_NAME     CONFIG_BT_DEVICE_NAME
#define DEVICE_NAME_LEN (sizeof(DEVICE_NAME) - 1)

static const struct bt_data ad[] = {
    BT_DATA_BYTES(BT_DATA_FLAGS, (BT_LE_AD_GENERAL | BT_LE_AD_NO_BREDR)),
    BT_DATA(BT_DATA_NAME_COMPLETE, DEVICE_NAME, DEVICE_NAME_LEN),
};

static const struct bt_data sd[] = {
    BT_DATA_BYTES(BT_DATA_UUID128_ALL, BT_UUID_NUS_SRV_VAL),
};

bool ble_connected = false;

static void received(struct bt_conn *conn, const void *data, uint16_t len, void *ctx)
{
    char message[CONFIG_BT_L2CAP_TX_MTU + 1] = "";
    memcpy(message, data, MIN(sizeof(message) - 1, len));
    message[len] = '\0';

    printk("Received BLE command: %s\n", message);

    if (strncmp(message, "rec", 3) == 0 && !recording) {
        start_recording();
    } else if (strncmp(message, "send", 4) == 0) {
        stream_audio();
    } else if (strncmp(message, "imu", 3) == 0) {
        stream_imu_data();
    } else if (strcmp(message, "stop") == 0) {
        recording = false;
        current_mode = MODE_MANUAL;
        led_off(&red_led);
        led_off(&green_led);
        led_off(&blue_led);
        printk("Received stop command. Switching to Manual Mode.\n");
    } else if (strncmp(message, "manual", 6) == 0) {
        recording = false;
        current_mode = MODE_MANUAL;
        printk("Switched to manual mode\n");
    } else if (strncmp(message, "auto", 4) == 0) {
        current_mode = MODE_AUTO;
        k_sem_give(&mode_sem);
        printk("Switched to auto mode\n");
    } else if (strncmp(message, "cont", 4) == 0) {
        current_mode = MODE_CONTINUOUS;
        k_sem_give(&mode_sem);
        printk("Switched to continuous mode\n");
        led_on(&red_led);
        led_on(&green_led);
        led_on(&blue_led);
    } else {
        current_mode = MODE_MANUAL;
        recording = false;
        led_off(&red_led);
        led_off(&green_led);
        led_off(&blue_led);
        printk("Unknown BLE command: %s\n", message);

        const char *unknown = "Unknown Command!\n";
        if (bt_nus_send(NULL, unknown, strlen(unknown)) == 0) {
            k_sleep(K_MSEC(100));
        } else {
            LOG_ERR("Unknown command with no BLE connection.");
        }
    }
}

static void notif_enabled(bool enabled, void *ctx)
{
    ARG_UNUSED(ctx);
    printk("%s() - %s\n", __func__, (enabled ? "Enabled" : "Disabled"));
}

static struct bt_nus_cb nus_listener = {
    .notif_enabled = notif_enabled,
    .received = received,
};

static void connected(struct bt_conn *conn, uint8_t err)
{
    if (err) {
        LOG_ERR("BLE connection failed (err %d)", err);
        return;
    }

    LOG_INF("Connected!");
    ble_connected = true;

    if (last_sent_index > 0) {
        LOG_INF("Resuming audio stream from sample %d", last_sent_index);
        stream_audio();
    }
}

static void disconnected(struct bt_conn *conn, uint8_t reason)
{
    LOG_WRN("Disconnected (reason %d), restarting advertising...", reason);

    int err = bt_le_adv_start(BT_LE_ADV_CONN, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (err) {
        LOG_ERR("Failed to restart advertising (err %d)", err);
    } else {
        LOG_INF("Advertising restarted successfully.");
    }
}

static struct bt_conn_cb conn_callbacks = {
    .connected = connected,
    .disconnected = disconnected,
};

void ble_nus_init(void)
{
    int err;

    bt_conn_cb_register(&conn_callbacks);

    err = bt_nus_cb_register(&nus_listener, NULL);
    if (err) {
        LOG_ERR("Failed to register NUS callback: %d", err);
        return;
    }

    err = bt_enable(NULL);
    if (err) {
        LOG_ERR("Bluetooth enable failed: %d", err);
        return;
    }

    err = bt_le_adv_start(BT_LE_ADV_CONN, ad, ARRAY_SIZE(ad), sd, ARRAY_SIZE(sd));
    if (err) {
        LOG_ERR("Advertising start failed: %d", err);
    } else {
        LOG_INF("Bluetooth initialized and advertising");
    }
}
