import ollama

def ask_luna(transcription):
    try:
        # Single response
        response = ollama.chat(
            model='luna:latest',
            messages=[{
                'role': 'user',
                'content': transcription
            }]
        )
        return response['message']['content']
    except Exception as e:
        print(f"Error: {e}")
        return None

def stream_luna(transcription):
    try:
        # Streaming response
        stream = ollama.chat(
            model='luna:latest',
            messages=[{
                'role': 'user',
                'content': transcription
            }],
            stream=True
        )
        
        # Process the stream
        for chunk in stream:
            if 'message' in chunk:
                print(chunk['message']['content'], end='', flush=True)
        print()  # New line at end
            
    except Exception as e:
        print(f"Error: {e}")

# To collect the stream into a string:
def stream_luna_collect(transcription):
    full_response = []
    try:
        stream = ollama.chat(
            model='luna:latest',
            messages=[{
                'role': 'user',
                'content': transcription
            }],
            stream=True
        )
        
        for chunk in stream:
            if 'message' in chunk:
                token = chunk['message']['content']
                full_response.append(token)
                print(token, end='', flush=True)
        print()
        
        return ''.join(full_response)
        
    except Exception as e:
        print(f"Error: {e}")
        return None

def stream_luna2(transcription):
    stream = ollama.chat(
            model='luna:latest',
            messages=[{
                'role': 'user',
                'content': transcription
            }],
            stream=True
        )
    return stream
# Example usage:
# transcription = "Tell me a story"
# response = ask_luna(transcription)  # Single response
# stream_luna(transcription)          # Stream and print
# response = stream_luna_collect(transcription)  # Stream, print and collect