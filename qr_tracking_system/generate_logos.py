import base64
import os

files = {
    'CENTAURO_LOGO_BASE64': r'D:\Users\joaou\OneDrive\Documentos\Aplicativos\qr\static\centauro_isotipo.png',
    'CENTAURO_BANNER_BASE64': r'D:\Users\joaou\OneDrive\Documentos\Aplicativos\qr\static\centauro_logo_full.png'
}

out_path = r'c:\Users\joaou\.gemini\antigravity\QR tracking\qr_tracking_system\logos_base64.py'

with open(out_path, 'w') as f:
    for name, path in files.items():
        if os.path.exists(path):
            with open(path, 'rb') as img:
                b64 = base64.b64encode(img.read()).decode('utf-8')
                f.write(f'{name} = "{b64}"\n')
        else:
            print(f'Missing {path}')
print('Done!')
