import time
from machine import Pin
from DHT import DHT
import network
import socket
import urequests
from machine import Timer
from MicroWebSrv2 import MicroWebSrv2

dht_pin = 14  # DHT11 data pin
dht = DHT(Pin(dht_pin), 0)
ssid = "your_ssid"
password = "your_password"

data_points = []
time_interval = 60000  # 1 minute in milliseconds
max_data_points = 1440  # Max data points for 24 hours

# Connect to Wi-Fi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
if not wlan.isconnected():
    print("Connecting to Wi-Fi...")
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass
print("Connected to Wi-Fi")

# Web server
def _httpHandlerIndexGet(httpClient, httpResponse):
    temperature, humidity = dht.read()
    if temperature is not None and humidity is not None:
        jsonResponse = {
            "temperature": temperature,
            "humidity": humidity,
            "data_points": data_points
        }
        httpResponse.WriteResponseJSON(jsonResponse)
    else:
        httpResponse.WriteResponseBadRequest()

routeHandlers = [
    ({"path": "/", "method": "GET"}, _httpHandlerIndexGet)
]

srv = MicroWebSrv2()
srv.MaxWebSocketRecvLen = 256
srv.WebPath = "/www"
srv.RouteHandlers = routeHandlers
srv.StartManaged()

# Data collection
def data_collector(timer):
    temperature, humidity = dht.read()
    if temperature is not None and humidity is not None:
        if len(data_points) >= max_data_points:
            data_points.pop(0)
        data_points.append({
            "time": time.time(),
            "temperature": temperature,
            "humidity": humidity
        })

data_timer = Timer(0)
data_timer.init(period=time_interval, mode=Timer.PERIODIC, callback=data_collector)

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    data_timer.deinit()
    srv.Stop()
    print("Stopped.")
