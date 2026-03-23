from device_detector import DeviceDetector
from user_agents import parse

# Simulate the POCO X7 Pro user agent
ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
ua_with_model = "Mozilla/5.0 (Linux; Android 10; 2412DPC0AG) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"

print("--- DEVICE DETECTOR ---")
device = DeviceDetector(ua).parse()
print("Without model in UA: ", device.device_brand(), device.device_model())

device2 = DeviceDetector(ua_with_model).parse()
print("With model in UA: ", device2.device_brand(), device2.device_model())

print("\n--- USER AGENTS ---")
ua1 = parse(ua)
print("Without model in UA: ", ua1.device.brand, ua1.device.model)

ua2 = parse(ua_with_model)
print("With model in UA: ", ua2.device.brand, ua2.device.model)

# Client hints test
# DeviceDetector also has a method for client hints? Usually not in the basic wrapper, but we can check if there's a way.
