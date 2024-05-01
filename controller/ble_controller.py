#!/usr/bin/env python3

from email import utils
import subprocess
import dbus
import dbus.exceptions
import dbus.mainloop.glib
import dbus.service
import os
import time
import network
import socket
import json

import array
import sys
from gi.repository import GObject
import threading
from random import randint
from controller import ethernet_controller
from controller import utils
import device_controller
from controller import error_check_controller

import os
import time


# def set_ble_name(newName):    
#     print(f"set_ble_name {newName}")
#     # BLE의 MAC Address를 바꾸는 기능 
#     hexList = newName.split(':')
#     os.system(f"sudo hcitool cmd 0x3f 0x001 0x{hexList[5]} 0x{hexList[4]} 0x{hexList[3]} 0x{hexList[2]} 0x{hexList[1]} 0x{hexList[0]}")
#     time.sleep(1)
#     os.system(f"sudo hciconfig hci0 reset")
#     time.sleep(1)
#     # BLE의 Name 바꾸는 기능 
#     os.system(f"sudo hostnamectl --pretty set-hostname '{''.join(newName.split(':'))}'")
#     print(f"NameIs {''.join(newName.split(':'))}")
#     time.sleep(1)
#     os.system("sudo service bluetooth restart")
#     time.sleep(1) 
#     os.system("sudo hciconfig hci0 up")             
#     time.sleep(1)
#     os.system("sudo hciconfig hci0 leadv 0")

def set_ble_name(newName):    
    print(f"set_ble_name {newName}")
    # BLE의 MAC Address를 바꾸는 기능 
    hexList = newName.split(':')
        
    os.system(f"sudo hcitool cmd 0x3f 0x001 0x{hexList[5]} 0x{hexList[4]} 0x{hexList[3]} 0x{hexList[2]} 0x{hexList[1]} 0x{hexList[0]}")
    time.sleep(1)
    os.system(f"sudo hciconfig hci0 reset")
    time.sleep(1)
    
    newHostname = ''.join(newName.split(':'))
    # 현재 hostname 이 같은지 체크하고 같으면 pass
    if not getHostname(newHostname): 
        setHostname(newHostname)
    
    print(f"NameIs {''.join(newName.split(':'))}")
    # BLE의 Name 바꾸는 기능 
    os.system(f"sudo hostnamectl --pretty set-hostname '{''.join(newName.split(':'))}'")
    time.sleep(1)
    os.system("sudo service bluetooth restart")
    time.sleep(1) 
    os.system("sudo hciconfig hci0 up")             
    time.sleep(1)
    os.system("sudo hciconfig hci0 leadv 0")
    

def getHostname(newhostname):
    command = "hostname"    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    print(f"Current : {result.stdout.strip()}")
    print(f"New HostName : {newhostname}")
    return result.stdout.strip() == newhostname

def setHostname(newhostname):
    with open('/etc/hosts', 'r') as file:
        # read a list of lines into data
        data = file.readlines()

        # the host name is on the 6th line following the IP address
        # so this replaces that line with the new hostname
        data[5] = '127.0.1.1       ' + newhostname

        # save the file temporarily because /etc/hosts is protected
        with open('temp.txt', 'w') as file:
            file.writelines( data )

        # use sudo command to overwrite the protected file
        os.system('sudo mv temp.txt /etc/hosts')

        # repeat process with other file
        with open('/etc/hostname', 'r') as file:
            data = file.readlines()

        data[0] = newhostname

        with open('temp.txt', 'w') as file:
            file.writelines( data )

        os.system('sudo mv temp.txt /etc/hostname')
    
mainloop = None

uwb_settings_value = {}

BLUEZ_SERVICE_NAME = 'org.bluez'
GATT_MANAGER_IFACE = 'org.bluez.GattManager1'
DBUS_OM_IFACE =      'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE =    'org.freedesktop.DBus.Properties'

GATT_SERVICE_IFACE = 'org.bluez.GattService1'
GATT_CHRC_IFACE =    'org.bluez.GattCharacteristic1'
GATT_DESC_IFACE =    'org.bluez.GattDescriptor1'

class InvalidArgsException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.freedesktop.DBus.Error.InvalidArgs'

class NotSupportedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotSupported'

class NotPermittedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.NotPermitted'

class InvalidValueLengthException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.InvalidValueLength'

class FailedException(dbus.exceptions.DBusException):
    _dbus_error_name = 'org.bluez.Error.Failed'


class Application(dbus.service.Object):
    """
    org.bluez.GattApplication1 interface implementation
    """
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(UWBBLEService(bus, 0))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        print('GetManagedObjects')

        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
                descs = chrc.get_descriptors()
                for desc in descs:
                    response[desc.get_path()] = desc.get_properties()

        return response


