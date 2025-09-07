# These are the constants
samplerate = 4000.0
wavelet = 'db6'

# This part is for converting wav to array
import soundfile as sf
def wav_to_array(filename):
    #data is in numpy array format
    data, samplerate = sf.read(filename)
    time = np.linspace(0, len(data)/samplerate, num=len(data))

    return data, samplerate, time

# This part is for bandpass filter
import scipy.signal as signal
def bandpass_filter(data, samplerate, lowfreq, hifreq):
    nyquist = samplerate / 2
    low = lowfreq / nyquist
    high = hifreq / nyquist
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
def hr_peak_detection(data, time, samplerate):
    distance = 0
    moving_average = 0
    peaks = []
    peak_series = [0] * len(time)

    distance_threshold = int(samplerate*0.2)                    # Distance between two peaks is at most 0.2s
    n_moving_average = int(samplerate*0.5)                      # Moving average window is 0.5s
    start_record = int(samplerate*0.2)                          # Start recording after 0.2s to disregard PDM transient

    # print("Start of Recording: " + str(start_record/samplerate) +"s")
    # print("Length of Window: " + str(n_moving_average/samplerate)+"s")

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
                    peak_series[i] = 1
                    peaks.append(i)
                    distance = distance_threshold
            else:
                continue
        else:
            distance-=1
            continue
    
    # S1-S1 Peak Computations (Peak to Peak)
    intervals = np.diff(peaks) / samplerate
    heart_rate = 60 / np.mean(intervals)
    # print("BPM from P-P: " + str(heart_rate))
    
    # S1-S2 Peak Computations (Odd and Even)
    even_interval = np.diff(peaks[0::2]) / samplerate
    odd_interval = np.diff(peaks[1::2]) / samplerate
    heart_rate_1 = 60 / np.mean(even_interval)
    heart_rate_2 = 60 / np.mean(odd_interval)
    # print("BPM from Odd: " + str(heart_rate_1))
    # print("BPM from Even: " + str(heart_rate_2))
    # print("Average BPM: " + str((heart_rate_1 + heart_rate_2)/2))
    
    return heart_rate_1, peak_series

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
    peaks, _ = signal.find_peaks(areas, distance=samplerate*0.2)

    # Reject the local maxima if the value since the previous maxima did not go below the threshold 
    for i, j in enumerate(peaks):
        # print(f'Current peak = {areas[j]}, Previous peak = {last_peak}')
        if j > samplerate*0.2:
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

    intervals = np.diff(peaks) / samplerate
    respiratory_rate = 60 / np.mean(intervals)

    return respiratory_rate, peak_series, areas

# This is to save the output as wav
import soundfile as sf
def save_to_wav(data, filename, samplerate):
    sf.write(filename, data, samplerate)

import matplotlib.pyplot as plt
def main():
    # input_wav = "13918_MV.wav"
    # input_wav = "9983_AV.wav"
    # input_wav = "test_audio_1.wav"
    # input_wav = "test_audio_2.wav"
    # bp_output_wav = "[Bandpass] " + input_wav
    # dn_output_wav = "[Denoised] " + input_wav
    # input_wav = "Stethoscope.wav"
    # input_wav = "Stethoscope1.wav"
    input_wav = "40840_TV.wav"

    data, samplerate, time = wav_to_array(input_wav)
    denoised_coefficients = denoising(data, wavelet)

    # Heart Rate Calculations
    coeff5 = [np.zeros_like(c) if j != 5 else c for j, c in enumerate(denoised_coefficients)]
    level5_wave = pywt.waverec(coeff5, wavelet)
    hr_shannon_energy, hr_envelope = extract_features(level5_wave)
    heartrate, hr_peak_series = hr_peak_detection(hr_envelope, time, samplerate)
    
    # Respiratory Rate Calculations
    coeff7 = [np.zeros_like(c) if j != 7 else c for j, c in enumerate(denoised_coefficients)]
    level7_wave = pywt.waverec(coeff7, wavelet)
    rr_shannon_energy, rr_envelope = extract_features(level7_wave)
    respiratoryrate, rr_peak_series, rr_area = rr_peak_detection(rr_envelope, time, samplerate)

    # Plotting both HS and LS
    # """
    plt.subplot2grid((5,2), (0,0), colspan=2)
    plt.plot(time, data)
    plt.title(f'Original Data - {input_wav}')
    
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

    # plt.tight_layout()
    plt.show()
    # """

main()