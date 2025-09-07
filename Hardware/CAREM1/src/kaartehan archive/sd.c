#include <zephyr/kernel.h>
#include <zephyr/fs/fs.h>
#include <zephyr/storage/disk_access.h>
#include <ff.h>
#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(sd_module);

#define DISK_NAME "SD"
#define MOUNT_POINT "/SD:"
#define LOG_FILENAME "audio.txt"

static FATFS fat_fs;
static struct fs_mount_t mp = {
    .type = FS_FATFS,
    .mnt_point = MOUNT_POINT,
    .fs_data = &fat_fs,
};

int init_sd_card(void)
{
    uint32_t block_count = 0;
    uint32_t block_size = 0;
    uint64_t memory_size_mb;
    int err;

    printk("Initializing SD card...\n");

    err = disk_access_init(DISK_NAME);
    if (err) {
        printk("disk_access_init failed: %d\n", err);
        return -1;
    }

    if (disk_access_ioctl(DISK_NAME, DISK_IOCTL_GET_SECTOR_COUNT, &block_count)) {
        printk("Unable to get sector count\n");
        return -1;
    }

    if (disk_access_ioctl(DISK_NAME, DISK_IOCTL_GET_SECTOR_SIZE, &block_size)) {
        printk("Unable to get sector size\n");
        return -1;
    }

    memory_size_mb = (uint64_t)block_count * block_size / (1024 * 1024);
    printk("SD card size: %llu MB\n", memory_size_mb);

    err = fs_mount(&mp);
    if (err) {
        printk("Error mounting filesystem: %d\n", err);
        return -1;
    }

    printk("SD card mounted at %s\n", MOUNT_POINT);
    return 0;
}

// Optional helper if you want to write simple data (e.g., strings)
/*
int write_to_sd(const char *filename, const char *data)
{
    struct fs_file_t file;
    fs_file_t_init(&file);

    char path[64];
    snprintf(path, sizeof(path), "%s/%s", MOUNT_POINT, filename);

    int err = fs_open(&file, path, FS_O_WRITE | FS_O_CREATE | FS_O_APPEND);
    if (err) {
        LOG_ERR("Failed to open file %s: %d", path, err);
        return err;
    }

    fs_write(&file, data, strlen(data));
    fs_close(&file);
    return 0;
}
*/
