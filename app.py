import os
from datetime import date

from flask import Flask
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from sqlalchemy import inspect, select, text, update

from config import Config
from models import Cuenta, Egreso, FormaPago, Parametro, db
from routes import auth_bp, bp

csrf = CSRFProtect()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para continuar."
login_manager.login_message_category = "error"


@login_manager.user_loader
def load_user(cuenta_id: str) -> Cuenta | None:
    try:
        return db.session.get(Cuenta, int(cuenta_id))
    except ValueError:
        return None


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
    login_manager.init_app(app)
    app.register_blueprint(bp)
    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()
        if "cuenta_id" not in {
            column["name"] for column in inspect(db.engine).get_columns(Egreso.__tablename__)
        }:
            with db.engine.begin() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE egresos ADD COLUMN cuenta_id "
                        "INTEGER REFERENCES cuentas (id) ON DELETE RESTRICT"
                    )
                )
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_egresos_cuenta_id "
                    "ON egresos (cuenta_id)"
                )
            )

        primera_cuenta_id = db.session.scalar(select(Cuenta.id).order_by(Cuenta.id).limit(1))
        if primera_cuenta_id is not None:
            db.session.execute(
                update(Egreso)
                .where(Egreso.cuenta_id.is_(None))
                .values(cuenta_id=primera_cuenta_id)
            )
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
