from kokoro import KPipeline
import soundfile as sf
import simpleaudio as sa
import numpy as np
import os

# Initialize TTS pipeline
pipeline = KPipeline(lang_code='a')
text = """If we were to remove torch, the program would fail when trying to import and use the kokoro package. The kokoro library uses PyTorch internally for:
Neural network operations
Audio processing
Model inference
So while we don't see torch in our code, it's an essential dependency that we need to keep in the requirements file."""

# Create output directory
os.makedirs('Output_audio', exist_ok=True)

# Generate and save audio
generator = pipeline(text, voice='af_heart')
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

# Play the combined audio file
data, samplerate = sf.read(output_path)
audio_data = (data * 32767).astype(np.int16)
play_obj = sa.play_buffer(audio_data, 1, 2, samplerate)
play_obj.wait_done()

