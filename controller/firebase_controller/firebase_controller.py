import firebase_admin
from firebase_admin import credentials, firestore, storage
from google.api_core.exceptions import DeadlineExceeded
import requests.exceptions
from google.cloud import exceptions
from controller import utils
from controller import ethernet_controller

import os
import time
import json 

# global thisAppVersion

# 현재 스크립트 파일의 절대 경로를 얻음
script_dir = os.path.dirname(os.path.abspath(__file__))

# Firebase 인증 키 파일의 절대 경로
key_file_path = os.path.join(script_dir, "credentials_certificate/파일명파일명파일명")

# credentials.Certificate() 메서드에 절대 경로로 전달
cred = credentials.Certificate(key_file_path)

# Firebase 프로젝트의 서비스 계정 키 경로 설정
# cred = credentials.Certificate("credentials_certificate/파일명파일명파일명")
firebase_admin.initialize_app(cred,{
    "storageBucket": "grow-maps-platform.appspot.com"
})

# Firestore 클라이언트 초기화
db = firestore.client()

# brickDevices 컬렉션에 대한 참조 생성
brick_devices_collection = db.collection("brickDevices")

def add_deviceData(gatewayDevice, tagDeviceList, anchorDeviceList):
    print(f'TransmitDataToServer: {gatewayDevice.serialNumber} Gateway -> {len(tagDeviceList)}EA Tag, {len(anchorDeviceList)}EA Anchor')

    # max_retries = 3
    # retries = 0
    # while retries < max_retries:
    try:
        # Firestore 문서에 연결
        device_ref = brick_devices_collection.document(gatewayDevice.serialNumber).collection("gatewayData").document()
        tagDataJson = json.JSONDecoder().decode(json.dumps([tagDevice.__dict__ for tagDevice in tagDeviceList], cls=utils.EnumEncoder, indent=1))
        anchorDataJson = json.JSONDecoder().decode(json.dumps([anchorDevice.__dict__ for anchorDevice in anchorDeviceList], cls=utils.EnumEncoder, indent=1))
        for element in tagDataJson :
            element.pop('serialNumber', None)
            element.pop('areaUid', None)
            element.pop('deviceType', None)
            element.pop('rssi', None)
        for element in anchorDataJson :
            element.pop('serialNumber', None)
            element.pop('areaUid', None)
            element.pop('deviceType', None)
            element.pop('accuracy', None)
        device_ref.set({
            'areaUid' : gatewayDevice.areaUid,            
            'dataList' : tagDataJson,
            'anchorList' :  anchorDataJson,
            'time' : time.time()
        })
        # print("TagData update.")
        # break  # 성공했으므로 루프 종료
    except (DeadlineExceeded, requests.exceptions.Timeout):
        # Timeout 예외가 발생한 경우 재시도
        print(f"Connection Timeout. Retrying...")        
        time.sleep(2)  # 일정 시간 대기 후 재시도
    except Exception as e:
        # 다른 예외가 발생한 경우
        # case 1 공장초기화 상태로 firestore 에 설정이 안되어있을 때 404 에러가 나옴
        # 설정이 될때까지 계속 while 문을 나갈 수 없음.
        print(f"deviceData Update > Exception: {e}")
        time.sleep(2)  # 일정 시간 대기 후 재시도


def add_serviceLogData(gatewayDevice, service):
    try:        
        # 현재 연결된 네트워크 IP 
        connectedNetworkData = ethernet_controller.GetCurrentlyConnectedNetwork()        
        networkData = json.JSONDecoder().decode(json.dumps([element.__dict__ for element in connectedNetworkData], cls=utils.EnumEncoder, indent=1))
        # print(f'networkData {networkData}')
        # Firestore 문서에 연결
        device_ref = brick_devices_collection.document(gatewayDevice.serialNumber).collection("serviceStatus").document("service")
        device_ref.set({
            'service' : service,
            'time' : time.time(),
            'networkData' : networkData
        })
    except (DeadlineExceeded, requests.exceptions.Timeout):
        # Timeout 예외가 발생한 경우 재시도
        print(f"Connection Timeout. Retrying...")
        time.sleep(1)  # 일정 시간 대기 후 재시도
    except Exception as e:
        print(f"deviceData Update > Exception: {e}")            
        time.sleep(1)  # 일정 시간 대기 후 재시도
        
def add_statusCodeLogData(gatewayDevice, status_code):        
    try:
        # Firestore 문서에 연결
        device_ref = brick_devices_collection.document(gatewayDevice.serialNumber).collection("serviceStatus").document("statusCode")
        device_ref.set({
            'statusCode' : status_code,
            'time' : time.time()
        })
    except (DeadlineExceeded, requests.exceptions.Timeout):
        # Timeout 예외가 발생한 경우 재시도
        print(f"Connection Timeout. Retrying...")
        time.sleep(1)  # 일정 시간 대기 후 재시도
    except Exception as e:
        print(f"deviceData Update > Exception: {e}")            
        time.sleep(1)  # 일정 시간 대기 후 재시도