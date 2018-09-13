import socket as s
import threading 
import Queue
import time
import struct 

def send_msg(sock, addr, msg):
    # Prefix each message with a 4-byte length (network byte order)
    msg = struct.pack('>L', len(msg)) + msg
    sock.sendto(msg.encode(), addr)

    print(msg)
    # sock.sendall(msg)

def recv_msg(sock):
    # Read message length and unpack it into an integer
    raw_msglen = recvall(sock, 4)
    if not raw_msglen:
        return None
    msglen = struct.unpack('>I', raw_msglen)[0]
    # Read the message data
    return recvall(sock, msglen)

def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = b''
    while len(data) < n:
       
        packet, addr = sock.recvfrom(n - len(data))
        if not packet:
            return None
        data += packet
    return data





class pupil_comms:

    def __init__(self, send_IP = '192.168.0.2', send_PORT = 5000, recv_IP = '192.168.0.1', recv_PORT = 5020, SIZE = 1024):
        """
        When you create an instance it will set up all the connections and send a test signal to the Eyetrike machine.
        

        To check the connection is live call self.send_msg("test"). Then sleep for half a second or so. Then call self.poll_msg(). This should return 'comms.online'
        
        
        args:
            send_IP: IP of machine you are sending requests to (Eyetrike)
            recv_IP: IP of machine running this code
        """

        self.send_IP = send_IP
        self.send_PORT = send_PORT

        self.recv_IP = recv_IP
        self.recv_PORT = recv_PORT

        self.SIZE = SIZE

        self.start_send_socket()
        self.start_recv_socket()
        
    def start_send_socket(self):

        self.send_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
        self.send_addr = (self.send_IP, self.send_PORT)

    def start_recv_socket(self):

        self.output_queue = Queue.Queue()

        self.recv_process = threading.Thread(target = message_receiver, args = (self.recv_IP, self.recv_PORT, self.output_queue, self.SIZE))
        self.recv_process.daemon = True

        self.recv_process.start()
        
    def send_msg(self, msg):

        # send_msg(self.send_sock, self.send_addr, msg.encode()) #Send the message using send protocol
        self.send_sock.sendto(msg.encode(), self.send_addr)

    def send_message_from_console(self):
        """Type messages over the console. 
        Enter q to close"""

        while True:
            msg = input("Type a command ")
           
            if msg == 'q':

                self.close_comms()

                return

            elif msg == 'poll':

                messages = self.poll_msg()

                print(messages)
                
            self.send_msg(msg)

    def poll_msg(self):
        """See if any messages have appeared in the message thread"""

    
        all_messages = []

        while not self.output_queue.empty():
       
            all_messages.append(self.output_queue.get())

           
       # print(all_messages)

        return all_messages

    def check_connection(self):
        """Check that we have communication with eyetrike"""


        #Check the connection is live
        time.sleep(0.5)
        self.send_msg('__test')
        time.sleep(0.5)

        self.send_msg('__time ' + str(time.time()))

        msg_recv = self.poll_msg()

        if 'comms.online' in msg_recv:

            return True
        
        else:

            return False

    def close_comms(self):
        """Close the communications down.

        Just joins the message thread"""

        self.recv_process.join(.01)

    def reset_time(self, timestamp):
        """Reset the timer on eyetrike"""

        self.send_msg('T ' + str(timestamp))

        print "reset timestamp to " + str(timestamp)        


    def start_trial(self, fname, timestamp = 0.00):
        """Start recording a new file on eyetrike"""

        #reset time with given timestamp
        print "reset timestamp"
        self.reset_time(timestamp)
        
        #start eyetracking recording
        self.send_msg('R ' + fname)
        
   
    def annotate(self, msg):
        """Tell eyetrike to annotate file with msg"""

        label = "A" + msg
        self.send_msg(label)


    def stop_trial(self):
        """Stop recording on eyetrike"""

        self.send_msg('r')

    def send_marker_positions(self, markers):        
        """Pass a list of markers (each markers are a list size 2) and send them to venlab remote"""

        message = '__'.join([str(item) for sublist in markers for item in sublist])

        message = 'markers:' + message

        self.send_msg(message)

 

def message_receiver(recv_IP, recv_PORT, output_queue, SIZE = 1024):

    """Recieve messages from a socket and flush the messages to a pipe"""

    
    recv_sock = s.socket( s.AF_INET, s.SOCK_DGRAM )
    recv_sock.bind((recv_IP, recv_PORT))

    recv_sock.setsockopt(s.SOL_SOCKET,s.SO_REUSEADDR,1)

    while True:

        # data = recv_msg(recv_sock)
        data, addr = recv_sock.recvfrom(SIZE)

        if data: 
            #decode message
            msg = data.decode('utf-8')

            output_queue.put(msg)
		



if __name__ == '__main__':

    #If networking
    # comms = pupil_comms()

    test_markers = [[5, 2], [6,20], [9,3]]
    #If debugging on eyetrike
    #comms = pupil_comms(send_IP = '0.0.0.0', send_PORT = 5000, recv_IP = '0.0.0.0', recv_PORT = 5020, SIZE = 1024)
    comms = pupil_comms()

    #Check the connection is live
    connected = comms.check_connection()

    

    if connected:

        comms.send_marker_positions(test_markers)

        # #Test in cosole
        # comms.send_message_from_console()        



    else:

        raise Exception("Not connected to comms")
    
    currtime = time.time()
    #comms.reset_time(currtime)
    comms.reset_time(0)

    polled = False
    while not polled:
        msgs = comms.poll_msg()
        if len(msgs) > 0:
            polled = True
            print (msgs)
    #print (comms.poll_msg())

    print('After poll: ' + str(time.time()))

    # comms.send_message_from_console()
    