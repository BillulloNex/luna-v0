import sounddevice as sd
import opuslib
import numpy as np
import argparse
from pathlib import Path
from pyogg import OpusFile

def read_opus_file(file_path):
    """
    Read and decode an Opus file using pyogg.
    
    Args:
        file_path (str): Path to the Opus file
        
    Returns:
        numpy.ndarray: Decoded audio data
    """
    try:
        opus_file = OpusFile(file_path)
        
        # Get the raw audio data
        pcm_data = opus_file.as_array()
        
        # Convert to numpy array
        audio_data = np.array(pcm_data)
        
        return audio_data
        
    except Exception as e:
        raise Exception(f"Failed to decode Opus file: {e}")

def play_audio(audio_data, sample_rate=48000):
    """
    Play audio through default output device.
    
    Args:
        audio_data (numpy.ndarray): Audio data to play
        sample_rate (int): Sample rate of the audio (default: 48000)
    """
    try:
        # Normalize audio data to float between -1 and 1
        audio_float = audio_data.astype(np.float32) / 32768.0
        
        sd.play(audio_float, sample_rate)
        sd.wait()  # Wait until the audio is finished playing
    except sd.PortAudioError as e:
        print(f"Error playing audio: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    parser = argparse.ArgumentParser(description='Play Opus audio file through audio output')
    parser.add_argument('file_path', type=str, help='Path to the Opus file')
    args = parser.parse_args()
    
    file_path = Path(args.file_path)
    
    if not file_path.exists():
        print(f"Error: File '{file_path}' does not exist")
        return
    
    try:
        print(f"Reading file: {file_path}")
        audio_data = read_opus_file(str(file_path))
        
        print("Playing audio...")
        play_audio(audio_data)
        
    except Exception as e:
        print(f"Error processing file: {e}")

if __name__ == "__main__":
    main()