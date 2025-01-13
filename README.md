# Voice Chat Application

## Project Overview
The Voice Chat Application was developed as part of the CS447 Computer Networks course. This project provides a platform for real-time voice communication using a client-server architecture. Users can create or join chat rooms, enabling seamless communication.

---

## Features
- **Real-Time Voice Communication**: Stream audio data in real-time with minimal latency.
- **Chat Room Management**: Create, join, and manage chat rooms.
- **User-Friendly Interface**: Simple and intuitive GUI for easy navigation.
- **Concurrent Audio Handling**: Supports multiple users communicating simultaneously.

---

## Technologies Used
- **Python** for the application logic.
- **socket**: Networking and communication.
- **pyaudio**: Audio streaming and processing.
- **threading**: Multi-threading for real-time operations.
- **AWS EC2**: Server hosting.

---

## System Architecture
The application uses a client-server model:

### Server
- Handles client connections.
- Manages chat room creation and closure.
- Broadcasts audio data to clients in the same room.

### Client
- Connects to the server.
- Streams audio to the server and processes received audio.
- Provides a GUI for user interaction.

---

## Installation and Usage
### Prerequisites
- Python 3.8 or later
- Required libraries: `pyaudio`, `socket`

Install dependencies using pip:
```bash
pip install pyaudio
```

### Running the Application
1. **Start the Server**
   Run the server script on an AWS EC2 instance or local machine:
   ```bash
   python server.py
   ```

2. **Start the Client**
   On the client machine, run:
   ```bash
   python client.py
   ```

3. **Interact with the Application**
   - Create a room: Type `NEW:<RoomName>` in the input bar.
   - Join a room: Select from the list of active rooms.
   - Leave a room: Type `leave` and press Enter.

---

## Key Components
### Client-Side
- **Audio Streaming**: Captures and streams audio using `pyaudio`.
- **Multi-Threading**: Manages sending and receiving audio concurrently.
- **Jitter Buffer**: Ensures smooth playback by handling network jitter.

### Server-Side
- **Client Management**: Accepts and manages multiple connections.
- **Audio Broadcasting**: Relays audio data to clients in a room.
- **Room Management**: Handles room creation, listing, and joining.

---

## Challenges and Solutions
- **Audio Latency**: Implemented a jitter buffer to minimize playback issues.
- **Server Load Management**: Optimized threading and socket communication.

---

## Results
- **Audio Quality**: Clear and consistent for up to 5 users.
- **Latency**: Maintained an acceptable range of 100-150ms.
- **Scalability**: Successfully managed multiple chat rooms and users.

---

## Future Enhancements
- **Scalability**: Optimize server for larger user loads.
- **Encryption**: Implement secure communication channels.
- **GUI Improvements**: Enhance user experience.

---

## Contributors
- **Ahmet Berkay Arslanpençe**
- **Eren Darak**
- **Ragıp Şamil Bekiryazıcı**
- **Kerem Okumuş**
- **Ömer Emre Bozkurt**

---

## Repository
Access the project on GitHub:
[Voice Chat Application Repository](https://github.com/OmerEmreBozkurt/VoiceChatApp)

---

## Contact
For any inquiries, feel free to contact the contributors through their GitHub profiles or email addresses.
