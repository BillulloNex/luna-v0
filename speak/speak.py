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


class StreamToSpeech:
    def __init__(self):
        self.sentence_queue = queue.Queue()
        self.tts_streamer = TextToSpeechStreamer()
        self.is_running = False
        self.speech_thread = None
    
    def process_stream_chunk(self, chunk):
        """Process a single chunk from the stream"""
        try:
            # Extract only the message content from the chunk
            if hasattr(chunk, 'message') and hasattr(chunk.message, 'content'):
                return chunk.message.content
            return ""
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return ""

    def accumulate_and_process_sentences(self, text_accumulator):
        """Process accumulated text into sentences"""
        # Only process if we have text to process
        if not text_accumulator.strip():
            return text_accumulator
            
        sentences = sent_tokenize(text_accumulator)
        
        # If we have complete sentences, process all but the last one
        if len(sentences) > 1:
            for sentence in sentences[:-1]:
                if sentence.strip():
                    self.sentence_queue.put(sentence.strip())
            # Return the last potentially incomplete sentence
            return sentences[-1]
        return text_accumulator

    def speech_worker(self):
        """Worker thread to process sentences and convert them to speech"""
        while self.is_running:
            try:
                # Get a sentence from the queue, wait up to 1 second
                sentence = self.sentence_queue.get(timeout=1)
                print(f"\nSpeaking: {sentence}")
                
                # Create temporary file for this sentence
                file_path = self.tts_streamer.synthesize_sentence(sentence, 0)
                if file_path:
                    self.tts_streamer.play_audio(file_path)
                    # Clean up the file
                    try:
                        os.remove(file_path)
                    except Exception as e:
                        print(f"Error removing temporary file: {e}")
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Error in speech worker: {e}")

    def start_speaking(self):
        """Start the speech worker thread"""
        self.is_running = True
        self.speech_thread = threading.Thread(target=self.speech_worker)
        self.speech_thread.start()

    def stop_speaking(self):
        """Stop the speech worker thread"""
        self.is_running = False
        if self.speech_thread:
            self.speech_thread.join()

    def process_stream(self, stream):
        """Process an input stream and convert to speech in real-time"""
        try:
            # Start the speech worker
            self.start_speaking()
            
            # Initialize text accumulator
            text_accumulator = ""
            
            # Process the stream
            for chunk in stream:
                if not chunk:
                    continue
                
                # Process the chunk
                content = self.process_stream_chunk(chunk)
                text_accumulator += content
                
                # If we have potential sentence endings, process them
                if any(punct in content for punct in '.!?'):
                    text_accumulator = self.accumulate_and_process_sentences(text_accumulator)
            
            # Process any remaining text
            if text_accumulator.strip():
                sentences = sent_tokenize(text_accumulator)
                for sentence in sentences:
                    if sentence.strip():
                        self.sentence_queue.put(sentence.strip())
            
            # Wait a bit to ensure all sentences are processed
            time.sleep(2)
            
        finally:
            # Clean up
            self.stop_speaking()

def example_usage():
    """Example of how to use the StreamToSpeech class"""
    # Create the speaker
    speaker = StreamToSpeech()
    
    # Example with your stream_luna2 function
    def stream_luna2(transcription):
        # Your existing stream_luna2 function here
        pass
    
    # Get the stream
    stream = stream_luna2("Tell me a story")
    
    # Process the stream
    speaker.process_stream(stream)

# Example of direct usage with your stream_luna2 function:
"""
from your_module import stream_luna2

speaker = StreamToSpeech()
stream = stream_luna2("Tell me a story")
speaker.process_stream(stream)
"""