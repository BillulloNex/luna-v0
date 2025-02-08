import sounddevice as sd
import soundfile as sf
import numpy as np
import subprocess
from datetime import datetime
import os
import threading
import queue

def record_audio(target_sample_rate=16000):
    """
    Record audio from Yeti microphone using sounddevice.
    Recording starts and stops with Enter key.
    
    Args:
        target_sample_rate (int): Desired sample rate in Hz
    """
    # List available devices
    devices = sd.query_devices()
    
    # Find Yeti device
    device_index = None
    for i, device in enumerate(devices):
        if "yeti" in device["name"].lower() and device["max_input_channels"] > 0:
            device_index = i
            break
    
    if device_index is None:
        raise Exception("Yeti microphone not found!")
    
    # Get device info
    device_info = sd.query_devices(device_index, 'input')
    default_sample_rate = int(device_info['default_samplerate'])
    print(f"Using device: {device_info['name']}")
    print(f"Default sample rate: {default_sample_rate} Hz")
    
    # Set the device
    sd.default.device = device_index
    
    # Create a queue for audio data
    q = queue.Queue()
    
    # Callback function to store audio data
    def callback(indata, frames, time, status):
        q.put(indata.copy())
    
    # Create an input stream
    stream = sd.InputStream(samplerate=default_sample_rate,
                          channels=1,
                          dtype=np.float32,
                          callback=callback)
    
    input("Press Enter to start recording...")
    
    # Start the recording
    recording = []
    with stream:
        print("* Recording... Press Enter to stop")
        input()  # Wait for Enter key
        
        # Get all remaining data from the queue
        while not q.empty():
            recording.extend(q.get())
    
    print("* Done recording")
    
    # Convert list to numpy array
    recording = np.concatenate(recording)
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recording_{timestamp}.wav"
    
    # If the recorded sample rate is different from target, resample
    if default_sample_rate != target_sample_rate:
        print(f"Resampling from {default_sample_rate}Hz to {target_sample_rate}Hz")
        from scipy import signal
        num_samples = round(len(recording) * float(target_sample_rate) / default_sample_rate)
        recording = signal.resample(recording, num_samples)
    
    # Convert to int16
    recording = (recording * 32767).astype(np.int16)
    
    # Save the recorded data as a WAV file
    sf.write(filename, recording, target_sample_rate)
    
    return filename

def transcribe_audio(wav_file):
    """
    Transcribe the audio file using the specified command.
    Deletes the WAV file after transcription.
    
    Args:
        wav_file (str): Path to the WAV file
    """
    command = f"taskset -c 4-7 python -m useful_transformers.transcribe_wav {wav_file}"
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        
        # Clean up the output
        output = result.stdout
        # Remove the tokens and tags
        output = output.replace("[50257, 50362]", "").strip()
        output = output.replace("<|startoftranscript|>", "").strip()
        output = output.replace("<|notimestamps|>", "").strip()
        
        # Delete the WAV file
        os.remove(wav_file)
        print(f"Deleted temporary file: {wav_file}")
        
        return output
    except subprocess.CalledProcessError as e:
        print(f"Error during transcription: {e}")
        # Delete the WAV file even if transcription fails
        if os.path.exists(wav_file):
            os.remove(wav_file)
            print(f"Deleted temporary file: {wav_file}")
        return None
    
def list_audio_devices():
    """Print all available audio devices."""
    print("\nAvailable audio devices:")
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        input_channels = device["max_input_channels"]
        if input_channels > 0:  # Only show input devices
            print(f"{i}: {device['name']} (Inputs: {input_channels})")
            if "default_samplerate" in device:
                print(f"   Default sample rate: {device['default_samplerate']} Hz")
    print()

def listen():
    # Show available devices
    list_audio_devices()
    
    try:
        wav_file = record_audio()
        print(f"Audio saved to: {wav_file}")
        
        print("Starting transcription...")
        transcription = transcribe_audio(wav_file)
        
        if transcription:
            print("Transcription:")
            print(transcription)
            return transcription
        else:
            print("Transcription failed")
            return  'No transcription found'
        
    except Exception as e:
        print(f"Error: {e}")
        return str(e)

# if __name__ == "__main__":
#     main()
