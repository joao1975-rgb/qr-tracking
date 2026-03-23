import os
from device_detector import DeviceDetector

ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
client_hint_model = "2412DPC0AG"

# Simulate injecting it
fake_ua = ua.replace("Android 10; K", f"Android 10; {client_hint_model}")
print("Fake UA:", fake_ua)

device = DeviceDetector(fake_ua).parse()
print("Brand:", device.device_brand())
print("Model:", device.device_model())
