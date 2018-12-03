from socket import *
import time
import os

def createServer():
    serversocket = socket(AF_INET, SOCK_STREAM)
    try :
        serversocket.bind(('localhost', 8080))
        serversocket.listen(5)
        while(1):
            (clientsocket, address) = serversocket.accept()

            rd = clientsocket.recv(5000).decode()
            pieces = rd.split("\n")
            if ( len(pieces) > 0 ) : print(pieces[0])

            data = "HTTP/1.1 200 OK\r\n"
            data +="Date: " + str(time.strftime("%c"))
            data += "Content-Type: text/html; charset=utf-8\r\n"
            data += "Last-Modified: " + str(os.stat("test.py").st_mtime)
            data += "\r\n"
            data += "<html><body>Hello World</body></html>\r\n\r\n"
            print(data)
            clientsocket.sendall(data.encode())
            clientsocket.shutdown(SHUT_WR)

    except KeyboardInterrupt :
        print("\nShutting down...\n")
    except Exception as e :
        print("Error:\n")
        print(e)

    serversocket.close()

print('Access http://localhost:8080')
createServer()
