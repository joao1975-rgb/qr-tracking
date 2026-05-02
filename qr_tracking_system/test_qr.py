import sys
import os
import base64

# Ensure the app code is importable
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import generate_qr_image

# Test generating a QR code with default logo
print("Testing QR generation with logo_mode='default'...")
b64 = generate_qr_image(data="https://example.com", size=300, error_correction="H", logo_mode="default")

if b64:
    print(f"Success! Generated base64 string of length {len(b64)}.")
    print("Prefix:", b64[:50])
else:
    print("Failed to generate QR image.")
