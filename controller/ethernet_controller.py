# -*- coding: utf-8 -*-
import codecs
import subprocess
from controller import utils

import network
import wifi
import socket
import requests
# import netifaces as ni
from subprocess import check_output
from controller.main_controller import Service, StatusCode, WiFiScanDTO
from controller.main_controller import NetworkInfoDTO
import device_controller
from controller.firebase_controller import firebase_controller
import time
import os
import json

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

def ConnectToWiFi(ssid, password):
    max_retries = 5
    try:
        print(f"ssid : {ssid} / type : {type(ssid)}")
        print(f"password : {password} / type : {type(password)}")
        
        # 네트워크 인터페이스를 활성화 한번하자
        command = 'sudo ifconfig wlan0 up'
        subprocess.run(command.split(' ') ,check=True)
        
        time.sleep(0.2)
        
        # Scan 을 한번 해주고 진입하자.
        # subprocess.run(['sudo', 'iwlist', 'wlan0', 'scan'], check=True)
        
        # time.sleep(2)
        # f'' type command is not running to split function
        command = f'sudo nmcli device wifi connect {ssid} password {password}'
        result = subprocess.run(command, check=True, text=True, shell=True, capture_output=True)
        
        retries = 0
        while retries < max_retries:
            print("Waiting for network connection...")

            if result.returncode is None:
                reset_running_log = f"Waiting for network connection...{retries}"
                print(reset_running_log)
                time.sleep(1)
            else:
                completed = f"Network connection completed with return code: {result.returncode}"
                print(completed)
                break
            retries += 1
        else:
            max_retries = "Max retries reached. Git reset did not complete."
            print(max_retries)        
            return
                
        print(f'Connected to {ssid} successfully!')
        
        if utils.checkEthernetIsConnected():            
            firebase_controller.add_serviceLogData(gatewayDevice=device_controller.thisGatewayDevice, service=Service.Activing.value)
            firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.Normal.value)
            print("Updated serviceLogData & statusCodeLogData!")
            
    except subprocess.CalledProcessError as e:
        print(f'Failed to connect to {ssid}. Error: {e}')

def GetIPAddress():
    ip = check_output(['hostname', '--all-ip-addresses'])
    print(ip)  # should print "192.168.100.37"
    return ip

def GetWiFiSSID():
    wifi = check_output(['iwgetid', '--raw', 'wlan0'], encoding='utf-8').strip()
    print(wifi)
    return wifi

# 라즈베리파이의 Scan List 를 가져온다.
def GetWiFiScanList():
    try:        
        command = "iwlist wlan0 scan | awk -F'[:=]+' '/ESSID/{essid=$2} /Signal level/{signal=$3; print essid \":\" signal}' | sort -t: -k2,2nr"
        
        result = subprocess.run(command, shell=True, capture_output=True)
        
        print(f'GetWiFiScanList 1 : {result}')
        
        if result == "" : return
        
        string_data = result.stdout.decode('euc-kr')

        # 추출된 값을 얻기        
        wifi_info_list = extract_wifi_info(string_data)
        
        print(f'GetWiFiScanList 2 : {wifi_info_list}')
        
        # 신호 세기 기반으로 정렬 #
        wifi_info_list.sort(key=lambda x: x.signal, reverse = True)
        
        # 길이를 자르기 (너무 기니까.. BLE로 다 못받아서 Json Parsing Error 가 발생해.. Android 에서 513번째 에서 Error 발생함 ) #
        max_char_len = 500
        filtered_info_list = []
        char_count = 0
        for wifi_info_data in wifi_info_list:
            char_count = char_count + len(json.dumps(wifi_info_data.__dict__))
            if(char_count < max_char_len) :
                filtered_info_list.append(wifi_info_data)
        
        return filtered_info_list
    except subprocess.CalledProcessError as e:
        print(f'Failed to GetWiFiScanList: {e}')
# wifi list의 원하는 필드만 추출해서 WiFiScanDTO 에 담고 리스트로 돌려주는 함수
def extract_wifi_info(text):

    lines = text.strip().split('\n')
    # 결과를 저장할 빈 리스트
    result_list = []

    # 각 줄을 파싱하여 딕셔너리로 저장하고 리스트에 추가
    for line in lines:
        parts = line.split(':')
        ssid = (decode_hex(parts[0].strip('"')))
        signal_level = parts[1].split('/')[0]
        
        # 여기서 result_list 에 넣고 signal_level 세기에 따른 정렬하기
        result_list.append(WiFiScanDTO(ssid=ssid, signal=signal_level))
        
    # signal_level을 기준으로 리스트 정렬
    # result_list.sort(key=lambda x: x.signal, reverse=True)
        
    return result_list

# 한글로 디코딩하는 함수
def decode_hex(encoded_text):
    try:
        # decoded_text = bytes.fromhex(encoded_text).decode('utf-8')
        decoded_text = codecs.decode(encoded_text, 'unicode_escape').encode('latin1').decode('utf-8')
        return decoded_text
    except (ValueError, UnicodeDecodeError):
        return encoded_text

# 현재 연결되어있는 IPAddress를 가져온다.
# 추가적으로 어떤 인터페이스인지도 추가하자.
def GetCurrentlyConnectedNetwork():
    try:
        # nmcli connection show --active
        # 무선, 유선 둘다 연결되있으면? 시간순에 따라 가장 최근에 연결된 네트워크부터 상단에 표기
        # 연결이 안되어있으면 안나옴
        command = "nmcli -t -f NAME,UUID,TYPE connection show --active"
        result_list = subprocess.run(command, shell=True, capture_output=True)
        string_data = result_list.stdout.decode('utf-8')
        
        if string_data == "": return
        
        networkDataList = []
        macAddress = ""
        
        lines = string_data.strip().split('\n')
        
        for line in lines:
            parts = line.split(':')
            name = parts[0]
            type = parts[2]
            command_get_ip = f"nmcli -g IP4.ADDRESS connection show {parts[1]}"
            result = subprocess.run(command_get_ip, shell=True, capture_output=True)
            time.sleep(0.1)
            ip = result.stdout.decode('utf-8').strip('\n')
            
            # 이때의 MAC Address 확인
            if "-wireless" in type:
                macAddress = getMACAddress("wlan0")
            elif "-ethernet" in type:
                macAddress = getMACAddress("eth0")
            
            networkDataList.append(NetworkInfoDTO(name=name, mac=macAddress, ip=ip, type=type))
            
        return networkDataList
        
    except subprocess.CalledProcessError as e:
        # 값이 없으면 나올듯
        print(f'Failed to GetCurrentlyActiveNetwork: {e}')
        
def getMACAddress(type):
    macAddress=""
    command_get_mac_address = f"ifconfig {type} | awk '/ether/ {{print $2}}'"
    result = subprocess.run(command_get_mac_address, shell=True, capture_output=True)
    time.sleep(0.1)
    macAddress = result.stdout.decode('utf-8').strip()
    # print(f"macAddress {macAddress}")
    return macAddress