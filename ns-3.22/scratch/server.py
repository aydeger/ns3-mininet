import socket
import threading

bind_ip = "7.2.0.3"
bind_port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((bind_ip, bind_port))
server.listen(5)

print "[*] Listening on %s:%d" % (bind_ip, bind_port)

def handle_client(client_socket):

	while True:	
		client_socket.send("ACK!")
		request = client_socket.recv(1024)
		print "[*] Received: %s" % request

while True:
	client, addr = server.accept()
	print "[*] Accepted connection from: %s:%d" % (addr[0], addr[1])
	client_handler = threading.Thread(target = handle_client, args = (client,))
	client_handler.start()

server.close()
client.close()
