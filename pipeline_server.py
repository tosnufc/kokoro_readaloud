from kokoro import KPipeline
import socket
import pickle
import threading
import time
import struct
import warnings
import logging
import sys
import os
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

# Suppress all warnings
warnings.filterwarnings('ignore')

class PipelineServer:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port
        self.pipeline = None
        self.server_socket = None
        self.is_running = False
        logging.info(f"PipelineServer initialized with host={host}, port={port}")

    def initialize_pipeline(self):
        logging.info("Initializing Kokoro TTS pipeline...")
        try:
            self.pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
            logging.info("Pipeline initialized successfully!")
        except Exception as e:
            logging.error(f"Error initializing pipeline: {e}")
            raise

    def start_server(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(1)
            self.is_running = True
            logging.info(f"Pipeline server started on {self.host}:{self.port}")

            while self.is_running:
                try:
                    logging.info("Waiting for client connection...")
                    client_socket, address = self.server_socket.accept()
                    logging.info(f"Client connected from {address}")
                    client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    if self.is_running:
                        logging.error(f"Error accepting connection: {e}")
        except Exception as e:
            logging.error(f"Error starting server: {e}")
            self.shutdown()
            raise

    def send_data(self, sock, data):
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

    def receive_data(self, sock):
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

    def handle_client(self, client_socket):
        try:
            while True:
                logging.info("Waiting for client request...")
                request = self.receive_data(client_socket)
                if not request:
                    logging.warning("No request received from client")
                    break
                
                logging.info(f"Received request type: {request.get('type', 'unknown')}")
                if request['type'] == 'get_pipeline':
                    if self.pipeline is None:
                        logging.error("Pipeline not initialized")
                        response = {'status': 'error', 'message': 'Pipeline not initialized'}
                    else:
                        logging.info("Sending pipeline to client")
                        response = {'status': 'success', 'pipeline': self.pipeline}
                    self.send_data(client_socket, response)
                elif request['type'] == 'shutdown':
                    logging.info("Received shutdown request")
                    self.is_running = False
                    response = {'status': 'success', 'message': 'Server shutting down'}
                    self.send_data(client_socket, response)
                    break
        except Exception as e:
            logging.error(f"Error handling client: {e}")
        finally:
            try:
                client_socket.close()
                logging.info("Client connection closed")
            except:
                pass

    def shutdown(self):
        logging.info("Shutting down server...")
        self.is_running = False
        if self.server_socket:
            try:
                self.server_socket.close()
                logging.info("Server socket closed")
            except:
                pass

if __name__ == "__main__":
    server = PipelineServer()
    try:
        server.initialize_pipeline()
        server.start_server()
    except KeyboardInterrupt:
        logging.info("\nShutting down server...")
        server.shutdown()
    except Exception as e:
        logging.error(f"\nError: {e}")
        server.shutdown() 