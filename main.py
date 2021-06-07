import os
from threading import Timer
from influxdb import InfluxDBClient
from goodwe import Goodwe

def fillInflux():
    '''
    Retrieve stats and insert into influx
    '''
    global gw, influx_host, influx_user, influx_pass, influx_port, influx_db, influx_tls
    try:
        retries = 2
        data = gw.get_inverter_data()
        while (data['error'] != 'no error') and retries > 0:
            print("Got error:",data,"retries remaining:",retries)
            retries -= 1
            data = gw.get_inverter_data()
        if(data['error'] == 'no error'):
            db = InfluxDBClient(influx_host,influx_port,influx_user,influx_pass,influx_db, ssl=influx_tls)
            jso = [ {"measurement": "goodwe", "tags":{"source": "Python" }, "fields": data } ]
            db.write_points(jso)
            db.close()
            print("Written to db:",data)
        else:
            print("No valid data:",data)
    finally:
        Timer(10,fillInflux).start()

inverter_host = os.environ['INVERTER_HOST']
influx_host = os.environ.get('INFLUX_HOST','localhost')
influx_user = os.environ.get('INFLUX_USER','')
influx_pass = os.environ.get('INFLUX_PASS','')
influx_port = int(os.environ.get('INFLUX_PORT',8086))
influx_db = os.environ.get('INFLUX_DB','default')
tls = os.environ.get('INFLUX_TLS','false')
influx_tls = ("true" in tls) or ("True" in tls)

gw = Goodwe(inverter_host)

fillInflux()