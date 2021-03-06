


import network
import socket
import ure
import json
import machine
from acs712 import *


ap_ssid = "PyEnergy"
ap_password = "1234567890"

ap_authmode = 3  # WPA2
resposta_dicionario = {}

NETWORK_PROFILES = 'wifi.dat'

wlan_ap = network.WLAN(network.AP_IF)
wlan_sta = network.WLAN(network.STA_IF)

server_socket = None
user_email = None


def ler_dados():
    f = open("dados.txt", "r")
    contents = f.read()
    contents = contents.replace("\r","")
    contents = contents.replace("\n","")
    contents = contents.replace("\t","")
    return contents.split(",")


def salvar_dados(ssid, password, email,dispositivo):
    f = open("dados.txt", "w")
    f.write(ssid + "," + password + "," + email + ","+ dispositivo)
    f.close()


def do_connect(ssid, password):
    import time
    wlan_sta.active(True)
    wlan_ap.active(False)
    print('Trying to connect to %s...' % ssid)
    
    
    if (password == ""):
      print("Without password")
      wlan_sta.connect(ssid, )
    else:
      print("With password")
      wlan_sta.connect(ssid, password)
    
    for retry in range(200):
        connected = wlan_sta.isconnected()
        if connected:
            break
        time.sleep(0.1)
        print('.', end='')
    # if connected:
    print('\nConnected. Network config: ', wlan_sta.ifconfig)
    
    if not connected:
      f = open('dados.txt','w')
      f.__del__()
      f.close()
      machine.reset()
      
      
    
    # else:
    # print('\nFailed. Not Connected to: ' + ssid)
    return connected


def send_header(client, status_code=200, content_length=None):
    client.sendall("HTTP/1.0 {} OK\r\n".format(status_code))
    client.sendall("Content-Type:application/json\r\n")


    if content_length is not None:
        client.sendall("Content-Length: {}\r\n".format(content_length))
    client.sendall("\r\n")


def send_response(client, payload, status_code=200):
    content_length = len(payload)
    send_header(client, status_code, content_length)
    if content_length > 0:
        client.sendall(payload)
    client.close()


def handle_root(client, result):
    wlan_sta.active(True)
    ssids = sorted(ssid.decode('utf-8') for ssid, *_ in wlan_sta.scan())
    send_header(client)

    resposta_dicionario["resultado"] = result

    client.sendall(json.dumps(resposta_dicionario))

    client.close()


def stop():
    global server_socket

    if server_socket:
        server_socket.close()
        server_socket = None


def start(port=80):
    global server_socket

    if (False):
        print("ola")

    else:
        addr = socket.getaddrinfo('0.0.0.0', port)[0][-1]

        stop()

        wlan_ap.active(True)

        wlan_ap.config(essid=ap_ssid, password=ap_password, authmode=ap_authmode)
        
        print(wlan_ap.ifconfig)
        server_socket = socket.socket()
        server_socket.bind(addr)
        server_socket.listen(1)

        while True:
            if (wlan_sta.isconnected()):
                break

            client, addr = server_socket.accept()
            print('client connected from', addr)
            try:
                client.settimeout(5.0)

                request = b""
                try:
                    while "\r\n\r\n" not in request:
                        request += client.recv(512)
                except OSError:
                    pass

                print("Request is: {}".format(request))

                try:

                    dados = str(request).split("\\r\\n")[0].replace("b'GET /?", "").replace(" HTTP/1.1", "").split("&")
                    dados1 = dados[0].split("=")
                    dados2 = dados[1].split("=")
                    dados3 = dados[2].split("=")[1]
                    disp = dados[3].split("=")[1]
                except IndexError:
                    handle_root(client, "error")
                    return False

                    pass

                print(dados1[1], dados2[1], dados3)
                salvar_dados(dados1[1], dados2[1], dados3,disp)

                # if "HTTP" not in request:  # skip invalid requests
                # continue
                if (do_connect(str(dados1[1]), str(dados2[1]))):
                    handle_root(client, "ok")
                    time.sleep(2)
                    wlan_ap.active(False)
                else:
                  
                    handle_root(client, "error")
                    wlan_ap.active(False)
                    machine.reset()


            finally:
                client.close()

            return True



def postar_dados(email,dispositivo):
  import time
  import json
  from urequests import *
    
  email = email[:email.index('@')]
  
  date = "{}-{}-{}".format(machine.RTC().datetime()[2],machine.RTC().datetime()[1],machine.RTC().datetime()[0])
    
  if (machine.RTC().datetime()[5] < 10 and (machine.RTC().datetime()[4] - 3) > 10):
    time = "{}:0{}".format(machine.RTC().datetime()[4] - 3, machine.RTC().datetime()[5])
  if (machine.RTC().datetime()[5] < 10 and (machine.RTC().datetime()[4] - 3) < 10):
    time = "0{}:0{}".format(machine.RTC().datetime()[4] - 3, machine.RTC().datetime()[5])
  if (machine.RTC().datetime()[5] > 10 and (machine.RTC().datetime()[4] - 3) < 10):
    time = "0{}:{}".format(machine.RTC().datetime()[4] - 3, machine.RTC().datetime()[5])
  if (machine.RTC().datetime()[5] > 10 and (machine.RTC().datetime()[4] - 3)> 10):
    time = "{}:{}".format(machine.RTC().datetime()[4] - 3, machine.RTC().datetime()[5])

  
  tipo_dispositivo = dispositivo
   
  dicionario_pot = {}
    

  dicionario_pot["potencia"] = 155.56*getCurrentAC(5)
  
  print("http://micropython-1e299.firebaseio.com/"+email+"/"+tipo_dispositivo+"/"+date+"/"+time+"/.json")
  print("Json postado ->", dicionario_pot)
  try:
    request("PUT", "https://micropython-1e299.firebaseio.com/"+email+"/"+tipo_dispositivo+"/"+date+"/"+time+"/.json", data=json.dumps(dicionario_pot))
  except OSError:
    machine.reset()




from ntptime import *
lista_dados = ler_dados()

if (len(lista_dados) > 1):
    if (not do_connect(lista_dados[0], lista_dados[1])):

        print("Não conectou")
        
        if (start()):
            try:
              settime()  
            except OSError:
              machine.reset()
            
            while(True):
              if(wlan_sta.isconnected()):
                postar_dados(lista_dados[2],lista_dados[3])
              else:
                machine.reset()

    else: 
          try:
            settime()

          except OSError:
            machine.reset()
            
            
          while(True):
            if(wlan_sta.isconnected()):
              postar_dados(lista_dados[2],lista_dados[3])
            else:
              machine.reset()
else:
    start()









