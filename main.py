import os
from threading import Timer
from influxdb_client import InfluxDBClient, Point
from goodwe import Goodwe

def fillInflux():
    '''
    Retrieve stats and insert into influx
    '''
    global gw, influxdb_org, influxdb_bucket
    try:
        retries = 2
        data = gw.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:",data,"retries remaining:",retries)
            retries -= 1
            data = gw.get_inverter_data()
        if(data['error'] == 'no error'):
            db = InfluxDBClient.from_env_properties()
            with db.write_api() as write_api:
                jso = [ {"measurement": "goodwe", "tags":{"source": "Python" }, "fields": data } ]
                write_api.write(influxdb_bucket, influxdb_org, jso)
            db.close()
            print("Written to db:",data)
        else:
            print("No valid data:",data)
    finally:
        Timer(10,fillInflux).start()

inverter_host = os.environ['INVERTER_HOST']
influxdb_bucket = os.environ['INFLUXDB_V2_BUCKET']
influxdb_org = os.environ['INFLUXDB_V2_ORG']
gw = Goodwe(inverter_host)

fillInflux()