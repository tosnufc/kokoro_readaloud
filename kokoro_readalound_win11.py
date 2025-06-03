import soundfile as sf
import pyaudio
import numpy as np
import os
import re
import pyperclip
import socket
import pickle
import struct
import warnings
import logging
import time
import sys
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

# Suppress all warnings
warnings.filterwarnings('ignore')

def send_data(sock, data):
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Save the data to the temporary file
            pickle.dump(data, temp_file)
            temp_file.flush()
            temp_file_path = temp_file.name

        try:
            # Get file size
            file_size = os.path.getsize(temp_file_path)
            logging.debug(f"Sending file of size: {file_size} bytes")

            # Send file size
            sock.sendall(struct.pack('>L', file_size))

            # Send file in chunks
            with open(temp_file_path, 'rb') as f:
                chunk_size = 1024 * 1024  # 1MB chunks
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    logging.debug(f"Sent {f.tell()}/{file_size} bytes")

            logging.debug("File sent successfully")
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    except Exception as e:
        logging.error(f"Error sending data: {e}")
        raise

def receive_data(sock):
    try:
        # Receive the size of the data first
        size_data = sock.recv(4)
        if not size_data:
            logging.warning("No size data received")
            return None
        size = struct.unpack('>L', size_data)[0]
        logging.debug(f"Received data size: {size}")

        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name

        try:
            # Receive the data in chunks and write to file
            with open(temp_file_path, 'wb') as f:
                received = 0
                chunk_size = 1024 * 1024  # 1MB chunks
                while received < size:
                    remaining = size - received
                    chunk = sock.recv(min(remaining, chunk_size))
                    if not chunk:
                        raise ConnectionError("Connection closed while receiving data")
                    f.write(chunk)
                    received += len(chunk)
                    logging.debug(f"Received {received}/{size} bytes")

            # Load the data from the file
            with open(temp_file_path, 'rb') as f:
                data = pickle.load(f)

            return data
        finally:
            # Clean up the temporary file
            try:
                os.unlink(temp_file_path)
            except:
                pass

    except Exception as e:
        logging.error(f"Error receiving data: {e}")
        return None

def get_pipeline_from_server(host='localhost', port=5000, max_retries=3, retry_delay=1):
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempting to connect to server (attempt {attempt + 1}/{max_retries})...")
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.settimeout(60)  # Increased timeout to 60 seconds
            client_socket.connect((host, port))
            logging.info("Connected to server successfully")
            
            # Request pipeline
            logging.info("Requesting pipeline from server...")
            request = {'type': 'get_pipeline'}
            send_data(client_socket, request)
            
            # Receive response
            logging.info("Waiting for server response...")
            response = receive_data(client_socket)
            client_socket.close()
            
            if response and response['status'] == 'success':
                logging.info("Successfully received pipeline from server")
                return response['pipeline']
            elif response and response['status'] == 'error':
                logging.error(f"Server error: {response.get('message', 'Unknown error')}")
            else:
                logging.error("Invalid response from server")
        except socket.timeout:
            logging.error(f"Connection attempt {attempt + 1} timed out")
        except ConnectionRefusedError:
            logging.error(f"Connection refused on attempt {attempt + 1}")
        except Exception as e:
            logging.error(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
        
        if attempt < max_retries - 1:
            logging.info(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            logging.error("All connection attempts failed.")
            logging.error("Please make sure the pipeline server is running.")
            exit(1)

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

# Get pipeline from server
logging.info("Connecting to pipeline server...")
pipeline = get_pipeline_from_server()
logging.info("Successfully connected to pipeline server")

# Get text from clipboard
text = pyperclip.paste()
if not text:
    logging.error("No text found in clipboard. Please copy some text and try again.")
    exit(1)

logging.info("Original text from clipboard:")
logging.info(text)
logging.info("Processing text...")

# Preprocess the text
processed_text = preprocess_text(text)
logging.info("Processed text:")
logging.info(processed_text)
logging.info("Generating audio...")

# Create output directory
os.makedirs('Output_audio', exist_ok=True)

# Generate and save audio
generator = pipeline(processed_text, voice='af_heart')
all_audio_segments = []

# Collect all audio segments
for i, (gs, ps, audio) in enumerate(generator):
    logging.info(f"Generating segment {i}: {gs}, {ps}")
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