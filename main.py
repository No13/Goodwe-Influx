'''
Main function for docker container
'''
import os
from threading import Timer
from influxdb_client import InfluxDBClient
from influxdb_client.client.write_api import SYNCHRONOUS
import requests
from goodwe import GoodWe

def fillInflux():
    '''
    Retrieve stats and insert into influx
    '''
    global gw, influxdb_org, influxdb_bucket
    try:
        retries = 2
        data = gw.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:", data, "retries remaining:", retries)
            retries -= 1
            data = gw.get_inverter_data()
        if data['error'] == 'no error':
            with InfluxDBClient.from_env_properties() as db:
                with db.write_api(write_options=SYNCHRONOUS) as write_api:
                    jso = [{"measurement": "goodwe",
                            "tags":{"source": "Python"}, "fields": data}]
                    write_api.write(influxdb_bucket, influxdb_org, jso)
                print("Written to db:", data)
        else:
            print("No valid data:", data)
    finally:
        Timer(10, fillInflux).start()

def fillDomoticz():
    '''
    Retrieve stats and insert into domoticz
    '''
    global gw, domoticz_idx, domoticz_url, domoticz_user, domoticz_pass, domoticz_interval
    try:
        retries = 2
        data = gw.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:", data, "retries remaining:", retries)
            retries -= 1
            data = gw.get_inverter_data()
        if data['error'] == 'no error':
            val = []
            val.append(str(data['temp']))
            val.append(str(data['iac']))
            val.append(str(data['vac']))
            val.append(str(data['power'])+';'+str(data['etot']*1000))
            val_index = 0
            resp_code = []
            for idx in range(int(domoticz_idx), int(domoticz_idx)+4):
                url = domoticz_url+'/json.htm?type=command&param=udevice&idx='
                url += str(idx)+'&nvalue=0&svalue='+val[val_index]
                resp = requests.get(url,
                                    auth=requests.auth.HTTPBasicAuth(domoticz_user, domoticz_pass))
                resp_code.append(resp.status_code)
                val_index += 1
            print(resp_code)
    finally:
        Timer(int(domoticz_interval), fillDomoticz).start()

inverter_host = os.environ['INVERTER_HOST']
influxdb_enabled = True
try:
    influxdb_bucket = os.environ['INFLUXDB_V2_BUCKET']
    influxdb_org = os.environ['INFLUXDB_V2_ORG']
except:
    influxdb_enabled = False
    print("InfluxDB not complete, disabling")

domoticz_enabled = True
try:
    domoticz_idx = os.environ['DOMO_IDX_START']
    domoticz_url = os.environ['DOMO_URL']
    domoticz_user = os.environ['DOMO_USER']
    domoticz_pass = os.environ['DOMO_PASS']
    domoticz_interval = os.environ['DOMO_INTERVAL']
except:
    domoticz_enabled = False
    print("Domo not complete, disabling")

gw = GoodWe(inverter_host)
if influxdb_enabled:
    fillInflux()
if domoticz_enabled:
    fillDomoticz()
