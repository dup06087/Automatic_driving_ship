import time
import threading

from prac_client import Client

client = Client()
client_thread = threading.Thread(target=client.run)
client_thread.start()

while True:
    print("hello")
    time.sleep(1)