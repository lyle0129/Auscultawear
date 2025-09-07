import time as t
import soundfile as sf
import scipy.signal as signal
import pywt
import numpy as np

wavelet = 'db6'

def wav_to_array(filename):
    data, samplerate = sf.read(filename)
    time = np.linspace(0, len(data)/samplerate, num=len(data))
    return data, samplerate, time

def bandpass_filter(data, samplerate, lofreq, hifreq):
    low = lofreq/(samplerate/2)
    high = hifreq/(samplerate/2)
    order = 5
    numerator, denumerator = signal.butter(order, [low, high], btype='band')
    filtered_data = signal.filtfilt(numerator, denumerator, data, axis=0)
    return filtered_data

def denoising(data, wavelet): 
    coefficients = pywt.wavedec(data, wavelet, level=9)
    sigma = np.median(np.abs(coefficients[-1])) / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(data)))
    denoised_coefficients = [ pywt.threshold(c, threshold) for c in coefficients ]    
    return denoised_coefficients

def extract_features(data):
    squared_signal = np.square(data)
    envelope = np.abs(signal.hilbert(data))
    return envelope

def hr_peak_detection(data, time, samplerate, default=0):
    distance = 0
    moving_average = 0
    peaks = []
    peak_series = [0] * len(time)
    cumulative_peak_difference = 0
    cumulative_square_distance = 0
    distance_threshold = int(samplerate*0.1)                    
    n_moving_average = int(samplerate*0.5)                      
    start_record = 0
    for i, j in enumerate(data):
        if distance < 1:
            if i > max(start_record, n_moving_average):
                if i < n_moving_average-1:
                    moving_average = np.mean(data[start_record : i+1])
                else:
                    moving_average = np.mean(data[i-n_moving_average+1 : i+1])
                lower_threshold = moving_average * 2
                upper_threshold = moving_average * 10
                if j > lower_threshold and j < upper_threshold:
                    if len(peaks) == 0:
                        peak_series[i] = 1
                        peaks.append(i)
                        distance = distance_threshold
                    else:
                        peak_difference = ((i - peaks[-1])**2)**0.5
                        cumulative_peak_difference += peak_difference
                        square_distance = (peak_difference - (cumulative_peak_difference/len(peaks)) ) ** 2
                        cumulative_square_distance += square_distance
                        if len(peaks) > 2:
                            sample_stdev = ( (cumulative_square_distance) / (len(peaks) - 1) ) ** 0.5
                            z_score = (square_distance**0.5)/sample_stdev
                            if z_score < 3:
                                peak_series[i] = 1
                                peaks.append(i)
                                distance = distance_threshold
                            else:
                                pass
                        else:
                            peak_series[i] = 1
                            peaks.append(i)
                            distance = distance_threshold   
            else:
                continue
        else:
            distance-=1
            continue
    odd_peak_series = []
    even_peak_series = []
    for i, j in enumerate(peaks):
        if i % 2:
            odd_peak_series.append(data[j])
        else:
            even_peak_series.append(data[j])
    even_interval = np.diff(peaks[0::2]) / samplerate
    odd_interval = np.diff(peaks[1::2]) / samplerate
    heart_rate_1 = 60 / np.mean(even_interval)
    heart_rate_2 = 60 / np.mean(odd_interval)
    heart_rate_ave = (heart_rate_1 + heart_rate_2) / 2

    return heart_rate_ave, peak_series
    
def rr_peak_detection(data, time, samplerate, default = 0):
    areas = []
    peaks = []
    peak_series = [0] * len(time)
    window_size = samplerate//2
    last_peak = 0
    adjust = 0
    for i in range(len(data)):
        if i < window_size:
            window = data[0 : i+1]
        else:
            window = data[i-window_size : i]
        area = np.trapz(window)
        areas.append(area)
    areas = areas / max(areas)
    areas = areas - np.mean(areas)
    for i, j in enumerate(areas):
        if j < 0:
            areas[i] = 0
    peaks, _ = signal.find_peaks(areas, distance=samplerate*1)
    for i, j in enumerate(peaks):
        if j > samplerate*0.5:
            if last_peak == 0:
                last_peak = areas[j]
                last_peak_index = j
                peak_series[j] = 1
            else:
                if min(areas[last_peak_index:j]) == 0:
                    last_peak = areas[j]
                    last_peak_index = j
                    peak_series[j] = 1
                else:
                    peaks = np.delete(peaks, i - adjust)
                    adjust += 1
        else:
            peaks = np.delete(peaks, i - adjust)
            adjust += 1
    if default == 1:
        odd_rr = 60 / np.mean(np.diff(peaks[0::2]) / samplerate)
        even_rr = 60 / np.mean(np.diff(peaks[1::2]) / samplerate)
        ave_rr = (odd_rr + even_rr) / 2
        return ave_rr, peak_series, areas
    else:
        rr_count = peaks.size
        respiratory_rate = rr_count / (time.size/samplerate) * 60
        return respiratory_rate, peak_series, areas

import matplotlib.pyplot as plt
import pywt
def main(filename, filepath = "./", default = 1):
    data, samplerate, time = wav_to_array(filepath+filename)
    hr_filtered_input = bandpass_filter(data, samplerate, 10, 200)
    hr_denoised_coefficients = denoising(hr_filtered_input, wavelet)
    coeff5 = [np.zeros_like(c) if j != 5 else c for j, c in enumerate(hr_denoised_coefficients)]
    level5_wave = pywt.waverec(coeff5, wavelet)
    if level5_wave.size > len(time):
        level5_wave = level5_wave[:len(time)]
    elif level5_wave.size < len(time):
        level5_wave = np.pad(level5_wave, (0, len(time) - level5_wave.size))
    hr_envelope = extract_features(level5_wave)
    heartrate, _ = hr_peak_detection(hr_envelope, time, samplerate, default)
    
    rr_filtered_input = bandpass_filter(data, samplerate, 100, 950)
    rr_denoised_coefficients = denoising(rr_filtered_input, wavelet)
    coeff7 = [np.zeros_like(c) if j != 7 else c for j, c in enumerate(rr_denoised_coefficients)]
    level7_wave = pywt.waverec(coeff7, wavelet)
    if level7_wave.size > len(time):
        level7_wave = level7_wave[:len(time)]
    elif level7_wave.size < len(time):
        level7_wave = np.pad(level7_wave, (0, len(time) - level7_wave.size))
    rr_envelope = extract_features(level7_wave)
    respiratoryrate, _, _ = rr_peak_detection(rr_envelope, time, samplerate, 1)
    
    return (heartrate, respiratoryrate)

print(main("FS2_1.wav", "./auscultawear/final_trials/"))