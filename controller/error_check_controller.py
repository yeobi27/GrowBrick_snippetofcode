

import time
from controller.main_controller import ErrorType
from controller.serial_controller import getSerialEventChecker_aurs, setWriteSerialData
from controller.utils import checkEthernetIsConnected, getCurEpochTime


curErrorType =ErrorType.Waiting


global receiveAnchorTimeMillis
receiveAnchorTimeMillis = getCurEpochTime()
global receiveTagTimeMillis
receiveTagTimeMillis = getCurEpochTime()

ledReceiveTimeZoneLimit_Tag = 5      # 해당시간동안  tag 데이터 받지 않으면 LED Mode를 바꿈
ledReceiveTimeZoneLimit_Anchor = 300      # 해당시간동안 anchor데이터 받지 않으면 LED Mode를 바꿈


def updateAnchorTimeMillis():
    global receiveAnchorTimeMillis
    receiveAnchorTimeMillis =getCurEpochTime()

def updateTagTimeMillis():
    global receiveTagTimeMillis
    receiveTagTimeMillis =getCurEpochTime()


def errorCheckLoop():
    global ledReceiveTimeZoneLimit_Tag
    global receiveAnchorTimeMillis
    global receiveTagTimeMillis
    global curErrorType
    if ( abs(getCurEpochTime() - receiveAnchorTimeMillis) > ledReceiveTimeZoneLimit_Anchor) :
        curErrorType = ErrorType.NoUWBAnchorData
    elif ( abs(getCurEpochTime() - receiveTagTimeMillis) > ledReceiveTimeZoneLimit_Tag) :
        curErrorType = ErrorType.NoUWBTagData
    elif (checkEthernetIsConnected() == False):
        curErrorType = ErrorType.NoInternet
    else :
        curErrorType = ErrorType.Run
    print(f'LEDControlStateCheckLoop {curErrorType}')
    return curErrorType
        

def updateLEDModeToDeviceSerial():    
    global curErrorType
    retry_count = 0
    while True:
        if(curErrorType == ErrorType.NoUWBAnchorData):
            setWriteSerialData(value='aurs 2 2\r')
        elif(curErrorType == ErrorType.NoUWBTagData):
            setWriteSerialData(value='aurs 4 4\r')
        elif(curErrorType == ErrorType.NoInternet):
            setWriteSerialData(value='aurs 5 5\r')
        elif(curErrorType == ErrorType.Run):
            setWriteSerialData(value='aurs 3 3\r')
        else :
            setWriteSerialData(value='aurs 1 1\r')
        time.sleep(1)
        if( getSerialEventChecker_aurs() ):
            print(f'ChangeLEDMode Success {curErrorType}')
            break
        else :
            print('changeLEDMode Fail')
        retry_count = retry_count + 1
        if(retry_count > 10) :
            print('changeLEDMode Fail - Retry Max')
            break
