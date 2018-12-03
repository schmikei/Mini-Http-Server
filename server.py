import http, select, socket, time
import os,sys,traceback, signal

class Server:
    def __init__(self, port, docroot, logfile_name):
        self.port = port
        self.docroot = docroot
        self.logfile = logfile_name

        self.ip = ''
        self.http_socket =  socket.socket(socket.AF_INET, socket.SOCK_STREAM, \
        socket.IPPROTO_TCP)
        self.http_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            self.http_socket.bind((self.ip, self.port))
        except Exception as e:
            print('binding error:\n')
            print(e)

        #listening on socket
        self.http_socket.listen(5)

        #handler for ctrl-C
        signal.signal(signal.SIGINT, self.sighandler)

    #Here is the main method I think we should work on
    def serve(self):
        try:
            #inputready,outputready,exceptready = select.select(self.inputs, self.outputs, [])
            while(1):
                (clientsocket, address) = self.http_socket.accept()

                rd = clientsocket.recv(5000).decode()
                #some reason we are getting an empty string from Chrome? :(
                if rd is '':
                    continue
                pieces = rd.split("\n")
                headline = pieces[0]
                requested_file = headline.split(" ")[1]
                http_method = headline.split(" ")[0]
                #print out headline of message
                if ( len(pieces) > 0 ) : print(headline)

                if http_method == "GET":
                    #if it is a directory and not asking for the homepage
                    if os.path.isdir(self.docroot + requested_file) and requested_file != '/':
                        self.send_directory_contents(clientsocket, requested_file)
                    #otherwise treat it like a file, even if no file was indicated
                    else:
                        self.send_file(clientsocket, requested_file)
                else:
                    self.send_unimplemented(clientsocket)

        except KeyboardInterrupt:
            print("\nShutting down...\n")
            sys.exit(3)
        except Exception as e :
            print("Error:\n")
            traceback.print_exc()

        self.http_socket.close()

    def sighandler(self, signum, frame):
        print('Got a sigint, shutting down the server')
        self.http_socket.close()
        sys.exit(1)

    def send_directory_contents(self,clientsocket, requested_file):
        #Construct response when okay! 200
        response_hdr = "HTTP/1.1 200 OK\r\n"
        #date header
        response_hdr +="Date: " + str(time.strftime("%c"))
        response_hdr += "Content-Type: text/html; charset=utf-8\r\n"
        #last modified header
        response_hdr += "Last-Modified: " + str(os.stat(self.docroot+requested_file).st_mtime)
        response_hdr += "\r\n\r\n"

        #construct html for directory
        send_file = "<html><h2>Requested a directory. Here are the contents you can see: </h2>"
        send_file += "<li>".join([str(i)  for i in os.listdir(self.docroot + requested_file)])
        send_file +="+ </li></html>"
        send_file += "\r\n\r\n"

        #send the constructed file
        clientsocket.send(response_hdr.encode())
        clientsocket.send(send_file.encode())

    def send_file(self,clientsocket, requested_file):
        #default will direct them to the index.html!
        if requested_file == '/':
            #Construct response when okay! 200
            response_hdr = "HTTP/1.1 200 OK\r\n"
            #date header
            response_hdr +="Date: " + str(time.strftime("%c")+"\r\n")
            response_hdr += "Content-Type: text/html; charset=utf-8\r\n"
            #last modified header
            response_hdr += "Last-Modified: " + str(os.stat(self.docroot+requested_file).st_mtime)
            response_hdr += "\r\n\r\n"

            send_file = open(self.docroot + "/index.html", "r").read().encode() + b"\r\n\r\n"

            #send homepage!
            clientsocket.send(response_hdr.encode())
            clientsocket.send(send_file)
        else:
            #check if file exists and has permission
            if os.path.exists(self.docroot + requested_file):
                #Construct valid document when okay! 200
                response_hdr = "HTTP/1.1 200 OK\r\n"
                #date header
                response_hdr +="Date: " + str(time.strftime("%c"))

                #valid binary files
                if os.path.splitext(requested_file)[1] in {'.pdf', '.jpg', '.png', '.ico'}:
                    send_file = open(self.docroot + requested_file, "rb").read() + b"\r\n\r\n"
                    response_hdr += "Content-Type: jpg/png/ico/pdf;"
                #valid utf-8 encoded texts
                elif os.path.splitext(requested_file)[1]  in {'.txt', '.html'}:
                    send_file = open(self.docroot + requested_file, "r").read().encode() + b"\r\n\r\n"
                    response_hdr += "Content-Type: text/html; charset=utf-8"
                else: #unsupported file
                    response_hdr = "HTTP/1.1 501 Not Implemented\r\n"
                    response_hdr += "Content-Type: text/html; charset=utf-8\r\n"
                    response_hdr +="Date: " + str(time.strftime("%c"))
                    response_hdr += "\r\n\r\n"
                    send_file = "<html><h1>unsupported web view of this file</h1></html>".encode()

                #last modified header
                response_hdr += "Last-Modified: " + str(os.stat(self.docroot+requested_file).st_mtime)
                response_hdr += "\r\n\r\n"


                clientsocket.send(response_hdr.encode())
                clientsocket.send(send_file)
            #either the file is not there
            else:
                print("Cannot find: "+ requested_file)
                response_hdr = "HTTP/1.1 404 Not Found\r\n"
                response_hdr += "Content-Type: text/html; charset=utf-8\r\n"
                response_hdr +="Date: " + str(time.strftime("%c"))
                response_hdr += "\r\n\r\n"

                send_file = open(os.path.join(self.docroot, 'assets/404.html'), "r").read().encode() + b'\r\n\r\n'
                #send over 404 header
                clientsocket.send(response_hdr.encode())
                clientsocket.send(send_file)


    #for when we don't get the right http method
    def send_unimplemented(self, clientsocket):
        response_hdr = "HTTP/1.1 501 Not Implemented\r\n"
        response_hdr += "Content-Type: text/html; charset=utf-8\r\n"
        response_hdr +="Date: " + str(time.strftime("%c"))
        response_hdr += "\r\n\r\n"

        clientsocket.send(response_hdr.encode())




if __name__ == '__main__':
    import argparse
    #parsing for the arguments using the argparse package
    parser = argparse.ArgumentParser(prog='Web Server')
    parser.add_argument('-p', help='Port number for the server', type = int,  default = 8080)
    parser.add_argument('-docroot', help='Docstring for what the server\'s root is', default = '.')
    parser.add_argument('-logfile', help='A file for log messages to be written out', default = None)

    #unpacking them from the Argumentparser
    args = parser.parse_args()
    #initialize server
    S = Server(args.p, args.docroot, args.logfile)
    #run main method
    S.serve()
