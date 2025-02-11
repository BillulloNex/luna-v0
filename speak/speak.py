import requests
import json
import nltk
import os
import subprocess
import time
import threading
import queue
from nltk.tokenize import sent_tokenize

# Check and download nltk data if needed
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

class TextToSpeechStreamer:
    def __init__(self, api_url="http://0.0.0.0:8848/api/v1/synthesise"):
        self.api_url = api_url
        self.headers = {'Content-Type': 'application/json'}
        self.synthesis_queue = queue.Queue(maxsize=5)  # Increased buffer size
        self.is_running = False
        self.current_index = 0
        self.total_sentences = 0
        
    def synthesize_sentence(self, sentence, index):
        """Convert a single sentence to speech"""
        try:
            payload = {"text": sentence.strip()}
            response = requests.post(
                self.api_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                output_file = f"temp_{index}.opus"
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                print(f"✓ Synthesized sentence {index + 1}/{self.total_sentences}")
                return output_file
            else:
                print(f"Error synthesizing speech: {response.status_code}")
                return None
        except Exception as e:
            print(f"Exception during synthesis: {e}")
            return None

    def play_audio(self, file_path):
        """Play the audio file using ffplay"""
        try:
            subprocess.run(
                ['ffplay', '-nodisp', '-autoexit', '-hide_banner', file_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except Exception as e:
            print(f"Error playing audio: {e}")
            return False

    def synthesis_worker(self, sentences):
        """Worker thread for synthesizing sentences"""
        for i, sentence in enumerate(sentences):
            if not self.is_running:
                break
            file_path = self.synthesize_sentence(sentence, i)
            if file_path:
                self.synthesis_queue.put((i, file_path))
        
        # Add sentinel value to indicate synthesis is complete
        self.synthesis_queue.put((-1, None))

    def playback_worker(self):
        """Worker thread for playing audio files"""
        played_files = set()
        next_index = 0
        sentinel_count = 0

        while self.is_running:
            try:
                index, file_path = self.synthesis_queue.get(timeout=1)
                
                # Check for sentinel value
                if index == -1:
                    sentinel_count += 1
                    if sentinel_count >= 1:  # Only one synthesis worker now
                        break
                    continue

                # Wait until it's this file's turn to play
                if index == next_index and file_path not in played_files:
                    print(f"► Playing sentence {index + 1}/{self.total_sentences}")
                    self.play_audio(file_path)
                    played_files.add(file_path)
                    os.remove(file_path)
                    next_index += 1
                else:
                    # Put it back in the queue if it's not time yet
                    self.synthesis_queue.put((index, file_path))
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in playback worker: {e}")

    def generate_continuous_speech(self, num_sentences=None):
        """Generate and play a continuous stream of sentences"""
        # Get the full text and split into sentences
        sentences = sent_tokenize(get_long_phrase())
        
        # If a specific number is requested, trim to that length
        if num_sentences and num_sentences < len(sentences):
            sentences = sentences[:num_sentences]
        
        self.total_sentences = len(sentences)
        print(f"\nPreparing to speak {self.total_sentences} sentences:")
        for i, sent in enumerate(sentences, 1):
            print(f"{i}. {sent}")
        
        print("\nStarting speech synthesis and playback...")
        self.is_running = True
        
        # Start playback worker
        playback_thread = threading.Thread(target=self.playback_worker)
        playback_thread.start()
        
        # Start synthesis worker (single thread for better coordination)
        synthesis_thread = threading.Thread(
            target=self.synthesis_worker,
            args=(sentences,)
        )
        synthesis_thread.start()
        
        # Wait for synthesis to complete
        synthesis_thread.join()
        
        # Wait for playback to finish
        playback_thread.join()
        
        self.is_running = False
        print("\nSpeech generation complete!")

def get_long_phrase():
    """Generate a long combined phrase"""
    return """
    The quick brown fox jumps over the lazy dog. This pangram contains every letter of the alphabet. 
    In a world of endless possibilities, sometimes the simplest solution is the best one. Let's test that theory. 
    Welcome to the future of text-to-speech! This is a test of voice synthesis quality and natural flow. 
    Here's a variety of sentences with different punctuation! How does it handle questions? Let's find out... 
    Testing, testing, 1-2-3. This is a microphone check, but for text-to-speech. How does it sound? 
    The weather is beautiful today. Birds are singing. Flowers are blooming. Spring has finally arrived. 
    Artificial intelligence continues to evolve. Each day brings new discoveries. The future looks promising. 
    Music fills the air with joy. Dancing brings happiness to life. Rhythm moves the soul in mysterious ways. 
    Ocean waves crash on distant shores. Seabirds soar overhead. The salty breeze refreshes the spirit. 
    Mountains reach toward cloudy skies. Valleys stretch far below. Nature's grandeur inspires awe.
    """

def test_continuous_speaker():
    """Test the continuous text-to-speech system"""
    streamer = TextToSpeechStreamer()
    streamer.generate_continuous_speech()

if __name__ == "__main__":
    test_continuous_speaker()
