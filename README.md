Docker-compose voorbeeld:
```yaml
  goodwe-influx:
    container_name: goodwe-influx
    image: goodwe-influx
    environment:
      - INFLUXDB_V2_URL=http://influx:8086
      - INFLUXDB_V2_TOKEN=username:sosecret
      - INFLUXDB_V2_ORG=Grafana
      - INFLUXDB_V2_BUCKET=Grafana
      - INVERTER_HOST=10.1.2.3
      - DOMO_URL=https://domoticz.example.nl
      - DOMO_USER=mysensor
      - DOMO_PASS=veryverysecret
      - DOMO_INTERVAL=30
      - DOMO_IDX_START=63
    networks:
      - dmz_docker
    restart: always

```