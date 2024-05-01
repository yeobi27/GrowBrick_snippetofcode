
from enum import Enum
from dataclasses import dataclass


class DeviceType(Enum):
    TAG = 'tag'
    ANCHOR = 'anchor'
    GATEWAY = 'gateway'
    LISTENER = 'listener'
    
class ErrorType(Enum):
    Waiting = 'waiting'
    Run = 'run'
    NoUWBAnchorData = 'noUWBAnchorData'
    NoUWBTagData = 'noUWBTagData'
    NoInternet = 'noInternet'

class DeviceControllerState(Enum):
    Initializing = 'initializing'
    Run = 'Run'
    
class Service(Enum):
    Activing = "activing"
    Inactive = "inactive"

class StatusCode(Enum):
    Normal = 100
    AnchorError = 101
    TagError = 102
    BLE_GATT_Error = 103
    ParsingError = 104
    DeviceDataUploadError = 105
    LogDataUploadError = 106
    LED_Check_Error = 107

@dataclass
class DeviceDTO:
    serialNumber: str
    # time: str
    areaUid: str        # panID 0x0000
    # projectUid: str
    uwbID: str  # 4807    
    deviceType: DeviceType
    posX: float
    posY: float
    posZ: float
    accuracy:int    # Only Tag Data
    rssi: int   # Only Anchor Data
    readTime: int
    
    # data_list: list[dict[str,float]]
    # tag_data_dict: dict[str,list[dict[str,float]]]
    # anchor_data_dict: dict[str, list[dict[str, Union[int, float, str]]]]
    
    # Existing in data_dict    
    # qf: int   # Only Tag Data, Quality factor of the estimated

@dataclass
class WiFiScanDTO:
    ssid:str
    signal:int
    
@dataclass
class NetworkInfoDTO:
    name:str
    mac:str
    ip:str
    type:str    
    
    


