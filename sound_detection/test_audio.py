import pyaudio
import wave

# Audio settings
FORMAT = pyaudio.paInt16  # 16-bit format
CHANNELS = 1              # Mono
RATE = 44100              # Sampling rate
CHUNK = 1024              # Buffer size
RECORD_SECONDS = 10        # Short test recording
OUTPUT_FILENAME = "test_audio.wav"

# Initialize PyAudio
audio = pyaudio.PyAudio()

# Open audio stream
stream = audio.open(format=FORMAT, channels=CHANNELS,
                    rate=RATE, input=True,
                    frames_per_buffer=CHUNK)

print("Recording...")

frames = []
for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    frames.append(data)

print("Recording finished.")

# Stop and close stream
stream.stop_stream()
stream.close()
audio.terminate()

# Save recorded audio
wf = wave.open(OUTPUT_FILENAME, 'wb')
wf.setnchannels(CHANNELS)
wf.setsampwidth(audio.get_sample_size(FORMAT))
wf.setframerate(RATE)
wf.writeframes(b''.join(frames))
wf.close()

print(f"Audio saved as {OUTPUT_FILENAME}")

# Playback the recorded audio
import os
print("Playing back the recorded audio...")
os.system(f"aplay {OUTPUT_FILENAME}")  # Works on Raspberry Pi
