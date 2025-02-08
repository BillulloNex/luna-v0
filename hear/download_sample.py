import os
from datasets import load_dataset
import soundfile as sf

def download_audio_dataset(dataset_name, output_dir):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Load the dataset
    print(f"Loading dataset: {dataset_name}")
    ds = load_dataset(dataset_name)

    # Get the 'train' split (adjust if your dataset has different splits)
    train_data = ds['train']

    # Download audio files
    print("Downloading audio files...")
    for i, example in enumerate(train_data):
        # Get audio data
        audio_array = example['audio']['array']
        sampling_rate = example['audio']['sampling_rate']

        # Generate a filename
        filename = f"audio_sample_{i:04d}.wav"
        filepath = os.path.join(output_dir, filename)

        # Save the audio file
        sf.write(filepath, audio_array, sampling_rate)

        # Print progress
        if (i + 1) % 10 == 0:
            print(f"Downloaded {i + 1} files")

    print(f"Download complete. {len(train_data)} files saved to {output_dir}")

if __name__ == "__main__":
    # Dataset name
    dataset_name = "azain/LibriTTS-dev-clean-16khz-mono-loudnorm-100-random-samples-2024-04-18-17-34-39"

    # Output directory
    output_dir = "downloaded_audio"

    # Run the download function
    download_audio_dataset(dataset_name, output_dir)
