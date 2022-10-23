import socket
import sys
import concurrent.futures
import logging
import datetime
import os
import tqdm
import hashlib
import time
import select

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
HOST = "192.168.47.129"
PORT = 7777
FORMAT = 'utf-8'
BUFFER_SIZE = 4096
SEPARATOR = "<SEPARATOR>"
TIMEOUT = 3


logs = os.path.exists("./Logs")
if not logs:
    os.makedirs("./Logs")

format = "%(asctime)s: %(message)s"
now = datetime.datetime.now()
logfile = "./Logs/" + str(now.year) + "-" + str(now.month) + "-" + str(now.day) + "-" + str(now.hour) + "-" + str(now.minute) + "-" + str(now.second) + ".log"
logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S", filename=logfile)

fileName = ""

def conn(tid):
    print("Comienza hilo: " + str(tid))
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #client_socket.settimeout(2.0)
    try:
        client_socket.connect((HOST,PORT))
    except socket.error as msg:
        print(msg)
        exit(1)
    logging.info("Conexion establecida con: " + str(HOST) + " en puerto: " + str(PORT) + " cliente " + str(tid))
    idClient = bytes(str(tid), FORMAT)
    client_socket.sendto(idClient, (HOST,PORT))
    print("ID enviado")

    received = client_socket.recv(BUFFER_SIZE).decode()
    fName, fileSizeBytes = received.split(SEPARATOR)
    fileSizeBytes =int(fileSizeBytes)
    print(fName)
    print(fileSizeBytes)
    progress = tqdm.tqdm(range(fileSizeBytes), f"Receiving {fName}", unit="B", unit_scale=True, unit_divisor=1024)

    logs = os.path.exists("./ArchivosRecibidos")
    if not logs:
        os.makedirs("./ArchivosRecibidos")

    clientFileName = "./ArchivosRecibidos/" + "Cliente" + str(tid) + "-Prueba-" + cons +".txt"

    
    with open( clientFileName, "wb+") as f:
        start = time.time()
        while True:
            ready = select.select([client_socket], [], [], TIMEOUT)

            if ready[0]:
                bytes_read = client_socket.recv(BUFFER_SIZE)
                f.write(bytes_read)

                progress.update(len(bytes_read))
            else:
                end = time.time()
                newFileSize = os.path.getsize(clientFileName)
                if (fileSizeBytes == newFileSize):
                    logging.info('CLIENT # {}: {}->{}%'.format(idClient, 'TRANSFERENCIA COMPLETA (EXITOSA)', newFileSize*100/fileSizeBytes))
                else:
                    logging.info('CLIENT # {}: {}->{}%'.format(idClient, 'TRANSFERENCIA INCOMPLETA (NO EXITOSA)', newFileSize*100/fileSizeBytes))
                
                logging.info('TRANSFER TIME FOR CLIENT #{}: {}'.format(idClient, end-start))

                client_socket.close()    
                break
        
    
if __name__ == "__main__":

    print("Que archivo quiere descargar?")
    print("1) 100Mb")
    print("2) 250Mb")
    fileCode = input()
    if fileCode == "1":
        fileName = "100MB.txt"
    elif fileCode == "2":
        fileName = "250MB.txt"
    else:
        print("input no valido")
        exit(1)
    message = bytes(fileName, FORMAT)
    s.sendto(message, (HOST,PORT))
    print("Numero de Conexiones: ")
    cons = input()
    message = bytes(cons, FORMAT)
    s.sendto(message, (HOST,PORT))
    print("mensaje enviado")

    logging.info("Creando " + str(cons) + " clientes para descargar el archivo " + str(fileName))

    s.close()
    with concurrent.futures.ThreadPoolExecutor(max_workers=int(cons)) as executor:
        executor.map(conn, range(int(cons)))
