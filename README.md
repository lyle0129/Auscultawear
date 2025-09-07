This is an undergraduate Thesis Project aimed at measuring heart and respiratory rates.

_____________________________________________________________________________________________________________________________________________________________________

It has 3 parts with 3 codebases separated into folders:

Hardware
- programmed in C, making use of Zephyr's RTOS framework.

DSP
- using python's numpy library to handle large data computations and pywavelet to handle denoising of the raw collected data 

Mobile Application
- an android flutter based mobile application
_____________________________________________________________________________________________________________________________________________________________________


Auscultawear: Audio-Based Physiological Signal Wearable

Most commercial wearable health devices are unable to measure both heart rate (HR) and respiratory rate (RR) simultaneously since they rely on photoplethysmography (PPG). This project explores an audio-based approach for wearable devices, enabling simultaneous detection and measurement of HR and RR.

📌 Overview

Auscultawear is a wearable device built on the nRF52840 MCU and a MAX4466 electret microphone to capture physiological sounds. Signals are transmitted to a mobile device where advanced signal processing techniques isolate and analyze the data.

⚙️ Methodology

Signal Acquisition

nRF52840 + MAX4466 microphone

Records physiological audio signals

Signal Processing

Bandpass filter isolates target frequencies

Wavelet thresholding & decomposition (db6 wavelet) for denoising

Hilbert transform extracts signal envelope

Customized peak detection algorithm for HR & RR estimation

Validation

Compared against Pulse Oximeter (PPG), Smartwatch (EKG), and KardiaMobile® EKG Monitor

📊 Results

Heart Rate (HR):

Best accuracy at FS1 (upper right intercostal space) and FS4 (apex of heart)

MAE: 5.23 ± 1.79 BPM (FS1), 5.18 ± 6.58 BPM (FS4)

Further FS1 validation: 4.58 ± 2.54 BPM on normal BMI subject

Respiratory Rate (RR):

Most accurate at BS1

MAE: 1.98 ± 1.21 BPM

Battery Life:

Estimated 68.98 hours of continuous operation

🚀 Conclusion

Auscultawear demonstrates the potential of audio-based wearable health monitoring as a reliable and low-cost solution for real-time HR and RR tracking. While results are promising, further refinements and large-scale validation across diverse demographics are required to enhance robustness and generalizability.
