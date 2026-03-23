import re

with open('app.py', 'r', encoding='utf-8') as f:
    c = f.read()

device_create_code = """
class DeviceCreate(BaseModel):
    device_id: str
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    location: Optional[str] = None
    venue: Optional[str] = None
    description: Optional[str] = None
    active: bool = True

"""

if "class DeviceCreate(BaseModel):" not in c:
    c = c.replace('class ScanCreate(', device_create_code + 'class ScanCreate(')
    
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("DeviceCreate Injected successfully.")
else:
    print("Already exists.")
