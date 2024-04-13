import socket

def start_server():
    while True:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', 5001))
                s.listen()
                print("Server is listening on port 5001...")
                conn, addr = s.accept()
                with conn:
                    print('Connected by', addr)
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            print('Connection closed')
                            break
                        print(data.decode())
        except Exception as e:
            print(e)
            print('Error occurred, retrying...')

start_server()