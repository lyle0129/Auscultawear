import time as t

# These are the constants
wavelet = 'db6'

# This part is for converting wav to array
import soundfile as sf
def wav_to_array(filename):
    # data is in numpy array format
    data, samplerate = sf.read(filename)
    time = np.linspace(0, len(data)/samplerate, num=len(data))
    # print(f'Data size: {data.size}   Time size: {time.size}   Samplerate: {samplerate}')
    return data, samplerate, time

# This part is for bandpass filter
import scipy.signal as signal
def bandpass_filter(data, samplerate, lofreq, hifreq):
    low = lofreq/(samplerate/2)
    high = hifreq/(samplerate/2)
    order = 5
    numerator, denumerator = signal.butter(order, [low, high], btype='band')
    filtered_data = signal.filtfilt(numerator, denumerator, data, axis=0)
    
    return filtered_data

# This part is for wavelet denoising
import pywt
import numpy as np
def denoising(data, wavelet): 
    coefficients = pywt.wavedec(data, wavelet, level=9)
    sigma = np.median(np.abs(coefficients[-1])) / 0.6745
    threshold = sigma * np.sqrt(2 * np.log(len(data)))
    denoised_coefficients = [ pywt.threshold(c, threshold) for c in coefficients ]
    
    return denoised_coefficients

# This part is for feature extraction
import numpy as np
import scipy.signal as signal
def extract_features(data):
    squared_signal = np.square(data)
    shannon_energy = -squared_signal * np.log(squared_signal + 1e-10)
    envelope = np.abs(signal.hilbert(data))
    return shannon_energy, envelope

