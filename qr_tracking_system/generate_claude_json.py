import json

try:
    with open('app.py', encoding='utf-8') as f:
        app_code = f.read()
    with open('templates/tracking.html', encoding='utf-8') as f:
        tracking_code = f.read()

    start_idx = app_code.find('@app.get("/track")')
    end_idx = app_code.find('def get_all_scans', start_idx)
    relevant_app = app_code[start_idx:end_idx] if start_idx != -1 else app_code

    data = {
        "codigo_servidor_app_py": relevant_app,
        "codigo_cliente_tracking_html": tracking_code
    }

    with open('codigo_para_claude.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("codigo_para_claude.json created successfully.")
except Exception as e:
    print(f"Error: {e}")
