import os
import sys
import json
from flask import Flask, send_from_directory, jsonify, request

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# from src.models.user import db # Uncomment if you need database
# from src.routes.user import user_bp # Uncomment if you need database

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# app.register_blueprint(user_bp, url_prefix='/api') # Uncomment if you need database

# uncomment if you need to use database
# app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db.init_app(app)
# with app.app_context():
#     db.create_all()

@app.route('/', defaults={'path': ''}) # type: ignore
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/strategy_content')
def strategy_content():
    try:
        with open("parsed_strategy.json", "r", encoding="utf-8") as f:
            content = json.load(f)
        return jsonify(content)
    except FileNotFoundError:
        return jsonify({"error": "Strategy content not found"}), 404

@app.route('/contact', methods=['POST'])
def contact():
    data = request.get_json()
    name = data.get('name')
    email = data.get('email')
    message = data.get('message')

    # Here you would typically send an email, save to a database, etc.
    # For this local version, we'll just print to console and return a success message.
    print(f"New contact form submission:\nName: {name}\nEmail: {email}\nMessage: {message}")

    return jsonify({"message": "Mensaje enviado con éxito. ¡Gracias por tu interés!"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


