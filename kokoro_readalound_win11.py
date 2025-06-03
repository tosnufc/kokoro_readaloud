from kokoro import KPipeline
import soundfile as sf
import pyaudio
import numpy as np
import os
import re
import pyperclip

def preprocess_text(text):
    # Split text into sentences using common sentence endings
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    # Process each sentence
    processed_sentences = []
    for sentence in sentences:
        # Remove extra whitespace
        sentence = sentence.strip()
        if sentence:
            # Replace multiple spaces with single space
            sentence = re.sub(r'\s+', ' ', sentence)
            # Add sentence to list
            processed_sentences.append(sentence)
    
    # Join sentences with double newlines
    return '\n\n'.join(processed_sentences)

# Initialize TTS pipeline
pipeline = KPipeline(lang_code='a')

# Get text from clipboard
text = pyperclip.paste()
if not text:
    print("No text found in clipboard. Please copy some text and try again.")
    exit(1)

print("Original text from clipboard:")
print(text)
print("\nProcessing text...")

# Preprocess the text
processed_text = preprocess_text(text)
print("\nProcessed text:")
print(processed_text)
print("\nGenerating audio...")

# Create output directory
os.makedirs('Output_audio', exist_ok=True)

# Generate and save audio
generator = pipeline(processed_text, voice='af_heart')
all_audio_segments = []

# Collect all audio segments
for i, (gs, ps, audio) in enumerate(generator):
    print(f"Generating segment {i}: {gs}, {ps}")
    all_audio_segments.append(audio)

# Combine all segments into one audio array
combined_audio = np.concatenate(all_audio_segments)

# Save single audio file
output_path = 'Output_audio/output.wav'
sf.write(output_path, combined_audio, 24000)

# Play the combined audio file using PyAudio
p = pyaudio.PyAudio()
stream = p.open(format=pyaudio.get_format_from_width(2),  # 16-bit
                channels=1,
                rate=24000,
                output=True)

# Read the audio file
data, samplerate = sf.read(output_path)
audio_data = (data * 32767).astype(np.int16).tobytes()

# Play the audio
stream.write(audio_data)

# Clean up
stream.stop_stream()
stream.close()
p.terminate()