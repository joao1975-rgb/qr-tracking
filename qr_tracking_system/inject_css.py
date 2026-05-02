with open('templates/admin_campaigns.html', 'r', encoding='utf-8') as f:
    html = f.read()

# We need to completely rewrite the modal styles to float OVER the page
# and look like the Stitch mockup, without touching the HTML inputs.

css_old1 = """        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            backdrop-filter: blur(4px);
            z-index: 1000;
            display: none;
            align-items: center;
            justify-content: center;
        }"""

css_new1 = """        .modal-backdrop {
            display: none !important; /* Desactivado porque el contenedor principal ahora hace el backdrop */
        }"""

css_old2 = """        .modal {
            background: white;
            border-radius: 20px;
            width: 90%;
            max-width: 500px;
            max-height: 90vh;
            overflow-y: auto;
            box-shadow: 0 25px 50px rgba(0, 0, 0, 0.25);
            animation: modalIn 0.3s ease;
        }"""

css_new2 = """        .modal {
            /* ESTE ES EL CONTENEDOR PRINCIPAL QUE BLOQUEA LA PANTALLA */
            position: fixed !important;
            inset: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(17, 19, 23, 0.8) !important;
            backdrop-filter: blur(20px) !important;
            -webkit-backdrop-filter: blur(20px);
            z-index: 10000 !important;
            align-items: center;
            justify-content: center;
            padding: 20px;
            box-sizing: border-box;
            border-radius: 0 !important; /* Quitar bordes del fondo */
        }
        
        .modal-dialog {
            /* LA VENTANA FLOTANTE EN SI */
            background: linear-gradient(180deg, rgba(30, 32, 35, 0.95) 0%, rgba(20, 22, 25, 0.95) 100%) !important;
            border: 1px solid rgba(184, 195, 255, 0.2) !important;
            border-radius: 20px !important;
            width: 100%;
            max-width: 860px !important;
            max-height: 90vh !important;
            overflow-y: auto !important;
            box-shadow: 0 40px 100px rgba(0,0,0,0.8), 0 0 40px rgba(93, 63, 211, 0.15) !important;
            color: #e2e2e6 !important;
            animation: modalIn 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
            display: flex;
            flex-direction: column;
            position: relative;
        }"""

css_old3 = """        .modal-header {
            padding: 25px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-title {
            font-size: 1.25rem;
            font-weight: 700;
        }"""

css_new3 = """        .modal-header {
            padding: 24px 32px;
            border-bottom: 1px solid rgba(131, 131, 131, 0.15) !important;
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.2) !important;
            border-radius: 20px 20px 0 0;
        }
        
        .modal-title {
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 1.5rem;
            font-weight: 700;
            color: #b8c3ff !important;
            letter-spacing: -0.5px;
        }"""
        
css_old4 = """        .form-control, .form-select {
            width: 100%;
            padding: 10px 15px;
            border: 1px solid #d1d5db;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.2s;
        }"""

css_new4 = """        .form-control, .form-select {
            width: 100%;
            padding: 14px 18px !important;
            background: rgba(0, 0, 0, 0.4) !important;
            border: 1px solid rgba(131, 131, 131, 0.2) !important;
            color: #ffffff !important;
            border-radius: 10px !important;
            font-family: inherit;
            font-size: 0.95rem;
            transition: all 0.3s ease;
            outline: none !important;
        }
        
        .form-control:focus, .form-select:focus {
            border-color: #2ae500 !important;
            box-shadow: 0 0 0 3px rgba(42, 229, 0, 0.15) !important;
        }
        
        /* Premium Buttons */
        .btn-primary {
            background: linear-gradient(135deg, #0846ed 0%, #4804dd 100%) !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 8px 16px rgba(8, 70, 237, 0.2) !important;
        }
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 24px rgba(8, 70, 237, 0.35) !important;
        }
        
        /* Dark Tabs */
        .form-tabs {
            background: rgba(0,0,0,0.2) !important;
            border-bottom: 1px solid rgba(131, 131, 131, 0.15) !important;
            padding: 12px 20px 0 !important;
        }
        .form-tab {
            color: #888 !important;
            font-family: 'Space Grotesk', sans-serif !important;
        }
        .form-tab.active {
            color: #2ae500 !important;
            border-bottom-color: #2ae500 !important;
        }
        .form-group label {
            color: #c9c4d7 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        """

html = html.replace(css_old1, css_new1)
if css_old2 in html:
    html = html.replace(css_old2, css_new2)
else:
    print("Warning: css_old2 not found!")
html = html.replace(css_old3, css_new3)
html = html.replace(css_old4, css_new4)

with open('templates/admin_campaigns.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("CSS injected successfully!")
