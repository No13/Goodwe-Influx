Docker-compose voorbeeld:
```yaml
  goodwe-influx:
    container_name: goodwe-influx
    image: goodwe-influx
    environment:
      - INFLUX_HOST=influx
      - INFLUX_USER=myuser
      - INFLUX_PASS=sosecret
      - INFLUX_PORT=8086
      - INFLUX_DB=Grafana
      - INFLUX_TLS=false
      - INVERTER_HOST=10.1.2.3
    networks:
      - dmz_docker
    restart: always
```