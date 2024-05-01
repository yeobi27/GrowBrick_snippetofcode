# !/usr/bin/env python3

"""
v2.0.0

"""

from controller.main_controller import *
import os
from parse import *
from controller import ble_controller
import time
import threading
from controller import serial_controller
import device_controller
from controller.firebase_controller import firebase_controller
from controller import utils
from controller import error_check_controller
from controller.main_controller import Service, StatusCode

arrangedAnchorList = []

def mainLoop():
    
    ### eth0 Config ###        
    utils.eth0ConfigSettings()
    
    print('SystemStart stable')
    serial_controller.main()

    # GatewayDevice의 초기 정보를 얻을 때 까지 작동함.
    device_controller.thisGatewayDevice = device_controller.initializeDevice()
    print(f'InitializeDevice Finished - {device_controller.thisGatewayDevice}')

    # 서비스 시작 로그
    if utils.checkEthernetIsConnected():
        firebase_controller.add_serviceLogData(gatewayDevice=device_controller.thisGatewayDevice, service=Service.Activing.value)
        firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.Normal.value)
    
    ## Serial Data를 Parsing 하는 부분 ###
    def threadSerialParsing(): 
        while True:
            try :
                device_controller.realTimeSerialParsing(thisGatewayDevice=device_controller.thisGatewayDevice)
            except BaseException as e:
                print(f'threadSerialParsing Error : {e}')
                if utils.checkEthernetIsConnected():
                    firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.ParsingError.value)
            time.sleep(0.01)
    threading.Thread(target=threadSerialParsing).start()


    ## Anchor Data 를 요청하는 부분 ####    
    def threadAnchorDataRequest():
        time.sleep(10)
        tries = 1
        maxtries = 10
        while True:
            try :
                for i in range(3):
                    device_controller.requestAnchorData()
                    time.sleep(1)
                    global arrangedAnchorList
                    arrangedAnchorList = device_controller.getAnchorDeviceData()
                    if(len(arrangedAnchorList)>0) :
                        break
                    time.sleep(3)
            except BaseException as e:
                print(f'threadAnchorDataRequest Error : {e}')
                if utils.checkEthernetIsConnected():
                    firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.AnchorError.value)                
            
            time.sleep(60)
            
            if not arrangedAnchorList:
                tries += 1
                if maxtries < tries:
                    print("reboot!")
                    if utils.checkEthernetIsConnected():
                        firebase_controller.add_serviceLogData(gatewayDevice=device_controller.thisGatewayDevice, service=Service.Inactive.value)
                        time.sleep(1)
                        firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.AnchorError.value)                    
                    time.sleep(1)
                    os.system("sudo reboot")
            else:
                tries = 0
                
    threading.Thread(target=threadAnchorDataRequest).start()



    ##Data 를 서버로 업로드 하는 부분 ####    
    def threadAddToServer():
        while True:
            try :
                global arrangedAnchorList
                firebase_controller.add_deviceData(gatewayDevice=device_controller.thisGatewayDevice, tagDeviceList=device_controller.getTagDeviceData(), anchorDeviceList=arrangedAnchorList)
            except BaseException as e:                
                print(f'threadAddToServer Error : {e}')
                if utils.checkEthernetIsConnected():
                    firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.DeviceDataUploadError.value)
            time.sleep(1)
    threading.Thread(target=threadAddToServer).start()

    ## BLE GATT 실행 부분 ####    
    def threadBLEGatt():
        ble_controller.main(device_controller.thisGatewayDevice)
        while True:
            try :
                ### BLE로 최신 정보를 get 할 수 있게 데이터를 1초에 한번씩 업데이트하여줌
                ble_controller.updateData(
                    device_controller.thisGatewayDevice, 
                )                
            except BaseException as e:
                print(f'threadBLEGatt Error : {e}')
                if utils.checkEthernetIsConnected():
                    firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.BLE_GATT_Error.value)
            time.sleep(1)
    threading.Thread(target=threadBLEGatt).start()

    ##LED를 Control 하는 부분 ####
    def threadErrorCheck():
        while True:
            try :
                exLEDMode = error_check_controller.curErrorType
                error_check_controller.errorCheckLoop()
                if(error_check_controller.curErrorType != exLEDMode) :
                    error_check_controller.updateLEDModeToDeviceSerial()
            except BaseException as e:                
                print(f'threadControlLED Error : {e}')
                if utils.checkEthernetIsConnected():
                    firebase_controller.add_statusCodeLogData(gatewayDevice=device_controller.thisGatewayDevice, status_code=StatusCode.LED_Check_Error.value)
            time.sleep(1)
    threading.Thread(target=threadErrorCheck).start()
    
if __name__ == '__main__':
    mainLoop()
    