# This part is for heart rate peak detection
import numpy as np
import scipy.signal as signal
def hr_peak_detection(data, time, samplerate, default = "default"):
    distance = 0
    moving_average = 0
    peaks = []
    peak_series = [0] * len(time)
    cumulative_peak_difference = 0
    cumulative_square_distance = 0
    
    distance_threshold = int(samplerate*0.2)                    # Distance between two peaks is at most 0.2s
    n_moving_average = int(samplerate*0.5)                      # Moving average window is 0.5s
    # start_record is not needed for an electret microphone
    # start_record = int(samplerate*0.2)                          # Start recording after 0.2s to disregard PDM transient
    start_record = 0

    # print("Start of Recording: " + str(start_record/samplerate) +"s")
    # print("Length of Window: " + str(n_moving_average/samplerate)+"s")

    # The code below computes for the peak using moving average. The moving average starts from 0 or n_moving_average samples
    # before the current sample until the current sample.
    for i, j in enumerate(data):
        # print(moving_average)
        if distance < 1:
            if i > max(start_record, n_moving_average):
                if i < n_moving_average-1:
                    moving_average = np.mean(data[start_record : i+1])
                else:
                    moving_average = np.mean(data[i-n_moving_average+1 : i+1])
                
                lower_threshold = moving_average * 2        # Lower threshold
                upper_threshold = moving_average * 10       # Upper threshold

                if j > lower_threshold and j < upper_threshold:
                    # print(f'{i} of {len(time)}')
                    
                    if len(peaks) == 0:
                        peak_series[i] = 1
                        peaks.append(i)
                        distance = distance_threshold

                    else:
                        # The code below is for peak rejection. The essence of peak rejection is to remove unnecessary peak due to noise. This 
                        # works by calculating for the standard deviation and z-score, and checking if removing would improve the standard deviation

                        peak_difference = ((i - peaks[-1])**2)**0.5
                        cumulative_peak_difference += peak_difference
                        
                        square_distance = (peak_difference - (cumulative_peak_difference/len(peaks)) ) ** 2
                        cumulative_square_distance += square_distance

                        if len(peaks) > 1:
                            sample_stdev = ( (cumulative_square_distance) / (len(peaks) - 1) ) ** 0.5
                            z_score = (square_distance**0.5)/sample_stdev
                            
                            # print(f'Sample: {i}')
                            # print(f'Diff: {peak_difference:.2f}   Mean: {cumulative_peak_difference/len(peaks):.2f}   Dist: {square_distance**0.5:.2f}')
                            # print(f'Sample STDev: {sample_stdev:.2f}   Z-score: {z_score:.2f}')

                            # If the peak differences have z-scores less than 4, then accept
                            if z_score < 3:
                                # print("Sample Accepted")
                                peak_series[i] = 1
                                peaks.append(i)
                                distance = distance_threshold
                            else:
                                pass
                                # print("Sample Rejected")
                            # print()
                        else:
                            peak_series[i] = 1
                            peaks.append(i)
                            distance = distance_threshold   
            else:
                continue
        else:
            distance-=1
            continue

    # The code below groups the peaks into odd and even, and computes the average distances of their elements. If the mean of 
    # one of the groups would be greated than the mean of the other, then it detects S1 and S2 peaks. Otherwise, it detects
    # only S1 peaks.
    # Issues
    #   - The code relies on correct identification and grouping of S1 and S2 peaks. If an erroneous peak is detected, then it
    #       would throw off the grouping and cause the mean of the group to change.  

    odd_peak_series = []
    even_peak_series = []

    for i, j in enumerate(peaks):
        if i % 2:
            odd_peak_series.append(data[j])
        else:
            even_peak_series.append(data[j])
    
    even_peak_average = np.mean(even_peak_series)
    odd_peak_average = np.mean(odd_peak_series)

    intervals = np.diff(peaks) / samplerate
    instantaneous_bpm = 60/intervals
    instantaneous_bpm_1 = np.mean(instantaneous_bpm[0::2])
    instantaneous_bpm_2 = np.mean(instantaneous_bpm[1::2])

    # print(f'Even-Odd Ave: {instantaneous_bpm_1:.2f}, Odd-Even Ave: {instantaneous_bpm_2:.2f}')

    even_interval = np.diff(peaks[0::2]) / samplerate
    odd_interval = np.diff(peaks[1::2]) / samplerate
    heart_rate_1 = 60 / np.mean(even_interval)
    heart_rate_2 = 60 / np.mean(odd_interval)
    heart_rate_ave = (heart_rate_1 + heart_rate_2) / 2

    instantaneous_bpm_even = 60 / even_interval
    instantaneous_bpm_odd = 60 / odd_interval
    percent_error_even = np.abs(instantaneous_bpm_even - heart_rate_ave)/heart_rate_ave * 100
    percent_error_odd = np.abs(instantaneous_bpm_odd - heart_rate_ave)/heart_rate_ave * 100
    # print(f'Ave: {heart_rate_ave:.2f} | Even Instantaneous BPMs: {instantaneous_bpm_even}')
    # print(f'Ave: {heart_rate_ave:.2f} | Odd Instantaneous BPMs: {instantaneous_bpm_odd}')
    # print(f'% Error of Ave vs Even: MAX={np.max(percent_error_even):.2f}%   AVE={np.mean(percent_error_even):.2f}%')
    # print(f'% Error of Ave vs Odd: MAX={np.max(percent_error_odd):.2f}%   AVE={np.mean(percent_error_odd):.2f}%')
    
    heart_rate = 60 / np.mean(intervals)
    percent_error = np.abs(instantaneous_bpm - heart_rate)/heart_rate * 100
    
    """
    print(f'Ave: {heart_rate:.2f} | Instantaneous BPMs: {instantaneous_bpm}')
    print(f'% Error of Ave vs Inst: MAX={np.max(percent_error):.2f}%   AVE={np.mean(percent_error):.2f}%')
    
    print(f'Check if S-S or P-P...')
    print(f'S-S:')
    print(f'MEAN={heart_rate_ave:.2f} BPM')
    print(f'AMP_EVEN={even_peak_average}   AMP_ODD={odd_peak_average}')
    print(f'%E_EVEN={np.mean(percent_error_even):.2f}   %E_ODD={np.mean(percent_error_odd):.2f}')
    print(f'P-P')
    print(f'MEAN={heart_rate:.2f} BPM')
    print(f'%E={np.mean(percent_error):.2f}')
    # """

    # If there is a clear difference between O-E and E-O timing, then S1 and S2 are properly marked
    # print(f'Timing Difference Value: { (instantaneous_bpm_1 - instantaneous_bpm_2) / np.max([instantaneous_bpm_1, instantaneous_bpm_2]):.2f}   Threshold=0.4')
    if (instantaneous_bpm_1 - instantaneous_bpm_2) / np.max([instantaneous_bpm_1, instantaneous_bpm_2]) > 0.4:
        print(f'By peak series, heart rate is ')
        return heart_rate_ave, peak_series

    # print(f'Amplitude Difference Value: {((even_peak_average - odd_peak_average) / (odd_peak_average) > 0.3):.2f}   THRESHOLD=|0.3|')
    # If there is a clear difference between the mean peak, then one is S1 and the other is S2
    if (((even_peak_average - odd_peak_average) / odd_peak_average) > 0.3) or (((even_peak_average - odd_peak_average) / odd_peak_average) < -0.3):
        return heart_rate_ave, peak_series
    else:
        if default == 1:
            return heart_rate_ave, peak_series
        elif default == 2:
            return heart_rate, peak_series
        else:
            # print(f'% Error S-S Value: {( (np.mean(percent_error_even) + np.mean(percent_error_odd )) / 2):.2f}')
            # print(f'% Error P-P Value: {np.mean(percent_error):.2f}')
            # If the percent error against instantaneous BPM of S1-S1/S2-S2 is better than peak-to-peak, then its most likely
            # S1-S1 / S2-S2 
            if ((np.mean(percent_error_even)) + (np.mean(percent_error_odd) ) / 2) < np.mean(percent_error):
                return heart_rate_ave, peak_series
            else:
                return heart_rate, peak_series 

