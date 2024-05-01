import json
import socket
import subprocess
import time
import urllib

import requests
from controller.main_controller import *

def getCurEpochTime():
    return time.time()

def eth0ConfigSettings():
    try:
        ### eth0 설정 있는지 체크 ###
        command = 'nmcli --fields type connection show'
        result = subprocess.run(command, check=True, text=True, shell=True, capture_output=True)        
        
        # 결과에서 Ethernet이 있는지 확인
        if "ethernet" in result.stdout:
            print("Ethernet connection found.")
            return
        else:
            print("Ethernet connection not found.")
            command = 'sudo nmcli connection add type ethernet con-name Ethernet-conn-1 ifname eth0'
            subprocess.run(command, check=True, text=True, shell=True, capture_output=True)
            
            time.sleep(2)
            
            command = 'sudo nmcli connection up Ethernet-conn-1'
            subprocess.run(command, check=True, text=True, shell=True, capture_output=True)
            print(f'eth0 Settings successfully!')
            
    except subprocess.CalledProcessError as e:
        print(f'Failed to eth0 Settings. Error: {e}')

class EnumEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, DeviceType):
            return obj.name
        return json.JSONEncoder.default(self, obj)
    
    
def checkEthernetIsConnected():
    try:
        urllib.request.urlopen('http://google.com') #Python 3.x        
        return True
    except:
        return False

def isNetworkStatus():
    try:
        response = requests.get("http://www.google.com", timeout=5)
        # 응답 코드가 200(성공)인 경우에는 외부 인터넷이 연결되어 있음을 의미합니다.
        if response.status_code == 200:
            print(f"외부 네트워크 연결 상태: 연결됨 - {response.status_code}")
            return True
        else:
            print(f"외부 네트워크 연결 상태: 연결되지 않음 - {response.status_code}")
            return False
    except requests.ConnectionError as e:
        print(f"외부 네트워크 연결 상태: 연결되지 않음 - {e}")
        return False


