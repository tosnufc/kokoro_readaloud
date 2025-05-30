# Kokoro ReadAloud

This project provides a simple Text-to-Speech (TTS) script using the `kokoro` library. The script reads text from your clipboard, processes it, generates speech audio, and plays it back. It is designed for use on Arch Linux and has been tested on this platform.

## Features
- Reads text directly from your clipboard
- Preprocesses text for better TTS results
- Uses the `kokoro` TTS pipeline with a specified voice
- Saves the generated audio to a WAV file
- Plays the audio automatically after generation
- Runs efficiently on CPU-only systems (no GPU required)

Install all requirements with:
```bash
pip install -r requirements.txt
```

> **Note:** The code and requirements have been tested on Arch Linux. You may need to install system dependencies for audio playback and clipboard access.

## Usage
1. Copy any text you want to be read aloud to your clipboard.
2. Run the script:
   ```bash
   python kokoro_readalound.py
   ```
3. The script will:
   - Read the clipboard text
   - Preprocess and display it
   - Generate speech audio and save it to `Output_audio/output.wav`
   - Play the audio automatically

## How it works
- The script uses `pyperclip` to get text from the clipboard.
- It preprocesses the text (splitting into sentences, cleaning whitespace).
- The `kokoro.KPipeline` is used to generate audio segments for the text.
- All audio segments are concatenated and saved as a single WAV file.
- The audio is played using `simpleaudio`.

## License
MIT License

---

For more details, see the source code in [`kokoro_readalound.py`](kokoro_readalound.py). 