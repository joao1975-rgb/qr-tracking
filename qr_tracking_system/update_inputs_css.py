with open('templates/admin_campaigns.html', 'r', encoding='utf-8') as f:
    html = f.read()

css_old_inputs = """        .form-control, .form-select {
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
        }"""

css_new_inputs = """        /* Enhanced Form Inputs & Selects */
        .form-control, .form-select, input[type="text"], input[type="url"], input[type="number"], input[type="date"], select, textarea {
            width: 100%;
            padding: 16px 20px !important;
            background: rgba(255, 255, 255, 0.04) !important; /* Ligeramente más claro para resaltar */
            border: 1px solid rgba(184, 195, 255, 0.2) !important; /* Borde Electric Blue suave */
            color: #ffffff !important;
            border-radius: 12px !important;
            font-family: 'Inter', 'Segoe UI', sans-serif !important;
            font-size: 1rem !important; /* Letra un poco más grande */
            font-weight: 500 !important;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1) !important;
            outline: none !important;
            box-shadow: inset 0 2px 4px rgba(0,0,0,0.2) !important;
        }
        
        .form-control::placeholder, input::placeholder, textarea::placeholder {
            color: rgba(255, 255, 255, 0.3) !important;
        }
        
        /* Dropdown Options Specific Styling */
        select option {
            background-color: #1a1d24 !important; /* Fondo oscuro sólido para la persiana */
            color: #ffffff !important;
            padding: 12px !important;
            font-size: 1rem !important;
        }
        
        .form-control:hover, .form-select:hover, select:hover {
            border-color: rgba(184, 195, 255, 0.5) !important;
            background: rgba(255, 255, 255, 0.08) !important;
        }
        
        .form-control:focus, .form-select:focus, input:focus, select:focus, textarea:focus {
            border-color: #2ae500 !important; /* Borde Neon Green */
            background: rgba(42, 229, 0, 0.05) !important; /* Fondo ligeramente verde */
            box-shadow: 0 0 0 4px rgba(42, 229, 0, 0.15), inset 0 2px 4px rgba(0,0,0,0.1) !important;
            transform: translateY(-1px);
        }"""

css_old_labels = """        .form-group label {
            color: #c9c4d7 !important;
            font-family: 'Space Grotesk', sans-serif !important;
            text-transform: uppercase;
            letter-spacing: 1px;
        }"""

css_new_labels = """        .form-group label {
            color: #b8c3ff !important; /* Electric Blue para resaltar totalmente */
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 0.8rem !important;
            font-weight: 700 !important;
            text-transform: uppercase;
            letter-spacing: 1.5px !important;
            margin-bottom: 10px !important;
            display: inline-block;
            text-shadow: 0 1px 2px rgba(0,0,0,0.5);
        }"""

if css_old_inputs in html:
    html = html.replace(css_old_inputs, css_new_inputs)
else:
    print("Warning: css_old_inputs not found!")

if css_old_labels in html:
    html = html.replace(css_old_labels, css_new_labels)
else:
    print("Warning: css_old_labels not found!")

# Optional: Upgrade tab styling slightly too
css_old_tabs = """        .form-tab.active {
            color: #2ae500 !important;
            border-bottom-color: #2ae500 !important;
        }"""

css_new_tabs = """        .form-tab.active {
            color: #2ae500 !important;
            border-bottom: 3px solid #2ae500 !important;
            text-shadow: 0 0 10px rgba(42, 229, 0, 0.4);
            font-weight: 800 !important;
        }
        .form-tab:hover:not(.active) {
            color: #b8c3ff !important;
            background: rgba(255,255,255,0.03) !important;
            border-radius: 8px 8px 0 0;
        }"""
        
if css_old_tabs in html:
    html = html.replace(css_old_tabs, css_new_tabs)

with open('templates/admin_campaigns.html', 'w', encoding='utf-8') as f:
    f.write(html)
print("CSS forms injected successfully!")
