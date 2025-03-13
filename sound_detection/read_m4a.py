import numpy as np
import matplotlib.pyplot as plt
import librosa
import librosa.display
import sys
import os
from pydub import AudioSegment

def convert_m4a_to_wav(input_filename):
    """Converts an M4A file to WAV format for librosa to process."""
    output_filename = "temp_converted.wav"
    audio = AudioSegment.from_file(input_filename, format="m4a")
    audio.export(output_filename, format="wav")
    return output_filename

def main():
    if len(sys.argv) < 2:
        print("Usage: python read_m4a.py <audio_file>")
        return
    
    input_filename = sys.argv[1]

    # Check if the file exists
    if not os.path.exists(input_filename):
        print("Error: File not found.")
        return

    # Convert M4A to WAV if necessary
    if input_filename.lower().endswith(".m4a"):
        print("Converting M4A to WAV...")
        input_filename = convert_m4a_to_wav(input_filename)

    try:
        # Load the audio file
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
    plt.savefig("waveform_plot.png", dpi=300)
    plt.show()

    # FFT (Frequency Analysis)
    N = len(signal)
    freqs = np.fft.fftfreq(N, 1 / sample_rate)
    fft_values = np.abs(np.fft.fft(signal))

    # Plot frequency spectrum
    plt.figure(figsize=(12, 4))
    plt.plot(freqs[:N // 2], fft_values[:N // 2])
    plt.xlabel("Frequency (Hz)")
    plt.ylabel("Magnitude")
    plt.title("Frequency Spectrum (FFT)")
    plt.savefig("frequency_spectrum.png", dpi=300)
    plt.show()

    print("Plots saved as 'waveform_plot.png' and 'frequency_spectrum.png'")

    # Cleanup temporary WAV file if converted
    if input_filename == "temp_converted.wav":
        os.remove(input_filename)

if __name__ == "__main__":
    main()
