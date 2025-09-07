
struct adc_channel_cfg adc_channel_mic = {
    .gain = ADC_GAIN,
    .reference = ADC_REFERENCE,
    .acquisition_time = ADC_ACQUISITION_TIME,
    .channel_id = ADC_CHANNEL_MIC,
    .input_positive = SAADC_CH_PSELP_PSELP_AnalogInput0,  // <-- AIN0
};

// ADC sampling thread
void adc_sampling_thread(void *a, void *b, void *c) {
    struct adc_sequence sequence = {
        .channels = BIT(ADC_CHANNEL_MIC),
        .buffer = adc_sample_buffer,
        .buffer_size = sizeof(adc_sample_buffer),
        .resolution = ADC_RESOLUTION,
    };

    for (int i = 0; i < SAMPLE_COUNT; i++) {
        uint32_t t_start = k_cycle_get_32();
        if (adc_read(adc_dev, &sequence) == 0) {
                electret_buf[i] = adc_sample_buffer[0];
        } else {
                electret_buf[i] = -1;
                printk("ADC read failed at sample %d\n", i);
        }
        uint32_t t_end = k_cycle_get_32();
        uint32_t elapsed_us = k_cyc_to_us_floor32(t_end - t_start);
        if (elapsed_us < 500) {
            k_busy_wait(500 - elapsed_us);
        }
    }
    recording_done = true;
}

void start_electret_thread(void)
{
        k_thread_create(&adc_thread_data, adc_thread_stack,
                ADC_THREAD_STACK_SIZE,
                adc_sampling_thread,
                NULL, NULL, NULL,
                ADC_THREAD_PRIORITY, 0, K_NO_WAIT);
}
