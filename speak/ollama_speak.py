import threading
import queue
import time
import nltk
import os
from nltk.tokenize import sent_tokenize
from speak import TextToSpeechStreamer  # Import your existing TTS class

class StreamToSpeech:
    def __init__(self):
        self.sentence_queue = queue.Queue()
        self.tts_streamer = TextToSpeechStreamer()
        self.is_running = False
        self.speech_thread = None
    
    def process_stream_chunk(self, chunk):
        """Process a single chunk from the stream"""
        try:
            # Handle different types of chunks (dict with 'content' or direct string)
            if isinstance(chunk, dict) and 'message' in chunk:
                content = chunk['message']['content']
            else:
                content = 'none'
            
            return content
        except Exception as e:
            print(f"Error processing chunk: {e}")
            return ""

    def accumulate_and_process_sentences(self, text_accumulator):
        """Process accumulated text into sentences"""
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