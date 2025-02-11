from hear.main import listen
from llm.luna import stream_luna2
from speak.speak import StreamToSpeech
speaker = StreamToSpeech()
transcription = listen()

stream = stream_luna2(transcription=transcription)

speaker.process_stream(stream)







