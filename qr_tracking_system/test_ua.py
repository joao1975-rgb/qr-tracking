from device_detector import DeviceDetector

ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Mobile Safari/537.36"
client_hint_model = "2412DPC0AG"

# Just append it loosely
fake_ua1 = f"{ua} {client_hint_model}"
print("Loose append:", fake_ua1)
device1 = DeviceDetector(fake_ua1).parse()
print("Loose append Brand:", device1.device_brand(), "Model:", device1.device_model())

# Replace 'K' or 'Android XX'
import re
fake_ua2 = re.sub(r'(Android [^;]+;)\s*[^)]+', rf'\1 {client_hint_model}', ua)
print("\nRegex Sub:", fake_ua2)
device2 = DeviceDetector(fake_ua2).parse()
print("Regex Sub Brand:", device2.device_brand(), "Model:", device2.device_model())
