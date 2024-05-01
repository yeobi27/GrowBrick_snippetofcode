import time
from controller.error_check_controller import updateAnchorTimeMillis, updateTagTimeMillis

from controller.utils import *
from controller import serial_controller

from controller.main_controller import *
import time


global thisGatewayDevice

def initializeDevice():
    validateCheckCount = 0
    while (True):
        validateCheckCount = validateCheckCount + 1
        print(f'GatewayInfoValidateCheck - tryCount {validateCheckCount}')

        serial_controller.setWriteSerialData('a\r')
        time.sleep(0.1)
        serial_controller.setWriteSerialData('reset\r')
        time.sleep(2)
        serial_controller.setWriteSerialData('si\r')
        time.sleep(1)

        receivedData = parseGatewayDeviceFromReceiveData()
        if(gatewayInfoValidateChecker(receivedData) == True):
            print('GatewayDeviceValidate - True')
            serial_controller.setWriteSerialData('lep\r')
            return receivedData

def parseGatewayDeviceFromReceiveData():
    readedSerialNumber = ''
    readedPanID = ''
    for line in serial_controller.getReadSerialDataAll():
        lineData = line
        # if "GB:Type=" in lineData:
        #     DeviceTypeStr = lineData.split("GB:Type=")[1].replace("\r","").replace("\n","")
        # if "GB:ModelNo=" in lineData:
        #     ModelNumber = lineData.split("GB:ModelNo=")[1].replace("\r","").replace("\n","")
        # if "GB:Version=" in lineData:
        #     Version = lineData.split("GB:Version=")[1].replace("\r","").replace("\n","")
        if "GB:S/N=" in lineData:
            readedSerialNumber = lineData.split("GB:S/N=")[1].replace("\r","").replace("\n","")
        # if "GB:AuthKey=" in lineData:
        #     AuthKey = lineData.split("GB:AuthKey=")[1].replace("\r","").replace("\n","")
        if "panid=x" in lineData:
            readedPanID = '0x'+lineData.split("panid=x")[1].split(" ")[0]
        # if( (readedPanID != '')&(readedSerialNumber != '')):

    print(f"readedSerialNumber {readedSerialNumber}")
    print(f"readedPanID {readedPanID}")
    print(f"uwbID : {readedSerialNumber[18:].replace(':','')}")
    
    return DeviceDTO(
        serialNumber= readedSerialNumber,
        areaUid= readedPanID,
        deviceType=DeviceType.GATEWAY,
        uwbID=readedSerialNumber[18:].replace(':',''),
        posX=0,
        posY=0,
        posZ=0,
        accuracy=100,
        rssi=0,
        readTime=getCurEpochTime()
    )
    
def realTimeSerialParsing(thisGatewayDevice):
    # print('RealTimeSerialParsing')
    # 약 1초에 100번 도는동안, 읽을 lines이 있으면 읽어버림 ///
    # 정규식 패턴 설정
    # pattern = r"(\d+)\) id=(\w+) seat=(\w+) seens=(\w+) rssi=(-?\w+) cl=(\w+) nbr=(\w+) pos=([\d.]+):([\d.]+):([\d.]+)"
    # pattern = re.compile(r"id=(\d{12}).*rssi=(-?\d{1,2}).*pos=(-?\d+\.\d+:-?\d+\.\d+:-?\d+\.\d+)")
    # [000012.800 INF] 1) id=000000000000198B seat=6 seens=124 rssi=-82 cl=00000000 nbr=00000000 pos=0.01:0.01:0.01
    # [000012.800 INF] 3) id=0000000000008506 seat=8 seens=124 rssi=-86 cl=00000000 nbr=00000000 pos=3.00:0.00:0.00
    # [000012.800 INF] 5) id=0000000000000EB8 seat=2 seens=123 rssi=-89 cl=00000000 nbr=00000000 pos=3.00:-0.50:0.00
    
    for line in serial_controller.getReadSerialDataAll():
        lineData = line
        # 정규식 패턴이 느려서 시간안에 읽어오지 못함.
        parsedData = lineData.split()
        if len(parsedData) >= 9:            
            uwbID = parsedData[3]
            rssi_part = parsedData[6]
            pos_part = parsedData[-1]

            uwbID = uwbID[15:]
            rssi = rssi_part[5:]
            pos_values = pos_part.split(':')
            
            receiveAnchorDataBuf.append(
                DeviceDTO(
                    areaUid=thisGatewayDevice.areaUid,
                    deviceType=DeviceType.ANCHOR,
                    posX=float(pos_values[0][4:]),
                    posY=float(pos_values[1]),
                    posZ=float(pos_values[2]),
                    readTime=getCurEpochTime(),
                    serialNumber='',
                    accuracy=0,
                    rssi=rssi,
                    uwbID=uwbID
                )
            )
            if(len(receiveAnchorDataBuf) > 1000):
                receiveAnchorDataBuf.pop(0)

            updateAnchorTimeMillis()
        #     print(f'Matched : {uwbID} {rssi} {pos_values[0]}:{pos_values[1]}:{pos_values[2]}')
            
        # match = re.search(pattern, lineData)

        # if match :
        #     index = int(match.group(1))
        #     uwbID = match.group(2)[12:]            
        #     rssi = int(match.group(5))
        #     pos = [float(match.group(8)), float(match.group(9)), float(match.group(10))]
            
        #     receiveAnchorDataBuf.append(
        #         DeviceDTO(
        #             areaUid=thisGatewayDevice.areaUid,
        #             deviceType=DeviceType.ANCHOR,
        #             posX=float(match.group(8)),
        #             posY=float(match.group(9)),
        #             posZ=float(match.group(10)),
        #             readTime=getCurEpochTime(),
        #             serialNumber='',
        #             accuracy=rssi,
        #             uwbID=uwbID
        #         )
        #     )
        #     if(len(receiveAnchorDataBuf) > 1000):
        #         receiveAnchorDataBuf.pop(0)

        #     updateAnchorTimeMillis()
        #     print(f'Matched : {index} {uwbID} {rssi} {pos}')

        parsedData = lineData.split(',')
        if(len(parsedData)== 8):
            if( parsedData[0] == 'POS'):
                uwbID = lineData.split(',')[2]
                posX = float(lineData.split(',')[3])
                posY = float(lineData.split(',')[4])
                posZ = float(lineData.split(',')[5])
                accuracy = int(lineData.split(',')[6])
                global receiveTagDataBuf
                receiveTagDataBuf.append(
                    DeviceDTO(
                        posX=posX,
                        posY=posY,
                        posZ=posZ,
                        uwbID=uwbID,
                        readTime=getCurEpochTime(),
                        areaUid=thisGatewayDevice.areaUid,
                        deviceType=DeviceType.TAG,
                        serialNumber='',
                        accuracy=accuracy,
                        rssi=0
                    )
                )
                if(len(receiveTagDataBuf) > 1000):
                    receiveTagDataBuf.pop(0)
                    
                updateTagTimeMillis()
                # print(f'TagDataLen {len(receiveTagDataBuf)}')
                # POS,10,10B0,1.53,3.11,1.63,69,x0E            

