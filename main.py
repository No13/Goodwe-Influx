'''
Main function for docker container
'''
import os
from threading import Timer
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
import graphyte
from goodwe import GoodWe

DOMO_URL = ''
DOMO_IDX = ''
DOMO_USER = ''
DOMO_PASS = ''
DOMO_INTERVAL = ''
GW = None
INFLUXDB_BUCKET = ''
INFLUXDB_ORG = ''
GRAPHITE_HOST = ''

DOMOTICZ_ENABLED = True
GRAPHITE_ENABLED = True
INFLUXDB_ENABLED = True

def fill_graphite(data):
    '''
    Input stats into graphite
    '''
    global GRAPHITE_HOST
    try:
        graphyte.init(GRAPHITE_HOST, prefix="energy.data")
        graphyte.send("kwh.goodwe", float(data['etot']))
        graphyte.send("solar_goodwe", int(data['power']))
        graphyte.send("goodwe.temp", float(data['temp']))
        graphyte.send("goodwe.iac", float(data['iac']))
        graphyte.send("goodwe.vac", float(data['vac']))
    finally:
        print("Graphite done")

def fill_influx(data):
    '''
    Retrieve stats and insert into influx
    '''
    global INFLUXDB_BUCKET, INFLUXDB_ORG
    try:
        with InfluxDBClient.from_env_properties() as influx_db:
            with influx_db.write_api(write_options=SYNCHRONOUS) as write_api:
                jso = [{"measurement": "goodwe",
                        "tags":{"source": "Python"}, "fields": data}]
                write_api.write(INFLUXDB_BUCKET, INFLUXDB_ORG, jso)
            print("Written to db:", data)
    finally:
        print("Influx done")

def fill_domoticz(data):
    '''
    Retrieve stats and insert into domoticz
    '''
    global DOMO_URL, DOMO_IDX, DOMO_USER, DOMO_PASS, DOMO_INTERVAL
    try:
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
        print("Domo done")

def update_all():
    '''
    Retrieve all stats from inverter
    '''
    global DOMOTICZ_ENABLED, INFLUXDB_ENABLED, GRAPHITE_ENABLED
    global GW
    try:
        retries = 2
        data = GW.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:", data, "retries remaining:", retries)
            retries -= 1
            data = GW.get_inverter_data()
        if data['error'] == 'no error':
            if DOMOTICZ_ENABLED:
                fill_domoticz(data)
            if INFLUXDB_ENABLED:
                fill_influx(data)
            if GRAPHITE_ENABLED:
                fill_graphite(data)
    finally:
        Timer(30, update_all).start()

def main():
    '''
    Retrieve info and start timers
    '''
    global DOMO_URL, DOMO_IDX, DOMO_USER, DOMO_PASS, DOMO_INTERVAL
    global GW, INFLUXDB_BUCKET, INFLUXDB_ORG
    global INFLUXDB_ENABLED, GRAPHITE_ENABLED, DOMOTICZ_ENABLED
    global GRAPHITE_HOST
    inverter_host = os.environ['INVERTER_HOST']

    try:
        INFLUXDB_BUCKET = os.environ['INFLUXDB_V2_BUCKET']
        INFLUXDB_ORG = os.environ['INFLUXDB_V2_ORG']
    except:
        INFLUXDB_ENABLED = False
        print("InfluxDB not complete, disabling")

    try:
        DOMO_IDX = os.environ['DOMO_IDX_START']
        DOMO_URL = os.environ['DOMO_URL']
        DOMO_USER = os.environ['DOMO_USER']
        DOMO_PASS = os.environ['DOMO_PASS']
        DOMO_INTERVAL = os.environ['DOMO_INTERVAL']
    except:
        DOMOTICZ_ENABLED = False
        print("Domo not complete, disabling")

    try:
        GRAPHITE_HOST = os.environ['GRAPHITE_HOST']
    except:
        GRAPHITE_ENABLED = False
        print("No graphite")

    GW = GoodWe(inverter_host)

    update_all()

if __name__ == '__main__':
    main()
