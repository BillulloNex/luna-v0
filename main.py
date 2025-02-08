from hear.main import listen
from llm.luna import stream_luna
transcription = listen()

stream_luna(transcription=transcription)







