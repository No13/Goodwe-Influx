'''
GoodWe class for retrieving information from inverter
'''
import socket
import time

class GoodWe:
    '''
    GoodWe Class
    '''
    _data = ''
    def __init__(self, hostname):
        '''
        Set hostname for further function calls
        '''
        self.hostname = hostname
        self._s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)


    def crc16(self, data: bytes):
        '''
        CRC-16-ModBus Algorithm
        '''
        data = bytearray(data)
        poly = 0xA001
        crc = 0xFFFF
        for data_byte in data:
            crc ^= (0xFF & data_byte)
            for _ in range(0, 8):
                if crc & 0x0001:
                    crc = ((crc >> 1) & 0xFFFF) ^ poly
                else:
                    crc = ((crc >> 1) & 0xFFFF)
        return crc

    def get_int(self, in_bytes):
        '''
        Convert range of bytes to integer
        '''
        if type(in_bytes) is int:
            return in_bytes
        return int.from_bytes(in_bytes[:len(in_bytes)], 'big')

    def get_info(self, timeout=0.5):
        '''
        Retrieve WiFi information
        '''
        self._s.settimeout(timeout)
        try:
            self._s.sendto(bytes.fromhex('574946494b49542d3231343032382d52454144'),
                           (self.hostname, 48899))
            data, _address = self._s.recvfrom(4096)
            print(data)
        except:
            print('timeout')

    def get_inverter_data(self, timeout=0.5):
        '''
        Retrieve and parse data packet from inverter
        '''
        self._s.settimeout(timeout)
        try:
            self._s.sendto(bytes.fromhex('7f0375940049d5c2'), (self.hostname, 8899))
            data, _address = self._s.recvfrom(4096)
            # do CRC check
            self._data = data
            crc_data = data[-1:].hex()+data[-2:-1].hex()
            crc_calc = hex(self.crc16(data[2:-2]))[2:]
            if crc_data == crc_calc:
                inverter_data = {
                    'error': 'no error',
                    'vpv1': round(self.get_int(data[11:13])*0.1, 2),
                    'ipv1': round(self.get_int(data[13:15])*0.1, 2),
                    'vpv2': round(self.get_int(data[15:17])*0.1, 2),
                    'ipv2': round(self.get_int(data[17:19])*0.1, 2),
                    'vac': round(self.get_int(data[41:43])*0.1, 2),
                    'iac': round(self.get_int(data[47:49])*0.1, 2),
                    'fac': round(self.get_int(data[53:55])*0.01, 2),
                    'eday': round(self.get_int(data[93:95])*0.1, 2),
                    'etot': round(self.get_int(data[95:99])*0.1, 2),
                    'rssi': self.get_int(data[149:151]),
                    'hours': self.get_int(data[101:103]),
                    'temp': round(self.get_int(data[87:89])*0.1, 2),
                    'power': self.get_int(data[61:63]),
                    'status': self.get_int(data[63:65]),
                    'timestamp': time.mktime((2000+self.get_int(data[5]),
                                              self.get_int(data[6]),
                                              self.get_int(data[7]),
                                              self.get_int(data[8]),
                                              self.get_int(data[9]),
                                              self.get_int(data[10]), -1, -1, -1))}
                return inverter_data
            # In case of CRC error; enforce timeout to prevent early retry
            time.sleep(timeout)
            return {"error": "crc error"}
        except socket.timeout:
            return {"error": "timeout"}
        except Exception as error_msg:
            return {"error":str(error_msg)}
