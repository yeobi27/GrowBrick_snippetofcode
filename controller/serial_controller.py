from controller.main_controller import *
import time
import serial
import threading



serialWriteCommandBuffer = []
serialReceivedBuffer = []
serialEventChecker_aurs = False
serialEventChecker_nis = False

def getSerialEventChecker_nis():
    global serialEventChecker_nis
    if(serialEventChecker_nis == True):
        serialEventChecker_nis = False
        return True
    return False

def getSerialEventChecker_aurs():
    global serialEventChecker_aurs
    if(serialEventChecker_aurs == True):
        serialEventChecker_aurs = False
        return True
    return False

def setWriteSerialData(value):
    global serialWriteCommandBuffer
    serialWriteCommandBuffer.append(value)
    
def getReadSerialDataAll():
    global serialReceivedBuffer
    readList = serialReceivedBuffer
    serialReceivedBuffer = []
    return readList
    
global ser

def main():
    global ser
    try :
        ser = serial.Serial('/dev/ttyS0', 115200, timeout=0.5, writeTimeout=1)
        print(f'SerialIsConnected {ser.name}')
    except BaseException as e:
        print(f'SerialCatchError {e}')
    ser.reset_input_buffer()
    ser.reset_output_buffer()

    print('SerialController Initialize')
        
    threading.Thread(target=serialReadLoop).start()
    
    threading.Thread(target=serialWriteLoop).start()

def serialWriteLoop():
    ###########################################################
    # SerialWriteCommandBuffer에 데이터가 있으면, 커맨드 날리는 구조
    ###########################################################
    while True:
        global serialWriteCommandBuffer
        if(len(serialWriteCommandBuffer) != 0):
            for data in serialWriteCommandBuffer:
                serialWrite(writeValue=data)
                print(f'SerialWrite : {data}')
            serialWriteCommandBuffer = []
        time.sleep(0.1)

def serialReadLoop():
    global ser
    serial_read_buff = ''
    
    if(ser.readable()):
        while True:
            try :
                readData = ser.readline().decode('ascii')
                serial_read_buff = serial_read_buff + readData                
                if serial_read_buff.find('\n') > -1:
                    oneLine = serial_read_buff.split('\r')[0]                    
                    global serialReceivedBuffer
                    serialReceivedBuffer.append(oneLine)
                    serial_read_buff = serial_read_buff.split('\n')[1]
                    
                    if(oneLine.find('aurs: ok')>=0):
                        global serialEventChecker_aurs
                        serialEventChecker_aurs = True
                    if(oneLine.find('nis: ok')>=0):
                        global serialEventChecker_nis
                        serialEventChecker_nis = True
                
                time.sleep(0.00001)
                                    
            except BaseException as e :
                ser.reset_input_buffer()
                ser.reset_output_buffer()
                serial_read_buff = ''
                ser.flush()
                print(f'SerialReadError : {e}')


def serialWrite(writeValue):
    global ser
    for character in (writeValue):
        time.sleep(0.01)
        ser.write(str.encode(f'{character}'))