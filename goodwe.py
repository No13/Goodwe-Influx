import socket, time, os
from threading import Timer
from influxdb import InfluxDBClient

def crc16(data: bytes):
    '''
    CRC-16-ModBus Algorithm
    '''
    data = bytearray(data)
    poly = 0xA001
    crc = 0xFFFF
    for b in data:
        crc ^= (0xFF & b)
        for _ in range(0, 8):
            if (crc & 0x0001):
                crc = ((crc >> 1) & 0xFFFF) ^ poly
            else:
                crc = ((crc >> 1) & 0xFFFF)
    return crc

def get_int(in_bytes):
    '''
    Convert range of bytes to integer
    '''
    if type(in_bytes) is int:
        return in_bytes
    else:
        return int.from_bytes(in_bytes[:len(in_bytes)],'big')



def get_inverter_data(hostname,timeout=0.5):
    '''
    Retrieve and parse data packet from inverter
    '''
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
    s.settimeout(timeout)
    try:
        s.sendto(bytes.fromhex('7f0375940049d5c2'),(hostname,8899))
        data,address = s.recvfrom(4096)
        # do CRC check
        crc_data = data[-1:].hex()+data[-2:-1].hex() 
        crc_calc = hex(crc16(data[2:-2]))[2:]
        if(crc_data == crc_calc):
            inverter_data = {
                'error': 'no error',
                'vpv1': round(get_int(data[11:13])*0.1,2),
                'ipv1': round(get_int(data[13:15])*0.1,2),
                'vpv2': round(get_int(data[15:17])*0.1,2),
                'ipv2': round(get_int(data[17:19])*0.1,2),
                'vac': round(get_int(data[41:43])*0.1,2),
                'iac': round(get_int(data[47:49])*0.1,2),
                'fac': round(get_int(data[53:55])*0.01,2),
                'eday': round(get_int(data[93:95])*0.1,2),
                'etot': round(get_int(data[97:99])*0.1,2),
                'rssi': get_int(data[149:151]),
                'hours': get_int(data[101:103]),
                'temp': round(get_int(data[87:89])*0.1,2),
                'power': get_int(data[61:63]),
                'status': get_int(data[63:65]),
                'timestamp': time.mktime((2000+get_int(data[5]),get_int(data[6]),get_int(data[7]), get_int(data[8]), get_int(data[9]), get_int(data[10]),-1,-1,-1))
            }
            return(inverter_data)
        return {"error": "crc error"}
    except socket.timeout:
        return {"error": "timeout"}
    except Exception as e:
        return {"error":str(e)}

def fillInflux():
    '''
    Retrieve stats and insert into influx
    '''
    global inverter_host, influx_host, influx_user, influx_pass, influx_port, influx_db, influx_tls
    try:
        data = get_inverter_data(inverter_host)
        print("Got data:",data)
        # Retry once...
        if(data['error'] != 'no error'):
            print("Error on first run, retry")
            data = get_inverter_data(inverter)
        if(data['error'] == 'no error'):
            print("Good data")
            db = InfluxDBClient(influx_host,influx_port,influx_user,influx_pass,influx_db, ssl=influx_tls)
            jso = [ {"measurement": "goodwe", "tags":{"source": "Python" }, "fields": data } ]
            db.write_points(jso)
            db.close()
    finally:
        Timer(10,fillInflux).start()

inverter_host = os.environ['INVERTER_HOST']
influx_host = os.environ['INFLUX_HOST']
influx_user = os.environ['INFLUX_USER']
influx_pass = os.environ['INFLUX_PASS']
influx_port = int(os.environ['INFLUX_PORT'])
influx_db = os.environ['INFLUX_DB']
influx_tls = ("true" in os.environ['INFLUX_TLS']) or ("True" in os.environ['INFLUX_TLS'])

fillInflux()