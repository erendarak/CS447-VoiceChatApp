import socket
import threading

HOST = "0.0.0.0"
PORT = 5000

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(5)

rooms = {}
client_id_counter = 0
broadcast_lock = threading.Lock()

def start():
    print(f"Server started on {HOST}:{PORT}, waiting for connections...")
    while True:
        conn, addr = server.accept()
        t = threading.Thread(target=handle_new_connection, args=(conn,))
        t.start()

def handle_new_connection(conn):
    try:
        if rooms:
            room_list = "\n".join(rooms.keys())
        else:
            room_list = "No rooms available."
        welcome_msg = (
            "Available rooms:\n" +
            room_list +
            "\n\nType an existing room name to join it, "
            "or type 'NEW:<RoomName>' to create a new room:\n"
        )
        conn.send(welcome_msg.encode('utf-8'))

        room_choice = conn.recv(1024).decode('utf-8').strip()

        if room_choice.startswith("NEW:"):
            new_room_name = room_choice.split("NEW:")[-1].strip()
            if not new_room_name:
                conn.send(b"Invalid room name. Disconnecting.\n")
                conn.close()
                return
            if new_room_name not in rooms:
                rooms[new_room_name] = []
            room_choice = new_room_name

        if room_choice not in rooms:
            if room_choice == "":
                conn.send(b"No room chosen. Disconnecting.\n")
            else:
                msg = f"Room '{room_choice}' does not exist. Disconnecting.\n"
                conn.send(msg.encode('utf-8'))
            conn.close()
            return

        global client_id_counter
        client_id_counter += 1
        this_client_id = client_id_counter

        rooms[room_choice].append((conn, this_client_id))
        conn.send(f"Joined room: {room_choice}\n".encode('utf-8'))

        handle_client(conn, room_choice, this_client_id)

    except Exception as e:
        print("", e)
        conn.close()

def handle_client(conn, room_name, client_id):
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            with broadcast_lock:
                for cl, cl_id in rooms[room_name]:
                    if cl != conn:
                        header = f"DATA:{client_id}:{len(data)}\n".encode('utf-8')
                        cl.send(header + data)

    except Exception as e:
        print("", e)
    finally:
        if (conn, client_id) in rooms[room_name]:
            rooms[room_name].remove((conn, client_id))
        conn.close()

        if len(rooms[room_name]) == 0:
            del rooms[room_name]

        print(f"Client disconnected from room {room_name}")

start()
