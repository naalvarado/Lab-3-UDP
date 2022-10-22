from signal import signal, SIGPIPE, SIG_DFL
#Ignore SIG_PIPE and don't throw exceptions on it... (http://docs.python.org/library/signal.html)  
signal(SIGPIPE,SIG_DFL)   

import datetime, logging, socket, sys, threading, os, hashlib, time, tqdm
#"192.168.47.129"
HOST = "192.168.47.129"
PORT = 7777
FORMAT = 'utf-8'
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
print('Socket created')

#Bind socket 
try:
    s.bind((HOST, PORT))
except socket.error as msg:
    print ('Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1])
    sys.exit()
	
print ('Socket bind complete')

#Start listening on socket
#s.listen(10)
#print ('Socket now listening')

#Function for handling connections. This will be used to create threads
def clientthread(conn, fName):
    print("before id")
    # Identificacion del cliente de la conexion
    idClient, ad = s.recvfrom(1024)
    idClient = idClient.decode(FORMAT)
    print(idClient)

    # start sending the file
    fileSizeBytes = os.path.getsize(fName)
    s.sendto(f"{fName}{SEPARATOR}{fileSizeBytes}".encode(), ad)
    print(fName)
    print(fileSizeBytes)
    progress = tqdm.tqdm(range(fileSizeBytes), f"Sending {fName}", unit="B", unit_scale=True, unit_divisor=1024)
    print ("antesopen")
    with open(fName, "rb") as f:

        #Envio de archivo
        print("Empieza el envio")
        start = time.time()
        while True:
            # read the bytes from the file
            bytes_read = f.read(BUFFER_SIZE)
            if not bytes_read:
                s.sendto(bytes("FIN", FORMAT), ad)
                # file transmitting is done
                break
            # we use sendall to assure transimission in 
            # busy networks
            s.sendto(bytes_read, ad)
            # update the progress bar
            progress.update(len(bytes_read))

        logging.info('SENT {} WITH SIZE {}MB TO CLIENT #{}'.format(fName, str(fileSizeBytes/ (1024 * 1024)), idClient))
        print("FINALIZA ENVIO")

        end = time.time()

    print("TIEMPO TRANSF: " + str(end-start))
    #Calculo de tiempo de transferencia
    logging.info('TRANSFER TIME FOR CLIENT #{}: {}'.format(idClient, end-start))

    print("FIN CON CLIENT: " + str(idClient))
    #conn.close()

#Master client
fileName, ad = s.recvfrom(1024)
fileName = fileName.decode(FORMAT)
print("Archivo requerido " + str(fileName))
nClients, ad = s.recvfrom(1024)
nClients = int(nClients.decode(FORMAT))
#conn.close()

logs = os.path.exists("./Logs")
if not logs:
    os.makedirs("./Logs")

format = "%(asctime)s: %(message)s"
now = datetime.datetime.now()

logFileName = "./Logs/"+ "{}-{}-{}-{}-{}-{}.log".format(now.year, now.month, now.day, now.hour, now.minute, now.second)
logging.basicConfig(format=format, datefmt="%H:%M:%S", filename=logFileName, level=logging.INFO)

tList = []
#now keep talking with the client
print("antes del while")
print(str(nClients))
while nClients > 0:
    print(nClients)
    print("dentro del while")
    #wait to accept a connection - blocking call
    #conn, addr = s.accept()
    #print('Connected with ' + addr[0] + ':' + str(addr[1]))
    #logging.info('Connected with ' + addr[0] + ':' + str(addr[1]))

    #start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function.
    t = threading.Thread(target=clientthread, args=(ad, fileName))
    tList.append(t)

    nClients -= 1

for t in tList:
    t.start()

for t in tList:
    t.join()

s.close()