class Service(dbus.service.Object):
    """
    org.bluez.GattService1 interface implementation
    """
    PATH_BASE = '/org/bluez/example/service'

    def __init__(self, bus, index, uuid, primary):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_SERVICE_IFACE: {
                        'UUID': self.uuid,
                        'Primary': self.primary,
                        'Characteristics': dbus.Array(
                                self.get_characteristic_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    def get_characteristic_paths(self):
        result = []
        for chrc in self.characteristics:
            result.append(chrc.get_path())
        return result

    def get_characteristics(self):
        return self.characteristics

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    """
    org.bluez.GattCharacteristic1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + '/char' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.service = service
        self.flags = flags
        self.descriptors = []
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_CHRC_IFACE: {
                        'Service': self.service.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                        'Descriptors': dbus.Array(
                                self.get_descriptor_paths(),
                                signature='o')
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_descriptor(self, descriptor):
        self.descriptors.append(descriptor)

    def get_descriptor_paths(self):
        result = []
        for desc in self.descriptors:
            result.append(desc.get_path())
        return result

    def get_descriptors(self):
        return self.descriptors

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        print('Default StartNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        print('Default StopNotify called, returning error')
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE,
                         signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass


class Descriptor(dbus.service.Object):
    """
    org.bluez.GattDescriptor1 interface implementation
    """
    def __init__(self, bus, index, uuid, flags, characteristic):
        self.path = characteristic.path + '/desc' + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.chrc = characteristic
        dbus.service.Object.__init__(self, bus, self.path)

    def get_properties(self):
        return {
                GATT_DESC_IFACE: {
                        'Characteristic': self.chrc.get_path(),
                        'UUID': self.uuid,
                        'Flags': self.flags,
                }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE,
                         in_signature='s',
                         out_signature='a{sv}')
    def GetAll(self, interface):
        if interface != GATT_DESC_IFACE:
            raise InvalidArgsException()

        return self.get_properties()[GATT_DESC_IFACE]

    @dbus.service.method(GATT_DESC_IFACE,
                        in_signature='a{sv}',
                        out_signature='ay')
    def ReadValue(self, options):
        print ('Default ReadValue called, returning error')
        raise NotSupportedException()

    @dbus.service.method(GATT_DESC_IFACE, in_signature='aya{sv}')
    def WriteValue(self, value, options):
        print('Default WriteValue called, returning error')
        raise NotSupportedException()

uwbCharacteristicsData = []
class UWBBLEService(Service):
    TEST_SVC_UUID = 'uuiduuiduuiduuiduuiduuiduuiduuiduuiduuiduuiduuiduuiduuid'
    
    def __init__(self, bus, index):
        global uwbCharacteristicsData
        global thisGatewayDevice
        uwbCharacteristicsData = [
            {
                'name':'PanID',    
                'uuid':'uuiduuiduuiduuiduuiduuiduuid'
                'value':''
            },
            {
                'name':'WiFiScanResult',    
                'uuid':'uuiduuiduuiduuiduuiduuiduuid',  
                'value':''
            },
            {
                'name':'WiFiSettings',
                'uuid':'uuiduuiduuiduuiduuiduuiduuid',  
                'value':''
            },
            {
                'name':'EthernetState',
                'uuid':'uuiduuiduuiduuiduuiduuiduuid',
                'value':''
            },
            {
                'name':'NetworkInterface',
                'uuid':'uuiduuiduuiduuiduuiduuiduuid',
                'value':''
            },
            {
                'name':'Ping',
                'uuid':'uuiduuiduuiduuiduuiduuiduuid',
                'value':''
            },
            {
                'name':'Error',
                'uuid':'uuiduuiduuiduuiduuiduuiduuid',
                'value':''
            },
        ]
        Service.__init__(self, bus, index, self.TEST_SVC_UUID, True)
        
        for idx in range(len(uwbCharacteristicsData)):    
            self.add_characteristic(UWBBLEData(bus, idx, self))
# json.JSONDecoder().decode(json.dumps([tagDevice.__dict__ for tagDevice in tagDeviceList], cls=utils.EnumEncoder, indent=1))
class UWBBLEData(Characteristic):
    characteristicName = ""
    def __init__(self, bus, index, service):
        self.characteristicName = uwbCharacteristicsData[index]['name']
        TEST_CHRC_UUID = ((uwbCharacteristicsData[index]['uuid']))
        Characteristic.__init__(self, bus, index,TEST_CHRC_UUID,['read', 'write'],service)
        self.value = ((uwbCharacteristicsData[index]['value']))
        self.add_descriptor(CharacteristicDescriptor(bus, 0, self))

    def ReadValue(self, options):
        global thisGatewayDevice
        # scannedWiFiData = ethernet_controller.GetWiFiScanList()
        # connectedNetworkData = ethernet_controller.GetCurrentlyConnectedNetwork()
                
        print(f'Test : {self.characteristicName}')
        print('TestCharacteristic Read: ' + repr(self.value))
        if(self.characteristicName == 'EthernetState'):
            return bytes(f'{ethernet_controller.GetIPAddress()}', 'utf-8')
        elif(self.characteristicName == 'Ping'):
            return bytes(f'{ethernet_controller.isNetworkStatus()}', 'utf-8')
        elif(self.characteristicName == 'PanID'):
            return bytes.fromhex(device_controller.thisGatewayDevice.areaUid.split('0x')[1])[::-1]
        elif(self.characteristicName == 'WiFiSettings'):
            return bytes(f'{ethernet_controller.GetWiFiSSID()}', 'utf-8')
        elif(self.characteristicName == 'WiFiScanResult'):
            scannedWiFiData = ethernet_controller.GetWiFiScanList()
            return bytes(f'{json.JSONDecoder().decode(json.dumps([wifiData.__dict__ for wifiData in scannedWiFiData], cls=utils.EnumEncoder, indent=1))}', 'utf-8')
        elif(self.characteristicName == 'NetworkInterface'):
            connectedNetworkData = ethernet_controller.GetCurrentlyConnectedNetwork()
            return bytes(f'{json.JSONDecoder().decode(json.dumps([networkData.__dict__ for networkData in connectedNetworkData], cls=utils.EnumEncoder, indent=1))}', 'utf-8')
        elif(self.characteristicName == 'Error'):
            return bytes(f'{error_check_controller.curErrorType}', 'utf-8')
        else :
            return self.value

    def WriteValue(self, value, options):
        self.value = value
        if((self.characteristicName == 'WiFiSettings')) :
            stringValue = "".join([str(v) for v in value])
            if(len(stringValue.split(';')) > 1):
                WiFiSSID = stringValue.split(';')[0]
                WiFiPassword = stringValue.split(';')[1]
                print(f"WiFi Try Connect To : {WiFiSSID, WiFiPassword}")
                ethernet_controller.ConnectToWiFi(ssid=WiFiSSID, password=WiFiPassword)
        elif((self.characteristicName == 'PanID')):
            stringValue = "".join([str(v) for v in value])
            print(f'PanID Is Changed By BLE {self.characteristicName} - {stringValue}')
            device_controller.setDevicePanID(stringValue)            
        
        


class CharacteristicDescriptor(Descriptor):
    CUD_UUID = 'uuiduuiduuiduuiduuiduuiduuid'

    def __init__(self, bus, index, characteristic):
        self.writable = 'writable-auxiliaries' in characteristic.flags
        self.value = array.array('B', b'Client Characteristic Configuration')
        self.value = self.value.tolist()
        Descriptor.__init__(
                self, bus, index,
                self.CUD_UUID,
                ['read', 'write'],
                characteristic)

    def ReadValue(self, options):
        return self.value

    def WriteValue(self, value, options):
        if not self.writable:
            raise NotPermittedException()
        self.value = value


def register_app_cb():
    print('GATT application registered')


def register_app_error_cb(error):
    print('Failed to register application: ' + str(error))
    mainloop.quit()


def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()

    for o, props in objects.items():
        if GATT_MANAGER_IFACE in props.keys():
            return o

    return None

def main(gatewayDevice):
    global thisGatewayDevice
    thisGatewayDevice = gatewayDevice
    print(f'BLEGattServer Start : {gatewayDevice}')
    
    set_ble_name(gatewayDevice.serialNumber)
    global mainloop

    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    adapter = find_adapter(bus)
    if not adapter:
        print('GattManager1 interface not found')
        return

    service_manager = dbus.Interface(
            bus.get_object(BLUEZ_SERVICE_NAME, adapter),
            GATT_MANAGER_IFACE)

    app = Application(bus)

    mainloop = GObject.MainLoop()

    print('Registering GATT application...')

    service_manager.RegisterApplication(app.get_path(), {},
                                    reply_handler=register_app_cb,
                                    error_handler=register_app_error_cb)

    time.sleep(3)
    os.system("sudo hciconfig hci0 up")
    time.sleep(1)
    os.system("sudo hciconfig hci0 leadv 0")
    
    
    threading.Thread(target=mainloop.run).start()
    
    
def updateData(_thisGatewayDevice):
    global thisGatewayDevice
    thisGatewayDevice = _thisGatewayDevice
    
    os.system('echo 3 | sudo hciconfig hci0 leadv 0 >/dev/null 2>&1') 

    