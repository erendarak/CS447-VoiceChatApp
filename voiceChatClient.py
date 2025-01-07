import socket
import threading
import pyaudio
import sys
import time
from collections import deque
import queue
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

HOST = "63.176.94.180"
PORT = 5000

FORMAT = pyaudio.paInt16
CHUNKS = 4096
CHANNELS = 1
RATE = 44100

output_streams = {}  # user_id -> (pyaudio_instance, output_stream) (gelen her bir ses)
my_client_id = None
stop_audio_threads = False

jitter_buffers = {}   # user_id -> deque of audio chunks
playback_threads = {}  # user_id -> thread

BUFFER_FILL_THRESHOLD = 2

command_queue = queue.Queue()  # user input for gui

class GUIConsole(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("VoiceChatClient GUI")
        self.text_area = ScrolledText(self, wrap=tk.WORD, width=80, height=20)
        self.text_area.pack(padx=5, pady=5)
        input_frame = tk.Frame(self)
        input_frame.pack(fill=tk.X, padx=5, pady=(0,5))
        self.entry = tk.Entry(input_frame)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        enter_button = tk.Button(input_frame, text="Enter", command=self.on_enter_pressed)
        enter_button.pack(side=tk.LEFT, padx=5)
        self.text_area.config(state=tk.DISABLED)

    def on_enter_pressed(self):
        user_input = self.entry.get().strip()
        if user_input:
            command_queue.put(user_input)
        self.entry.delete(0, tk.END)

    def gui_print(self, msg):
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, msg + "\n")
        self.text_area.config(state=tk.DISABLED)
        self.text_area.see(tk.END)

def gui_print(msg):
    global app
    app.gui_print(msg)

def get_input():
    return command_queue.get()

def connect_to_server():
    client = socket.socket()
    client.connect((HOST, PORT))
    welcome_message = client.recv(4096).decode('utf-8')
    return client, welcome_message

def choose_room(client):
    while True:
        gui_print("Type an existing room name to join, 'NEW:<RoomName>' to create a new room, or 'q' to quit:")
        choice = get_input()
        if choice.lower() == 'q':
            client.shutdown(socket.SHUT_RDWR)
            client.close()
            sys.exit(0)
        client.send(choice.encode('utf-8'))
        response = client.recv(4096).decode('utf-8')
        gui_print(response)
        if "Joined room:" in response:
            return True
        elif "Disconnecting" in response:
            client.close()
            return False

def ensure_output_stream(user_id):
    if user_id not in output_streams:
        p = pyaudio.PyAudio()
        out_stream = p.open(format=FORMAT,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True,
                            frames_per_buffer=CHUNKS)
        output_streams[user_id] = (p, out_stream)
    if user_id not in jitter_buffers:
        jitter_buffers[user_id] = deque()
    if user_id not in playback_threads:
        t = threading.Thread(target=playback_thread_func, args=(user_id,))
        t.daemon = True
        t.start()
        playback_threads[user_id] = t

def playback_thread_func(user_id):
    global stop_audio_threads
    _, out_stream = output_streams[user_id]
    buffer = jitter_buffers[user_id]
    while not stop_audio_threads and len(buffer) < BUFFER_FILL_THRESHOLD:
        time.sleep(0.01)
    while not stop_audio_threads:
        if len(buffer) > 0:
            chunk = buffer.popleft()
            out_stream.write(chunk)
        else:
            silence = b'\x00' * (CHUNKS * 2)
            out_stream.write(silence)
            time.sleep(0.01)

def play_audio_data_for_user(user_id, audio_data):
    ensure_output_stream(user_id)
    jitter_buffers[user_id].append(audio_data)

def parse_server_messages(client):
    global stop_audio_threads, my_client_id
    f = client.makefile('rb')
    while not stop_audio_threads:
        try:
            header_line = f.readline()
            if not header_line:
                break
            header_line = header_line.strip()
            if header_line.startswith(b"DATA:"):
                parts = header_line.decode('utf-8').split(':')
                if len(parts) == 3:
                    _, sender_id_str, length_str = parts
                    sender_id = int(sender_id_str)
                    length = int(length_str)
                    audio_data = f.read(length)
                    if not audio_data or len(audio_data) < length:
                        break
                    play_audio_data_for_user(sender_id, audio_data)
            else:
                line_str = header_line.decode('utf-8')
                if line_str:
                    gui_print(line_str)
        except Exception as e:
            gui_print(f"Error receiving server messages: {e}")
            break

def audio_sender(client, input_stream):
    global stop_audio_threads
    while not stop_audio_threads:
        try:
            data = input_stream.read(CHUNKS, exception_on_overflow=False)
            if data:
                client.send(data)
        except:
            break

def user_input_thread(client):
    global stop_audio_threads
    while not stop_audio_threads:
        command = get_input().lower()
        if command == "leave":
            break
    stop_audio_threads = True
    try:
        client.shutdown(socket.SHUT_RDWR)
    except:
        pass
    client.close()

def audio_streaming(client):
    global stop_audio_threads, output_streams, jitter_buffers, playback_threads
    stop_audio_threads = False
    p = pyaudio.PyAudio()
    input_stream = p.open(format=FORMAT,
                          channels=CHANNELS,
                          rate=RATE,
                          input=True,
                          frames_per_buffer=CHUNKS)
    t_send = threading.Thread(target=audio_sender, args=(client, input_stream))
    t_recv = threading.Thread(target=parse_server_messages, args=(client,))
    t_input = threading.Thread(target=user_input_thread, args=(client,))
    t_send.start()
    t_recv.start()
    t_input.start()
    t_send.join()
    t_recv.join()
    t_input.join()
    for uid, t in playback_threads.items():
        if t.is_alive():
            t.join()
    playback_threads.clear()
    for uid, (pa, out_stream) in output_streams.items():
        out_stream.stop_stream()
        out_stream.close()
        pa.terminate()
    output_streams.clear()
    jitter_buffers.clear()
    input_stream.stop_stream()
    input_stream.close()
    p.terminate()

def main():
    while True:
        try:
            client, welcome_message = connect_to_server()
            gui_print(welcome_message)
            joined = choose_room(client)
            if not joined:
                continue
            audio_streaming(client)
        except SystemExit:
            sys.exit(0)
        except Exception as e:
            gui_print(f"Connection error: {e}")
            time.sleep(2)

def run_client():
    client_thread = threading.Thread(target=main, daemon=True)
    client_thread.start()

if __name__ == "__main__":
    app = GUIConsole()
    run_client()
    app.mainloop()
