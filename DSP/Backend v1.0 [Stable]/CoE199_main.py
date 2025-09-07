# These are the constants
hs_lowfreq = 100.0
hs_hifreq = 400.0
rs_lowfreq = 100.0
rs_hifreq = 1000.0

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
    denoised_data = pywt.waverec(denoised_coefficients, wavelet)
    
    return coefficients, denoised_coefficients, denoised_data[:len(data)]

# This part is for feature extraction
import numpy as np
import scipy.signal as signal
def extract_features(data):
    squared_signal = np.square(data)
    shannon_energy = -squared_signal * np.log(squared_signal + 1e-10)
    envelope = np.abs(signal.hilbert(data))
    return shannon_energy, envelope

# This part is for peak detection
import numpy as np
import scipy.signal as signal
def peak_detection(data, time, samplerate):
    peak_series = [0] * samplerate*10

    peaks, _ = signal.find_peaks(data, distance=samplerate*0.2, height=[np.mean(data) * 2, np.mean(data) * 10])

    for i, j in enumerate(peaks):
        if j > samplerate*0.2:
            peak_series[j] = 1
        else:
            peaks = np.delete(peaks, i)

    s1_peaks = peaks[0::2]
    s1_interval = np.diff(s1_peaks) / samplerate
    s1_bpm = 60 / np.mean(s1_interval)
    print("BPM from S1: " + str(s1_bpm))

    """
    s2_peaks = peaks[1::2]
    s2_interval = np.diff(s2_peaks) / samplerate
    s2_bpm = 60 / np.mean(s2_interval)
    print("BPM from S2: " + str(s2_bpm))
    """
    
    """
    intervals = np.diff(peaks) / samplerate
    heart_rate = 60 / np.mean(intervals)
    """
    
    return s1_bpm, peak_series

# This part is for plotting data
import matplotlib.pyplot as plt
def plot_data(input_data, time, processed_data):
    freq = np.fft.rfftfreq(len(input_data), d=1/samplerate)
    magnitude = np.abs(np.fft.rfft(input_data))
    
    processed_freq = np.fft.rfftfreq(len(processed_data), d=1/samplerate)
    processed_magnitude = np.abs(np.fft.rfft(processed_data))

    plt.figure(figsize=(12, 6))
    plt.subplot(2,2,1)
    plt.plot(time, input_data, label='Original Time Domain')
    plt.xlabel('Time (s)')
    plt.ylabel('Magnitude')
    plt.legend()

    plt.subplot(2,2,2)
    plt.plot(freq, magnitude, label='Original Frequency Domain', color='r')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.legend()

    plt.subplot(2,2,3)
    plt.plot(time, processed_data, label='Processed Time Domain', color='b')
    plt.xlabel('Time (s)')
    plt.ylabel('Magnitude')
    plt.legend()

    plt.subplot(2,2,4)
    plt.plot(processed_freq, processed_magnitude, label='Processed Frequency Domain', color='g')
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    plt.legend()
    
    plt.tight_layout()
    plt.show()

# This is to save the output as wav
import soundfile as sf
def save_to_wav(data, filename, samplerate):
    sf.write(filename, data, samplerate)

def main():
    # input_wav = "13918_MV.wav"
    # input_wav = "9983_AV.wav"
    # input_wav = "test_audio_1.wav"
    input_wav = "test_audio_2.wav"
    bp_output_wav = "[Bandpass] " + input_wav
    dn_output_wav = "[Denoised] " + input_wav

    data, samplerate, time = wav_to_array(input_wav)
    
    """
    # Create a wav file of a bandpass'd file
    filtered_data = bandpass_filter(data, samplerate, hs_lowfreq, hs_hifreq)
    plot_data(data, time, filtered_data)
    save_to_wav(filtered_data, bp_output_wav, samplerate)
    # """

    """
    # Create a wav file of a denoised file
    coefficients, denoised_coefficients, denoised_data = denoising(data, wavelet)
    for i, c in enumerate(coefficients):
        plt.subplot(len(coefficients) + 1, 1, i + 2)
        plt.plot(c)
        plt.title(f'Level {i} Coefficients')
        coeffs_filtered = [np.zeros_like(coeffs) if j != i else coeffs for j, coeffs in enumerate(coefficients)]
        output_audio = pywt.waverec(coeffs_filtered, wavelet)
        sf.write("[Level "+str(i)+"] " + input_wav, output_audio, samplerate)
    plt.tight_layout()
    plt.show()

    for i, c in enumerate(denoised_coefficients):
        plt.subplot(len(coefficients) + 1, 1, i + 2)
        plt.plot(c)
        plt.title(f'Level {i} Coefficients')
        coeffs_filtered = [np.zeros_like(coeffs) if j != i else coeffs for j, coeffs in enumerate(coefficients)]
        output_audio = pywt.waverec(coeffs_filtered, wavelet)
        sf.write("[Denoised Level "+str(i)+"] " + input_wav, output_audio, samplerate)
    plt.tight_layout()
    plt.show()
    """

    # for heart rate, we want Level 4 or 5
    coefficients, denoised_coefficients, denoised_data = denoising(data, wavelet)
    coeff5 = [np.zeros_like(c) if j != 5 else c for j, c in enumerate(denoised_coefficients)]
    level5_wave = pywt.waverec(coeff5, wavelet)
    shannon_energy, envelope = extract_features(level5_wave)
    bpm, peak_series = peak_detection(envelope, time, samplerate)


    plt.subplot(5, 1, 1)
    plt.plot(time, data)
    plt.title("Original Data")
    plt.subplot(5, 1, 2)
    plt.plot(time, level5_wave)
    plt.title("Level 5 Data")
    plt.subplot(5, 1, 3)
    plt.plot(time, shannon_energy)
    plt.title("Shannon Energy")
    plt.subplot(5, 1, 4)
    plt.plot(time, envelope)
    plt.title("Envelope")
    plt.subplot(5, 1, 5)
    plt.plot(time, peak_series)
    plt.title(f'Peaks - {bpm:.2f} BPM')

    plt.show()

    

main()