# This part is for respiratory rate peak detection
import numpy as np
import scipy.signal as signal
def rr_peak_detection(data, time, samplerate):
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

        # Compute area using trapezoidal integration
        area = np.trapz(window)
        areas.append(area)
    
    # Normalize the value of areas
    areas = areas / max(areas)

    # Get the signal that goes above the mean threshold
    areas = areas - np.mean(areas)
    for i, j in enumerate(areas):
        if j < 0:
            areas[i] = 0
    
    # Get the local maxima of the area
    peaks, _ = signal.find_peaks(areas, distance=samplerate*0.5)

    # Reject the local maxima if the value since the previous maxima did not go below the threshold 
    for i, j in enumerate(peaks):
        # print(f'Current peak = {areas[j]}, Previous peak = {last_peak}')
        if j > samplerate*0.5:
            if last_peak == 0:
                last_peak = areas[j]
                last_peak_index = j
                peak_series[j] = 1
                # print(f'Accept')

            else:
                if min(areas[last_peak_index:j]) == 0:
                    # print(f'Accept, reached {min(areas[last_peak_index:j])}')
                    last_peak = areas[j]
                    last_peak_index = j
                    peak_series[j] = 1
                    
                else:
                    # print(f'Reject, minimum of {min(areas[last_peak_index:j])} did not reach 0')
                    peaks = np.delete(peaks, i - adjust)
                    adjust += 1
        else:
            peaks = np.delete(peaks, i - adjust)
            adjust += 1
            # print(f'Rejected due to transient')

    rr_count = peaks.size
    # print(peaks.size)
    respiratory_rate = rr_count / (time.size/samplerate) * 60

    return respiratory_rate, peak_series, areas

# This is to save the output as wav
import soundfile as sf
def save_to_wav(data, filename, samplerate):
    sf.write(filename, data, samplerate)

