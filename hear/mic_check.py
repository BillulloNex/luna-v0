import pyaudio

p = pyaudio.PyAudio()
print(str(p.get_device_count()))
for i in range(1,p.get_device_count()):
    dev = p.get_device_info_by_index(i)
    if "USB" in dev['name']:
        print(f"Device {i}: {dev['name']}")
        print(f"  Max Input Channels: {dev['maxInputChannels']}")
        print(f"  Default Sample Rate: {dev['defaultSampleRate']}")
        print(f"  Supported Sample Rates: {dev['supportedSampleRates']}")

p.terminate()
