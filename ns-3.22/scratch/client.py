import socket

target_host = "7.2.0.3"
target_port = 9999

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((target_host, target_port))

while True:	
	response = client.recv(4096)
	print response
	client.send("hi")

client.close()