def requestAnchorData():
    serial_controller.setWriteSerialData('la\r')


global receiveTagDataBuf
global receiveAnchorDataBuf

receiveTagDataBuf = []
receiveAnchorDataBuf = []


# 지금까지 받은 Tag와 Anchor의 데이터를 가져갈 수 있음. 가져간 후, 데이터는 초기화됨
def getAllDeviceData():
    global receiveTagDataBuf
    global receiveAnchorDataBuf
    trans_data_buf = []
    trans_data_buf.extend(receiveTagDataBuf)
    receiveTagDataBuf = []
    print(f'trans_data_buf 1 - {len(trans_data_buf)}')
    trans_data_buf.extend(receiveAnchorDataBuf)
    print(f'trans_data_buf 2 - {len(trans_data_buf)}')
    receiveAnchorDataBuf = []
    return trans_data_buf

def getTagDeviceData():
    global receiveTagDataBuf
    trans_data_buf = receiveTagDataBuf
    receiveTagDataBuf = []
    return trans_data_buf

def getAnchorDeviceData():
    global receiveAnchorDataBuf
    trans_data_buf = receiveAnchorDataBuf
    receiveAnchorDataBuf = []
    return trans_data_buf
    

def gatewayInfoValidateChecker(value):
    if((value.serialNumber == '') | (value.areaUid == '')) :
        print('gatewayInfoValidateChecker Error 1')        
        return False
    if(len(value.serialNumber)!=23) :
        print('gatewayInfoValidateChecker Error 2')
        return False
    if( (value.serialNumber[2] != ':') | (value.serialNumber[5] != ':') | (value.serialNumber[8] != ':') 
       | (value.serialNumber[11] != ':') | (value.serialNumber[14] != ':') | (value.serialNumber[17] != ':') | (value.serialNumber[20] != ':') ) :
        print('gatewayInfoValidateChecker Error 3')
        return False
    if( len(value.areaUid) != 6) :
        print('gatewayInfoValidateChecker Error 4')
        return False
    if( (value.areaUid[0] != '0') | (value.areaUid[1] != 'x')) :
        print('gatewayInfoValidateChecker Error 5')
        return False
    return True
#  D7:3C:56:4F:54:ED:2C:9F 0xD438



def setDevicePanID(panID):    
    panID = panID.replace('0x', '')   
    retry_count = 0
    while True:
        global thisGatewayDevice
        serial_controller.setWriteSerialData(value=f'nis 0x{panID}\r')
        time.sleep(1)
        if( serial_controller.getSerialEventChecker_nis()):
            thisGatewayDevice.areaUid = '0x'+panID
            print(f'PanIDIsChanged To {panID}')
            break
        else :
            print('setDevicePanID Fail')
        
        retry_count = retry_count + 1
        if(retry_count > 10) :
            print('setDevicePanID Fail')
            break


