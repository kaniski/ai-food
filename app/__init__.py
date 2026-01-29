import os
from flask import Flask
from dotenv import load_dotenv

def create_app():
    load_dotenv()

    app = Flask(__name__)

    # Isso aqui é o "cadeado" da sessão do Flask.
    # Sem ele, o app até roda, mas sessão vira dor de cabeça.
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-please-change")

    # Debug controlado por env, porque é assim que a vida real funciona.
    app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "0") == "1"

    from .routes import main_bp
    app.register_blueprint(main_bp)

    return app
