import pyaudio
import numpy as np
import matplotlib.pyplot as plt
import wave
import time
from matplotlib.animation import FuncAnimation

# Audio settings
FORMAT = pyaudio.paInt16  # 16-bit format
CHANNELS = 1              # Mono
RATE = 44100              # Sampling rate (Hz)
CHUNK = 1024              # Buffer size
RECORD_SECONDS = 5        # Recording duration
OUTPUT_FILENAME = "recorded_audio.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Find USB microphone
device_index = None
for i in range(audio.get_device_count()):
    dev_info = audio.get_device_info_by_index(i)
    print(f"Device {i}: {dev_info['name']}")

    if "USB" in dev_info['name']:  # Adjust for your mic
        device_index = i
        print(f"Using USB microphone with index: {device_index}")
        break

if device_index is None:
    print("No USB microphone found. Using default input.")

# Open audio stream
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK,
                    input_device_index=device_index)

# Set up the plot
fig, ax = plt.subplots()
x = np.linspace(0, CHUNK / RATE, CHUNK)  # Time axis
line, = ax.plot(x, np.random.rand(CHUNK), '-', lw=1)

ax.set_ylim(-32000, 32000)  # 16-bit audio range
ax.set_xlim(0, CHUNK / RATE)
ax.set_xlabel("Time (s)")
ax.set_ylabel("Amplitude")
ax.set_title("Real-Time Audio Waveform")

frames = []

def update(frame):
    """Update function for animation."""
    global frames
    data = stream.read(CHUNK, exception_on_overflow=False)
    audio_data = np.frombuffer(data, dtype=np.int16)  # Convert to int16
    line.set_ydata(audio_data)  # Update graph
    frames.append(data)  # Save audio data for file
    return line,

# Create animation
ani = FuncAnimation(fig, update, interval=50, blit=True)

print("Recording... Close the plot window to stop.")
plt.show()

# Stop recording
print("Recording finished.")
stream.stop_stream()
stream.close()
audio.terminate()

# Save recorded audio to WAV file
wf = wave.open(OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

print(f"Audio saved as {OUTPUT_FILENAME}")
