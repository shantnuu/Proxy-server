from base64 import b64encode
import time
import os
import threading
import thread
import socket 
import sys

lines = open('./proxy/blacklist.txt', "r").readlines()
blocked = []
authorized = []
for i in range(len(lines)):
    blocked = lines[i].replace('\n','')

afile = open('./proxy/auth.txt', "r")
lines = afile.readlines()
for i in range(len(lines)):
    temp = lines[i].replace('\n','')
    authorized.append(b64encode(temp))

requestCount = {}
nextCacheSlot = 0
cacheFileNames = {0: 'cache1.txt', 1:'cache2.txt', 2:'cache3.txt'}
cachedResponse = {}
requestTime = {}
cachedTime = {}

def timeheader(self,data, mtime):   

    lines = data.splitlines()
    while lines[len(lines)-1] == '':
        lines.remove('')
    header =  mtime
    header = "If-Modified-Since: " + header
    lines.append(header)

    data = "\r\n".join(lines) + "\r\n\r\n"
    return data

def doCache(request_tuple, response_cache, port, file_name, requestCount):
    milis = int(round(time.time() * 1000))
    request_tuple = (port,file_name)

    if request_tuple in requestCount.keys():
        if milis-requestTime[request_tuple]<30000:
            requestCount[request_tuple] += 1
        else:
            if requestCount[request_tuple] > 0:
                requestCount[request_tuple] = 1
                requestTime[request_tuple] = milis
    else:
        requestCount[request_tuple] = 1
        requestTime[request_tuple] = milis

    if requestCount[request_tuple] == 3:
        if len(cachedResponse.keys()) == 3:
            cachedResponse = {key:val for key, val in cachedResponse.items() if val != cacheFileNames[nextCacheSlot]}
        f = open(cacheFileNames[nextCacheSlot], 'w') 
        f.write(response_cache)
        
        cachedResponse[request_tuple] = cacheFileNames[nextCacheSlot] 
        cachedTime[request_tuple] = time.ctime(os.path.getmtime(cacheFileNames[nextCacheSlot]))
        nextCacheSlot += 1 
        nextCacheSlot = nextCacheSlot % 3 
        requestCount = {key:val for key, val in requestCount.items() if key != request_tuple}

        return

def butcher(data):
    data = data.splitlines()
    method= data[0].split(' ')[0]
    host = data[0].split('/')[2]
    port = host.split(':')[1]
    authtext = ''
    filename =  data[0].split('/')[3].split(' ')[0]
    if 'Basic' in data[2]:
        if len(data[2].split(': Basic ')) > 0:
            authtext = data[2].split(': Basic ')[1]
    return port,method,filename,authtext

def threader(client_socket, address, data, port, method, filename, authtext, blocked, authorized, requestCount):

    print port,method,file_name,authtext

    s_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s_socket.connect(('127.0.0.1', int(port)))
    request = data.replace('http://127.0.0.1:','')
    request = request.replace(port,'')
    s_socket.send(request) 

    request_tuple = (port,file_name)

    temp = s_socket.recv(1024)
    final =''
    i = 0
    if method == 'GET':
        if request_tuple in cachedResponse.keys() and '530' not in temp :
            final += temp
            while len(temp)>0 and temp!=' ':
                temp = server_socket.recv(1024)
                final += temp
            cacheFilename = cachedResponse[request_tuple]
            f = open(cacheFilename, 'r') 
            cacheFileContent = f.read()
            final = cacheFileContent
        else: 
            while len(temp)!=0 and temp!=' ':
                temp = s_socket.recv(1024)
                final += temp
                i += 1
            doCache(request_tuple, final, port, file_name, requestCount)

    else:
        while len(temp)!=0 and temp!=' ':
            temp = s_socket.recv(1024)
            final += temp
            i += 1

    client_socket.send(final)

    s_socket.close() 
    client_socket.close() 

psocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
psocket.bind(('', 20100))
psocket.listen(5)

while True:
    flag = 0
    client_socket, client_addr = psocket.accept()
    client_data = client_socket.recv(1024)
    print "Proxy Server listened", client_data

    port,method,file_name,authtext = butcher(client_data)

    if int(client_addr[1]) not in range(20000,20100):
        print("Only IIIT Allowed\n")
        client_socket.send("Only IIIT Allowed\n")
        flag=1 

    if int(port) not in range(20000,20201):
        print("Port out of range"),port
        client_socket.send("Port out of range")
        flag=1

    if str(port) in blocked and str(authtext) not in authorized:
        print("Authorization Error\n")
        client_socket.send("Authorization Error\n")
        flag=1
    
    if flag == 0:
        t1 = threading.Thread(target=threader, args=(client_socket, client_addr, client_data, port, method, file_name, authtext, blocked, authorized, requestCount))
        t1.start()
    else:
        continue







    
