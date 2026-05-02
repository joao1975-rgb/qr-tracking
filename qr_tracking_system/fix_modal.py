import re

with open('templates/admin_campaigns.html', 'r', encoding='utf-8') as f:
    html = f.read()

# The modal starts at <div id="campaignModal"
# We need to find the start and end of this block.
start_idx = html.find('<div id="campaignModal"')
# Since it's exactly one top-level div, let's find the matching tag
def find_matching_div(text, start):
    open_tags = 0
    idx = start
    while idx < len(text):
        if text[idx:idx+4] == '<div':
            open_tags += 1
            idx += 4
        elif text[idx:idx+6] == '</div>':
            open_tags -= 1
            idx += 6
            if open_tags == 0:
                return idx
        else:
            idx += 1
    return -1

end_idx = find_matching_div(html, start_idx)

# Define the new modal HTML and CSS
NEW_MODAL = """
<style>
/* STITCH-INSPIRED GLASSMORPHISM CSS FOR CAMPAÑA MODAL */
#campaignModal.modal-overlay {
    position: fixed; inset: 0; z-index: 1000;
    background: rgba(0, 0, 0, 0.4);
    backdrop-filter: blur(8px);
    display: flex; align-items: center; justify-content: center;
    padding: 20px;
}

#campaignModal .glass-panel {
    background: rgba(30, 32, 35, 0.85);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(72, 69, 84, 0.3);
    border-radius: 16px;
    width: 100%; max-width: 800px; max-height: 90vh;
    color: #e2e2e6;
    display: flex; flex-direction: column;
    box-shadow: 0 24px 48px rgba(0,0,0,0.6);
    font-family: 'Inter', sans-serif;
    overflow: hidden;
}

#campaignModal .modal-header {
    padding: 24px 32px;
    border-bottom: 1px solid rgba(72, 69, 84, 0.2);
    display: flex; justify-content: space-between; align-items: center;
    background: rgba(26, 28, 31, 0.5);
}

#campaignModal .modal-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 24px; font-weight: 700; color: #b8c3ff;
    margin: 0; letter-spacing: -0.5px;
}
#campaignModal .modal-subtitle {
    font-size: 14px; color: #c9c4d7; margin: 4px 0 0 0; font-weight: 500;
}

#campaignModal .modal-close {
    background: transparent; border: none; font-size: 20px;
    color: #c9c4d7; cursor: pointer; border-radius: 50%; width: 36px; height: 36px;
    display: flex; align-items: center; justify-content: center;
    transition: background 0.2s, color 0.2s;
}
#campaignModal .modal-close:hover {
    background: rgba(40, 42, 45, 1); color: #fff;
}

#campaignModal .modal-body {
    padding: 32px; overflow-y: auto;
}

/* Form Styles */
#campaignModal .form-group {
    margin-bottom: 24px; display: flex; flex-direction: column; gap: 8px;
}
#campaignModal .two-cols {
    display: grid; grid-template-columns: 1fr 1fr; gap: 24px;
}
#campaignModal label {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1px; color: #c9c4d7;
}

#campaignModal input[type="text"], 
#campaignModal input[type="url"], 
#campaignModal select, 
#campaignModal textarea {
    background: transparent;
    border: none;
    border-bottom: 1px solid #484554;
    color: #e2e2e6;
    padding: 12px 0; font-size: 15px; outline: none;
    transition: border-color 0.2s;
    font-family: 'Inter', sans-serif;
}
#campaignModal input:focus, #campaignModal select:focus, #campaignModal textarea:focus {
    border-bottom-color: #b8c3ff;
}
#campaignModal select option { background: #1e2023; color: #fff; }

#campaignModal textarea {
    background: rgba(26, 28, 31, 0.5);
    border: 1px solid rgba(72, 69, 84, 0.2);
    border-radius: 8px; padding: 16px; min-height: 80px; resize: none;
}

/* Radio Cards */
#campaignModal .radio-cards {
    display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin-top: 8px;
}
#campaignModal .radio-card {
    background: rgba(26, 28, 31, 0.8);
    border: 1px solid rgba(72, 69, 84, 0.2);
    border-radius: 12px; padding: 20px 16px;
    cursor: pointer; text-align: center; transition: all 0.2s;
    display: flex; flex-direction: column; align-items: center; gap: 12px;
}
#campaignModal input[type="radio"] { display: none; }
#campaignModal input[type="radio"]:checked + .radio-card {
    border-color: #2ae500;
    background: rgba(42, 229, 0, 0.05);
}
#campaignModal .radio-card .icon { font-size: 32px; }
#campaignModal .radio-card .title { font-size: 14px; font-weight: 600; }

/* Gradient Button */
#campaignModal .btn-submit {
    background: linear-gradient(135deg, #0846ed, #4804dd);
    color: white; border: none; padding: 16px 32px;
    border-radius: 8px; font-family: 'Space Grotesk', sans-serif;
    font-weight: 800; font-size: 14px; letter-spacing: 1px;
    cursor: pointer; transition: transform 0.2s; width: 100%; box-shadow: 0 8px 16px rgba(8, 70, 237, 0.2);
}
#campaignModal .btn-submit:hover { transform: translateY(-2px); }

#campaignModal .btn-cancel {
    background: transparent; color: #c9c4d7; border: none; padding: 16px 32px;
    font-weight: 600; cursor: pointer; transition: color 0.2s;
}
#campaignModal .btn-cancel:hover { color: #fff; }

#campaignModal .modal-footer {
    padding: 24px 32px; border-top: 1px solid rgba(72, 69, 84, 0.2);
    display: flex; justify-content: flex-end; gap: 16px; background: rgba(17, 19, 23, 0.8);
}
</style>

<div id="campaignModal" class="modal-overlay" style="display:none">
  <div class="glass-panel">
    
    <header class="modal-header">
      <div>
        <h2 id="modalTitle" class="modal-title">Nueva Campaña</h2>
        <p class="modal-subtitle">Configura los parámetros de tu observatorio cinético</p>
      </div>
      <button type="button" onclick="closeCampaignModal()" class="modal-close">✕</button>
    </header>

    <div class="modal-body">
      <form id="campaignForm" onsubmit="submitCampaign(event)">
        <!-- Essential Hidden Defaults for API compatibility -->
        <input type="hidden" name="goal_conversion_rate" value="0">
        <input type="hidden" name="goal_scans" value="0">
        
        <div class="two-cols">
            <div class="form-group required">
              <label>Código de Campaña</label>
              <input type="text" name="campaign_code" id="campaign_code" 
                     placeholder="Ej: NIKE_VERANO_2025" 
                     pattern="[A-Z0-9_-]+" style="text-transform:uppercase" required>
            </div>
            
            <div class="form-group required">
              <label>Cliente / Anunciante</label>
              <input type="text" name="client" id="client" 
                     placeholder="Nombre del cliente" required>
            </div>
        </div>

        <div class="two-cols">
            <div class="form-group required">
              <label>Industria / Sector</label>
              <select name="industry" id="industry" required>
                <option value="" disabled selected>Selecciona sector</option>
                <option value="Retail & Moda">Retail & Moda</option>
                <option value="Tecnología">Tecnología</option>
                <option value="Automotriz">Automotriz</option>
                <option value="Entretenimiento">Entretenimiento</option>
                <option value="Inmobiliaria">Inmobiliaria</option>
                <option value="Otro">Otro</option>
              </select>
            </div>
            <div class="form-group required">
              <label>Marca (Brand)</label>
              <input type="text" name="brand" id="brand" placeholder="Nombre específico de la marca" required>
            </div>
        </div>
        
        <div class="form-group required">
          <label>URL de Destino</label>
          <input type="url" name="destination" id="destination" 
                 placeholder="https://tu-sitio.com/landing" required>
        </div>

        <div class="form-group">
          <label>Tipo de Campaña</label>
          <div class="radio-cards">
            <label>
              <input type="radio" name="campaign_type" value="Digital Billboard" checked>
              <div class="radio-card">
                <div class="icon" style="color: #b8c3ff;">🎯</div>
                <div class="title">Digital Billboard</div>
              </div>
            </label>
            <label>
              <input type="radio" name="campaign_type" value="Flyer/Poster">
              <div class="radio-card">
                <div class="icon" style="color: #c9beff;">📄</div>
                <div class="title">Flyer / Poster</div>
              </div>
            </label>
            <label>
              <input type="radio" name="campaign_type" value="Point of Sale">
              <div class="radio-card">
                <div class="icon" style="color: #bbaeff;">🏪</div>
                <div class="title">Point of Sale</div>
              </div>
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>Notas Adicionales</label>
          <textarea name="description" id="description" placeholder="Detalles sobre la ubicación o el objetivo..."></textarea>
        </div>
        
        <div class="modal-footer">
            <button type="button" class="btn-cancel" onclick="closeCampaignModal()">CANCELAR</button>
            <button type="submit" class="btn-submit" id="submitCampaignBtn">GUARDAR CAMPAÑA</button>
        </div>
      </form>
    </div>
  </div>
</div>
"""

new_html = html[:start_idx] + NEW_MODAL + html[end_idx:]

with open('templates/admin_campaigns.html', 'w', encoding='utf-8') as f:
    f.write(new_html)
print("Updated admin_campaigns.html successfully!")
