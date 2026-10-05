import os
from datetime import date

from flask import Flask
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import select

from config import Config
from models import FormaPago, Parametro, db
from routes import bp

csrf = CSRFProtect()


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)
    secret_key = app.config.get("SECRET_KEY")
    if not secret_key or secret_key == "replace-this-with-a-long-random-secret":
        raise RuntimeError("Configura una SECRET_KEY privada y aleatoria antes de iniciar la aplicación.")

    db.init_app(app)
    csrf.init_app(app)
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()
        if db.session.scalar(select(Parametro.id).limit(1)) is None:
            hoy = date.today()
            db.session.add(Parametro(gestion=hoy.year, mes=hoy.month))
        if db.session.scalar(select(FormaPago.idformapago).limit(1)) is None:
            db.session.add_all(
                [
                    FormaPago(desformapago="Efectivo"),
                    FormaPago(desformapago="Tarjeta"),
                    FormaPago(desformapago="Transferencia"),
                ]
            )
        db.session.commit()

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=int(os.getenv("PORT", "5000")),
        debug=os.getenv("FLASK_DEBUG") == "1",
    )
