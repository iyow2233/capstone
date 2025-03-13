import numpy as np
import matplotlib.pyplot as plt
import wave
import sys
from scipy.fftpack import fft

def main():
        if len(sys.argv) < 2:
                print("Usage: python test_sound_plot.py <audio_file>")
                return
        # Load WAV file
        wav_filename = sys.argv[1]
        
        # Open the WAV file
        wf = wave.open(wav_filename, "rb")
        
        # Extract Audio Parameters
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frame_rate = wf.getframerate()
        n_frames = wf.getnframes()
        
        print(f"Channels: {n_channels}, Sample Width: {sample_width}, Frame Rate: {frame_rate}, Frames: {n_frames}")
        
        # Read and convert the audio data to numpy array
        signal = wf.readframes(n_frames)
        signal = np.frombuffer(signal, dtype=np.int16)
        
        # Close the WAV file
        wf.close()
        
        # Generate time axis
        time = np.linspace(0, len(signal) / frame_rate, num=len(signal))
        
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
        freqs = np.fft.fftfreq(N, 1 / frame_rate)
        fft_values = np.abs(fft(signal))
        
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
