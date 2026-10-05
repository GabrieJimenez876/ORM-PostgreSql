from datetime import date, datetime, timezone
from decimal import Decimal

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, UniqueConstraint, func

db = SQLAlchemy()


class Cuenta(UserMixin, db.Model):
    __tablename__ = "cuentas"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), nullable=False, unique=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    egresos = db.relationship("Egreso", back_populates="cuenta")


class Parametro(db.Model):
    __tablename__ = "parametro"
    __table_args__ = (
        CheckConstraint("mes >= 1 AND mes <= 12", name="ck_parametro_mes"),
        UniqueConstraint("gestion", "mes", name="uq_parametro_gestion_mes"),
    )

    id = db.Column(db.Integer, primary_key=True)
    gestion = db.Column(db.Integer, nullable=False)
    mes = db.Column(db.Integer, nullable=False)


class FormaPago(db.Model):
    __tablename__ = "forma_pago"

    idformapago = db.Column(db.Integer, primary_key=True)
    desformapago = db.Column(db.String(50), nullable=False, unique=True)
    estado = db.Column(db.Boolean, nullable=False, default=True, server_default="true")

    egresos = db.relationship("Egreso", back_populates="forma_pago")


class Egreso(db.Model):
    __tablename__ = "egresos"
    __table_args__ = (
        CheckConstraint("monto > 0", name="ck_egresos_monto_positivo"),
        CheckConstraint("mes >= 1 AND mes <= 12", name="ck_egresos_mes"),
    )

    idegreso = db.Column(db.Integer, primary_key=True)
    detalle = db.Column(db.String(50), nullable=False)
    monto = db.Column(db.Numeric(10, 2), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=date.today, server_default=func.current_date())
    gestion = db.Column(db.Integer, nullable=False, index=True)
    mes = db.Column(db.Integer, nullable=False, index=True)
    fecha_add = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    fecha_upd = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    cuenta_id = db.Column(
        db.Integer,
        db.ForeignKey("cuentas.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    idformapago = db.Column(
        db.Integer,
        db.ForeignKey("forma_pago.idformapago", ondelete="RESTRICT"),
        nullable=False,
    )

    forma_pago = db.relationship("FormaPago", back_populates="egresos")
    cuenta = db.relationship("Cuenta", back_populates="egresos")

    def to_dict(self) -> dict[str, object]:
        return {
            "idegreso": self.idegreso,
            "detalle": self.detalle,
            "monto": str(Decimal(self.monto)),
            "fecha": self.fecha.isoformat(),
            "gestion": self.gestion,
            "mes": self.mes,
            "fecha_add": self.fecha_add.isoformat(),
            "fecha_upd": self.fecha_upd.isoformat(),
            "idformapago": self.idformapago,
            "forma_pago": self.forma_pago.desformapago if self.forma_pago else None,
        }
