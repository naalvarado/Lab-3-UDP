import socket
import sys
import concurrent.futures
import logging
import datetime
import os
import tqdm
import hashlib
import time

s = socket.socket()
HOST = "192.168.47.129"
PORT = 7777
FORMAT = 'utf-8'
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"


logs = os.path.exists("./Logs")
if not logs:
    os.makedirs("./Logs")

format = "%(asctime)s: %(message)s"
now = datetime.datetime.now()
logfile = "./Logs/" + str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "-" + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second) + ".log"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S", filename=logfile)

filesize = 0
fileName = ""

def getHashDigest(fileName):
    h = hashlib.sha1()

    with open(fileName, 'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(1024)
            h.update(chunk)
    
    return h.hexdigest()

def conn(tid):
    print("Comienza hilo: " + str(tid))
    client_socket = socket.socket()
    try:
        client_socket.connect((HOST,PORT))
    except socket.error as msg:
        print(msg)
        exit(1)
    logging.info("Conexion establecida con: " + str(HOST) + " en puerto: " + str(PORT) + " cliente " + str(tid))
    idClient = bytes(str(tid), FORMAT)
    client_socket.sendall(idClient)
    print("ID enviado")

    received = client_socket.recv(BUFFER_SIZE).decode()
    fName, fileSizeBytes = received.split(SEPARATOR)
    fileSizeBytes =int(fileSizeBytes)
    print(fName)
    print(fileSizeBytes)
    progress = tqdm.tqdm(range(fileSizeBytes), f"Receiving {fName}", unit="B", unit_scale=True, unit_divisor=1024)

    logs = os.path.exists("ArchivosRecibidos")
    if not logs:
        os.makedirs("ArchivosRecibidos")

    clientFileName = "ArchivosRecibidos/" + "Cliente" + str(tid) + "-Prueba-" + cons +".txt"

    start = time.time()
    with open( clientFileName, "wb+") as f:
        while True:
            bytes_read = client_socket.recv(BUFFER_SIZE)
            print(str(bytes_read.decode(FORMAT)))
            if str(bytes_read.decode(FORMAT)) == "FIN":
                break
            if not bytes_read:
                break
            
            f.write(bytes_read)
            
            progress.update(len(bytes_read))
    
    end = time.time()
    logging.info('TRANSFER TIME FOR CLIENT #{}: {}'.format(idClient, end-start))
    client_socket.sendall(bytes("ACK", FORMAT))
    hashDesc = client_socket.recv(1024).decode(FORMAT)
    realHash = getHashDigest(clientFileName)
    if hashDesc == realHash:
        logging.info("El hash corresponde para el cliente:" + str(tid))
    else:
        logging.info("El hash NO corresponde para el cliente:" + str(tid))
    client_socket.close()

if __name__ == "__main__":
    try:
        s.connect((HOST,PORT))
    except socket.error as msg:
        print(msg)
    print("Conexion establecida")
    logging.info("Conexion establecida con: " + str(HOST) + " en puerto: " + str(PORT))

    print("Que archivo quiere descargar?")
    print("1) 100Mb")
    print("2) 250Mb")
    fileCode = input()
    if fileCode == "1":
        fileName = "100MB.txt"
        filesize = 104857600
    elif fileCode == "2":
        fileName = "250MB.txt"
        filesize = 250000
    else:
        print("input no valido")
        exit(1)
    message = bytes(fileName, FORMAT)
    s.sendall(message)
    print("Numero de Conexiones: ")
    cons = input()
    message = bytes(cons, FORMAT)
    s.sendall(message)
    print("mensaje enviado")

    logging.info("Creando " + str(cons) + " clientes para descargar el archivo " + str(fileName))

    s.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(cons)) as executor:
        executor.map(conn, range(int(cons)))