import matplotlib.pyplot as plt
import pywt
def main(filename, filepath = "./training_data/", default = 0):
    # Default Key
    # 0 - Default, uses % difference to identify PP or SS
    # 1 - SS, uses the average of S1-S1 and S2-S2 for heart rate
    # 2 - PP, uses the average of peak to peak for heart rate
    start = t.process_time_ns()

    # File path
    # Extract data from wav to array
    data, samplerate, time = wav_to_array(filepath+filename)

    # Heart Rate Computations
    hr_lofreq = 10
    hr_hifreq = 200
    hr_filtered_input = bandpass_filter(data, samplerate, hr_lofreq, hr_hifreq)
    hr_denoised_coefficients = denoising(hr_filtered_input, wavelet)
    coeff5 = [np.zeros_like(c) if j != 5 else c for j, c in enumerate(hr_denoised_coefficients)]
    level5_wave = pywt.waverec(coeff5, wavelet)
    if level5_wave.size > len(time):
        level5_wave = level5_wave[:len(time)]
    elif level5_wave.size < len(time):
        level5_wave = np.pad(level5_wave, (0, len(time) - level5_wave.size))
    hr_shannon_energy, hr_envelope = extract_features(level5_wave)
    heartrate, hr_peak_series = hr_peak_detection(hr_envelope, time, samplerate, default)
    hr_lap = t.process_time_ns() - start

    # Respiratory Rate Computations
    rr_lofreq = 100
    rr_hifreq = 950
    rr_filtered_input = bandpass_filter(data, samplerate, rr_lofreq, rr_hifreq)
    rr_denoised_coefficients = denoising(rr_filtered_input, wavelet)
    coeff7 = [np.zeros_like(c) if j != 7 else c for j, c in enumerate(rr_denoised_coefficients)]
    level7_wave = pywt.waverec(coeff7, wavelet)
    if level7_wave.size > len(time):
        level7_wave = level7_wave[:len(time)]
    elif level7_wave.size < len(time):
        level7_wave = np.pad(level7_wave, (0, len(time) - level7_wave.size))
    rr_shannon_energy, rr_envelope = extract_features(level7_wave)
    respiratoryrate, rr_peak_series, rr_area = rr_peak_detection(rr_envelope, time, samplerate)
    rr_lap = t.process_time_ns() - hr_lap

    print(f'Runtime: HR {hr_lap:.2f}ns\tRR {rr_lap:.2f}ns,\tTotal {hr_lap + rr_lap:.2f}')

    if __name__ == "__main__":
        return(hr_denoised_coefficients, rr_denoised_coefficients, hr_filtered_input, rr_filtered_input, samplerate, time, data, filename, level5_wave, hr_shannon_energy, hr_envelope, heartrate, hr_peak_series, level7_wave, rr_shannon_energy, rr_envelope, respiratoryrate, rr_peak_series, rr_area)
    else:
        return (heartrate, respiratoryrate, hr_lap + rr_lap)

if __name__ == "__main__":
    filename = "39043_MV.wav"
    hr_denoised_coefficients, rr_denoised_coefficients, hr_filtered_input, rr_filtered_input, samplerate, time, data, filename, level5_wave, hr_shannon_energy, hr_envelope, heartrate, hr_peak_series, level7_wave, rr_shannon_energy, rr_envelope, respiratoryrate, rr_peak_series, rr_area = main(filename)
    
    # For debugging, saving back to wave
    hr_denoised = pywt.waverec(hr_denoised_coefficients, wavelet)
    rr_denoised = pywt.waverec(rr_denoised_coefficients, wavelet)
    
    save_to_wav(hr_filtered_input, "[HR1 Filtered] " + filename, samplerate)
    save_to_wav(hr_denoised, "[HR2 Denoised] " + filename, samplerate)
    save_to_wav(level5_wave, "[HR3 Level 5] " + filename, samplerate)

    
    save_to_wav(rr_filtered_input, "[RR1 Filtered] " + filename, samplerate)
    save_to_wav(rr_denoised, "[RR2 Denoised] " + filename, samplerate)
    save_to_wav(level7_wave, "[RR3 Level 7] " + filename, samplerate)

    # Plotting both HS and LS
    # """
    plt.subplot2grid((5,2), (0,0), colspan=2)
    plt.plot(time, data)
    plt.title(f'Original Data - {filename}')
    
    plt.subplot2grid((5,2), (1,0))
    plt.plot(time, level5_wave)
    plt.title("Level 5 Data")
    
    plt.subplot2grid((5,2), (2,0))
    plt.plot(time, hr_shannon_energy)
    plt.title("Shannon Energy")
    
    plt.subplot2grid((5,2), (3,0))
    plt.plot(time, hr_envelope/max(hr_envelope))
    plt.title(f'Envelope, Peaks - {heartrate:.2f} BPM')
    
    plt.subplot2grid((5,2), (4,0))
    plt.plot(time, np.multiply(hr_peak_series, np.max(level5_wave)))
    plt.plot(time, level5_wave)
    plt.title(f'Overlay')

    plt.subplot2grid((5,2), (1,1))
    plt.plot(time, level7_wave)
    plt.title("Level 7 Data")
    
    plt.subplot2grid((5,2), (2,1))
    plt.plot(time, rr_shannon_energy)
    plt.title("Shannon Energy")
    
    plt.subplot2grid((5,2), (3,1))
    plt.plot(time, rr_area)
    plt.title(f'Envelope, Peaks - {respiratoryrate:.2f} BPM')
    
    plt.subplot2grid((5,2), (4,1))
    plt.plot(time, np.multiply(rr_peak_series, np.max(level7_wave)))
    plt.plot(time, level7_wave)
    plt.title(f'Overlay')

    plt.show()
    # """