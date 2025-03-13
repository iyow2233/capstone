import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import sys

def main():
    # Check if the user provided a filename as an argument
    if len(sys.argv) < 2:
        print("Usage: python read_m4a.py <audio_file>")
        return
    
    input_filename = sys.argv[1]

    try:
        # Load audio file (supports WAV, M4A, MP3, etc.)
        signal, sample_rate = librosa.load(input_filename, sr=None)
    except Exception as e:
        print(f"Error: Unable to read the file. Details: {e}")
        return

    print(f"Sample Rate: {sample_rate}, Total Samples: {len(signal)}")

    # Generate time axis
    time = np.linspace(0, len(signal) / sample_rate, num=len(signal))

    # Plot waveform
    plt.figure(figsize=(12, 4))
    plt.plot(time, signal, label="Audio Waveform")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.title("Waveform of Audio File")
    plt.legend()
    plt.savefig("waveform_plot.png", dpi=300)  # Save the waveform plot
    plt.show()

    # FFT (Frequency Analysis)
    N = len(signal)
    freqs = np.fft.fftfreq(N, 1 / sample_rate)
    fft_values = np.abs(np.fft.fft(signal))

    # Plot frequency spectrum
    plt.figure(figsize=(12, 4))
    plt.plot(freqs[:N // 2], fft_values[:N // 2])  # Only plot positive frequencies
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.title("Frequency Spectrum (FFT)")
    plt.savefig("frequency_spectrum.png", dpi=300)  # Save the frequency spectrum plot
    plt.show()

    print("Plots saved as 'waveform_plot.png' and 'frequency_spectrum.png'")

if __name__ == "__main__":
    main()
