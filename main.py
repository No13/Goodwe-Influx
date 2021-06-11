'''
Main function for docker container
'''
import os
from threading import Timer
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
from goodwe import GoodWe

DOMO_URL = ''
DOMO_IDX = ''
DOMO_USER = ''
DOMO_PASS = ''
DOMO_INTERVAL = ''
GW = None
INFLUXDB_BUCKET = ''
INFLUXDB_ORG = ''

def main():
    '''
    Retrieve info and start timers
    '''
    global DOMO_URL, DOMO_IDX, DOMO_USER, DOMO_PASS, DOMO_INTERVAL
    global GW, INFLUXDB_BUCKET, INFLUXDB_ORG
    inverter_host = os.environ['INVERTER_HOST']
    influxdb_enabled = True
    try:
        INFLUXDB_BUCKET = os.environ['INFLUXDB_V2_BUCKET']
        INFLUXDB_ORG = os.environ['INFLUXDB_V2_ORG']
    except:
        influxdb_enabled = False
        print("InfluxDB not complete, disabling")

    domoticz_enabled = True
    try:
        DOMO_IDX = os.environ['DOMO_IDX_START']
        DOMO_URL = os.environ['DOMO_URL']
        DOMO_USER = os.environ['DOMO_USER']
        DOMO_PASS = os.environ['DOMO_PASS']
        DOMO_INTERVAL = os.environ['DOMO_INTERVAL']
    except:
        domoticz_enabled = False
        print("Domo not complete, disabling")

    GW = GoodWe(inverter_host)
    if influxdb_enabled:
        fill_influx()
    if domoticz_enabled:
        fill_domoticz()

if __name__ == '__main__':
    main()

def fill_influx():
    '''
    Retrieve stats and insert into influx
    '''
    global GW, INFLUXDB_BUCKET, INFLUXDB_ORG
    try:
        retries = 2
        data = GW.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:", data, "retries remaining:", retries)
            retries -= 1
            data = GW.get_inverter_data()
        if data['error'] == 'no error':
            with InfluxDBClient.from_env_properties() as influx_db:
                with influx_db.write_api(write_options=SYNCHRONOUS) as write_api:
                    jso = [{"measurement": "goodwe",
                            "tags":{"source": "Python"}, "fields": data}]
                    write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, jso)
                print("Written to db:", data)
        else:
            print("No valid data:", data)
    finally:
        Timer(10, fill_influx).start()

def fill_domoticz():
    '''
    Retrieve stats and insert into domoticz
    '''
    global DOMO_URL, DOMO_IDX, DOMO_USER, DOMO_PASS, DOMO_INTERVAL
    global GW, INFLUXDB_BUCKET, INFLUXDB_ORG
    try:
        retries = 2
        data = GW.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:", data, "retries remaining:", retries)
            retries -= 1
            data = GW.get_inverter_data()
        if data['error'] == 'no error':
            val = []
            val.append(str(data['temp']))
            val.append(str(data['iac']))
            val.append(str(data['vac']))
            val.append(str(data['power'])+';'+str(data['etot']*1000))
            val_index = 0
            resp_code = []
            for idx in range(int(DOMO_IDX), int(DOMO_IDX)+4):
                url = DOMO_URL+'/json.htm?type=command&param=udevice&idx='
                url += str(idx)+'&nvalue=0&svalue='+val[val_index]
                resp = requests.get(url,
                                    auth=requests.auth.HTTPBasicAuth(DOMO_USER, DOMO_PASS))
                resp_code.append(resp.status_code)
                val_index += 1
            print(resp_code)
    finally:
        Timer(int(DOMO_INTERVAL), fill_domoticz).start()
