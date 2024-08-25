import threading
import socket
import argparse
import os

class Server(threading.Thread):
    def __init__(self, host, port):
        super().__init__()
        self.connections = []
        self.host = host
        self.port = port
        self.running = True  # Flag to control the server's running state

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(1)
        print("Listening at", sock.getsockname())

        while self.running:
            try:
                sock.settimeout(1)  # Timeout to periodically check the running flag
                sc, sockname = sock.accept()
                print(f"Accepting a new connection from {sc.getpeername()} to {sc.getsockname()}")

                server_socket = ServerSocket(sc, sockname, self)
                server_socket.start()
                self.connections.append(server_socket)
                print("Ready to receive messages from", sc.getpeername())

            except socket.timeout:
                continue

        # Clean up: Close all connections and the socket
        print("Shutting down the server...")
        sock.close()
        for connection in self.connections:
            connection.sc.close()

    def broadcast(self, message, source):
        for connection in self.connections:
            if connection.sockname != source:
                try:
                    connection.send(message)
                except (ConnectionResetError, BrokenPipeError):
                    print(f"Connection to {connection.sockname} lost.")
                    connection.sc.close()
                    self.remove_connection(connection)

    def remove_connection(self, connection):
        self.connections.remove(connection)

    def stop(self):
        self.running = False


class ServerSocket(threading.Thread):
    def __init__(self, sc, sockname, server):
        super().__init__()
        self.sc = sc
        self.sockname = sockname
        self.server = server

    def run(self):
        while True:
            try:
                message = self.sc.recv(1024).decode('ascii')
                if message:
                    print(f"{self.sockname} says {message}")
                    self.server.broadcast(message, self.sockname)
                else:
                    print(f"{self.sockname} has closed the connection")
                    self.sc.close()
                    self.server.remove_connection(self)
                    return
            except (ConnectionResetError, BrokenPipeError):
                print(f"Connection to {self.sockname} lost.")
                self.sc.close()
                self.server.remove_connection(self)
                return

    def send(self, message):
        self.sc.sendall(message.encode('ascii'))


def exit_listener(server):
    while True:
        ipt = input("").strip().lower()
        if ipt == "q":
            server.stop()  # Stop the server thread
            break
    print("Server stopped.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Chatroom Server")
    parser.add_argument('host', help='Interface the server listens at')
    parser.add_argument('-p', metavar='PORT', type=int, default=1060, help='TCP port (default 1060)')

    args = parser.parse_args()

    server = Server(args.host, args.p)
    server.start()

    exit_thread = threading.Thread(target=exit_listener, args=(server,))
    exit_thread.start()

    # Wait for server and exit threads to finish
    server.join()
    exit_thread.join()

    print("Server program has exited.")
