import socket
import argparse
import threading
import sys
import hashlib
import time
import logging
import random
import os
import pprint as p
import traceback

#function to help with logging
def log(logger, name, lst):
    message = name + ','
    for word in lst:
        message += str(word) + ','
    message = message[:-1]
    logger.info(message)
    
def makeMessage(lst) -> str:
    message = ''
    for word in lst:
        message += str(word) + ','
    message = message[:-1]
    return message
    

class P2PClient():
    
    def __init__(self, name, folder, myport) -> None:
        self.connectHost = 'localhost'
        self.trackerPort = 5100
        self.name = name
        self.folder = folder
        self.myport = int(myport)
        self.host = 'localhost'
        self.myChunks = {} # int index, file name
        self.hashFiles = {} 
        self.total = 0 #total int
        self.missingChunks = [] # indexes of missing chunks
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.sendSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.terminate = False
        
        
        
        logging.basicConfig(filename = "logs.log", format = "%(message)s", filemode="a")
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        self.logger = logger
        
    def connect(self):
        self.socket.connect((self.connectHost, self.trackerPort))

        #scan the folder to know what chunks we have
        self.folder_scan()
        
        #create hash signatures
        self.hash()

        #send info to P2P Tracker
        self.updateP2PTracker()
        
        # now - complicated threading.
        # should we start a thread for the "where chunks part, proceed one by one in that"
        # and a separate thread for listening to 'new connection requests?'
        
        #where Chunks can continue in a linear fashion, one by one until len(missing) = 0
        # reciever for new connection req and file transfers will start separately
        thread = threading.Thread(target=self.P2PRequest)
        thread.start()
        
        self.whereChunks()
        
        #check if we have any missing chunks
        
 
    def whereChunks(self):
        
        #if no chunks left tp discover, just let it be. Or should we leave server?
        if len(self.missingChunks) == 0:
            return
        
        #what if we location of chunk 1 is unknown, we should ask for another chunk
        
        while len(self.missingChunks) != 0:
            
            #check for first missing chunk index
            missing_chunk_index = self.missingChunks.pop(0)
            
            message = 'WHERE_CHUNK,' + str(missing_chunk_index)
            self.socket.send(message.encode())
            log(self.logger, self.name, [message])
            
            data = self.socket.recv(1024).decode()
            data = data.strip().split(',')
            
            #DEBUG
            print(data)
            
            if data[0] == 'GET_CHUNK_FROM':
                
                #DEBUG
                print("Inside GET_CHUNK_FROM")
                
                #The P2PClient is expected to randomly pick a P2PClient to connect to, from the given list
                # did not create a separate thread right now. 
                result = self.getChunkFromClient(data) # what if we fail - return False
                
                if result == False:
                     #DEBUG
                    print("COULD NOT GET CHUNK -- READDING TO LIST")
                    # TODO: should we be using mutex locks for updating a common variable?
                    self.missingChunks.append(missing_chunk_index)
                    print("Missing Chunks ", self.missingChunks)
                    time.sleep(3)
                    continue
                else:
                    #wait and continue for next missing chunk
                    print("sucess in getting chunk")
                    time.sleep(3)
                    continue
                    
            
            elif data[0] == 'CHUNK_LOCATION_UNKNOWN':
                #add chunk index to end of list and retry
                
                #DEBUG
                print("CHUNK_LOCATION_UNKNOWN")
                
                # TODO: should we be using mutex locks for updating a common variable?
                self.missingChunks.append(missing_chunk_index)
                print("Missing Chunks ", self.missingChunks)
                time.sleep(3)
                continue
            
    def getChunkFromClient(self, data: list()) -> bool:
        # joins a new connection to a client and gets the package
        # should be use a separate thread or not? Probably not - we can do this part in a sequence.
        
        chunk_index = int(data[1])
        file_hash = data[2]
        
        # The P2PClient is expected to randomly pick a P2PClient to connect to, from the given list
        rand_index = random.randrange(3, len(data), 2)
        IP_address = data[rand_index]
        port = int(data[rand_index + 1])
        
        # first get the file from another P2PClient
        '''
        The client makes a TCP connection with a peer P2PClient specified in the
        P2PTracker++’s response. It then requests for a specific file chunk using the command:
        REQUEST_CHUNK,<chunk_index>
        The peer P2PClient sends the contents of the file in response. The contents are sent as
        bytes without any further application layer headers. Note that the contents can arrive
        in more than one segment over the TCP connection. Therefore, keep reading from the
        TCP socket until the socket is closed by the peer sending the file.
        '''
        try:
            #print(1)
            requestSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            requestSocket.connect((IP_address, port))
            #print(2)
            
            command = 'REQUEST_CHUNK'
            message =  makeMessage([command, chunk_index])
            requestSocket.send(message.encode())
            log(self.logger, self.name, [message, IP_address, port])
            print(3)
            
            #start receiving endlessly
            file = b''
            while True:
                chunk_bits = requestSocket.recv(1024)
                if not chunk_bits:
                    break
                file += chunk_bits
            
            # close socket cause we done bro
            requestSocket.close()
            print(4)
            
            ### Not working ??###
            
            # What if file was recv incorrectly? Maybe we can calc Hash and see if it matches. If not, try again?
            # h = hashlib.sha1()
            # h.update(file)
            # hash_new_file = h.hexdigest()
            # if hash_new_file != file_hash:
            #     print("FILE HASH DID NOT MATCH")
            #     return False
            
            
            # now we write the file onto our folder
            filename = 'chunk_' + str(chunk_index)
            direc = os.path.join(self.folder, filename)
            with open(direc, 'wb') as f:
                f.write(file)
            print("File written")
                
            #should be update the local_chunks.txt?
            #TODO: GOTTA UPDATE A LOT OF LOCAL VARS
            self.myChunks[chunk_index] = filename
            self.hashFiles[chunk_index] = file_hash
            print("local vars updated")
            
            '''
            Finally, the P2PClient updates the P2PTracker++ with the new chunk it has, by executing the command:
            LOCAL_CHUNKS,<chunk_index>,<file_hash>,<IP_address>,<Port_number>
            '''
            command = 'LOCAL_CHUNKS'
            message = makeMessage([command, chunk_index, file_hash, self.host, self.myport])
            #message = command + str(chunk_index) + ',' + file_hash + ',' + self.host + ',' + str(self.myport)
            self.socket.send(message.encode())
            print("Tracker updated")
        except Exception as e:
            print("error")
            print(e)
            traceback.print_exc()
            return False
        
        return True
    			
    def hash(self): #Works
        for index, name in self.myChunks.items():
            h = hashlib.sha1()
            filename = os.path.join(self.folder, name)
            with open(filename, 'rb') as file:
                chunk = file.read()
                h.update(chunk)
            self.hashFiles[index] = h.hexdigest()
        
        # #DEBUG
        # p.pprint("Hash Method")
        # p.pprint(self.hashFiles)
			
    def updateP2PTracker(self): #Works
        command = 'LOCAL_CHUNKS'
        for index, hash in self.hashFiles.items():
            message = makeMessage([command, index, hash, self.host, self.myport])
            #message = command + str(index) + ',' + hash + ',' + self.host + ',' + str(self.myport)
            self.socket.send(message.encode())
            log(self.logger, self.name, [message])
            time.sleep(1)
            
    def P2PRequest(self):
        self.sendSocket.bind((self.host, self.myport))
        self.sendSocket.listen(5)
        print("Started listening")
        while True:
            client, addr = self.sendSocket.accept()
            print("Client connected ", addr)
            client_thread = threading.Thread(target = self.handle_connection, args=(client, addr))
            client_thread.start()
      
    def handle_connection(self, client, addr):
        
        data = str(client.recv(1024).decode())
        print(data) 
        data_vals = data.strip().split(',')
        
        if data_vals[0] == 'REQUEST_CHUNK':
                #now we gotta send that chunk
                filename = self.myChunks[int(data_vals[1])]
                file_path = os.path.join(self.folder, filename)
                
                print("Sending File to ", addr, file_path)
                command = "SENDING_FILE"
                log(self.logger, self.name, [command, data_vals[1], addr])
                with open(file_path, 'rb') as f:
                    file_contents = f.read()
                    client.sendall(file_contents)
                    
        else:
            print("Incorrect Request")
        
        client.close()
        #threading.current_thread().join()
        
    def folder_scan(self) -> None: # WORKS
        filename = os.path.join(self.folder, 'local_chunks.txt')
        with open(filename, 'r') as file:
            for line in file:
                data = line.strip().split(',')
                if data[1] == 'LASTCHUNK':
                    self.total = int(data[0])
                else:
                    self.myChunks[int(data[0])] = data[1]
        
        #calculate missing chunk indexes:
        for i in range(1, int(self.total) + 1, 1):
            if i not in self.myChunks.keys():
                self.missingChunks.append(i)
        
        #DEBUG
        print("Folder Scan")
        print("Total: " , self.total)
        print("Mychunks:" ,  self.myChunks)
        print("Missing Chunks: " , self.missingChunks)


if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="Create a Client Object")
	parser.add_argument("-folder", type=str, required=True)
	parser.add_argument("-transfer_port", type=str, required=True)
	parser.add_argument("-name", type=str, required=True)

	args = parser.parse_args()
	print("started")
	client = P2PClient(args.name, args.folder, args.transfer_port)
	client.connect()