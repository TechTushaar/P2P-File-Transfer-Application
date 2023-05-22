import socket
import argparse
import threading
import sys
import hashlib
import time
import logging
import pprint as p

#function to help with logging
def log(logger, lst):
    message = ''
    for word in lst:
        message += str(word) + ','
    message = message[:-1]
    logger.info(message)

class ChunkData():
    
    def __init__(self, chunk_index, file_hash, IP_address, Port_number) -> None:
        self.chunk_index = int(chunk_index)
        self.file_hash = file_hash
        self.IP_address = IP_address
        self.Port_number = int(Port_number)
        return
    
    def __eq__(self, other):
        if not isinstance(other, ChunkData):
            return False
        return (self.chunk_index == other.chunk_index and
                self.file_hash == other.file_hash and
                self.IP_address == other.IP_address and
                self.Port_number == other.Port_number)
		

class P2PTracker():
    
    listening_port = 5100
    hostname = "localhost"
    
    def __init__(self) -> None:
        
        self.check_list = {}
        self.chunk_list = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((P2PTracker.hostname, P2PTracker.listening_port))
        
        logging.basicConfig(filename = "logs.log", format = "%(message)s", filemode="a")
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        self.logger = logger
       
    def listen(self):
        self.socket.listen(5)
        
        print(f"Tracker started on port {self.listening_port}. Accepting connections")
        sys.stdout.flush()
        
        while True:
            client, addr = self.socket.accept()
            print(addr)
            #add these to dict?
            thread = threading.Thread(target = self.handle_connection, args=(client, addr))
            thread.start()
        
        self.socket.close()
    
    
    def handle_connection(self, client, addr):
        
        #add close connection logic
        while True:
            
            try:
                data = str(client.recv(1024).decode())
            
                if data == "":
                    continue
                
                #DEBUG
                print(data)
                
                data_vals = data.strip().split(',')
                
                if data_vals[0] == 'LOCAL_CHUNKS':  
                    
                    #store local_chunks data in object
                    chunk_index = int(data_vals[1])
                    chunk_data = ChunkData(data_vals[1], data_vals[2], data_vals[3], data_vals[4])
                    
                    #first add to check list, then scan check list for movement to chunk list
                    if chunk_index in self.check_list:
                        
                        #add to check list 
                        #check for repeats
                        if chunk_data in self.check_list[chunk_index]:
                            pass
                        else:
                            self.check_list[chunk_index].append(chunk_data)
        
                        #run a hash scan
                        self.scan(chunk_index)
                    else:
                        self.check_list[chunk_index] = [chunk_data]
                elif data_vals[0] == 'WHERE_CHUNK':
                    #handle where chunk
                    chunk_index = int(data_vals[1])
                    
                    if chunk_index in self.chunk_list:
                        #iterate through chunkData vals in chunk index key and create return message
                        message = ''
                        file_hash = self.chunk_list[chunk_index][0].file_hash
                        message = 'GET_CHUNK_FROM,' + str(chunk_index) + ',' + file_hash
                        for chunk in self.chunk_list[chunk_index]:
                            message += ',' + chunk.IP_address + ',' + str(chunk.Port_number)
                        
                        client.send(message.encode())
                        log(self.logger, ['P2PTracker', message])
                    else:
                        message = 'CHUNK_LOCATION_UNKNOWN,' + str(chunk_index)
                        client.send(message.encode())
                        log(self.logger, ['P2PTracker', message])
                
            except:
                err = "Connection closed with ", addr, " suddenly"
                print(err)
                log(self.logger, ['P2PTracker', err])
                client.close()
                break
                
            # # DEBUG
            # p.pprint(self.check_list)
            # p.pprint(self.chunk_list)
        
        
                        
          
    def scan(self, chunk_index : str):
        file_hash_dict = {}
        
        #v1 : move max file_hash matches to final list
        
        #generate number of types of file hashes
        for chunk in self.check_list[chunk_index]:
            
            if chunk.file_hash in file_hash_dict:
                file_hash_dict[chunk.file_hash] += 1
            else:
                file_hash_dict[chunk.file_hash] = 1
            
        #find max matching file hash
        final_file_hash, num = max(file_hash_dict.items(), key = lambda x: x[1])
        
        # Move to Chunk_list
        if num > 1:      
            self.chunk_list[chunk_index] = []
            
            for chunk in self.check_list[chunk_index]:
                if chunk.file_hash == final_file_hash:
                    self.chunk_list[chunk_index].append(chunk)
        return

        

if __name__ == "__main__":

    server = P2PTracker()

    server.listen()