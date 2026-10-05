from datetime import date
from decimal import Decimal, InvalidOperation
import re

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import func, select, update
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from models import Cuenta, Egreso, FormaPago, Parametro, db

bp = Blueprint("web", __name__)
auth_bp = Blueprint("auth", __name__)


def _egreso_de_usuario(idegreso: int) -> Egreso:
    egreso = db.session.scalar(
        select(Egreso).where(
            Egreso.idegreso == idegreso,
            Egreso.cuenta_id == current_user.id,
        )
    )
    if egreso is None:
        abort(404)
    return egreso


@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("web.inicio"))

    username = request.form.get("username", "").strip().lower()
    if request.method == "POST":
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        errores = []
        if not re.fullmatch(r"[a-z0-9_.-]{3,32}", username):
            errores.append(
                "El usuario debe tener entre 3 y 32 caracteres: letras, números, punto, guion o guion bajo."
            )
        if len(password) < 12:
            errores.append("La contraseña debe tener al menos 12 caracteres.")
        if len(password) > 128:
            errores.append("La contraseña no puede superar los 128 caracteres.")
        if password != password_confirm:
            errores.append("Las contraseñas no coinciden.")
        if db.session.scalar(select(Cuenta.id).where(Cuenta.username == username)):
            errores.append("Ese nombre de usuario ya está registrado.")

        if not errores:
            cuenta = Cuenta(
                username=username,
                password_hash=generate_password_hash(password),
            )
            db.session.add(cuenta)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                if db.session.scalar(select(Cuenta.id).where(Cuenta.username == username)):
                    errores.append("Ese nombre de usuario ya está registrado.")
                else:
                    raise
            else:
                if cuenta.id == db.session.scalar(select(func.min(Cuenta.id))):
                    db.session.execute(
                        update(Egreso)
                        .where(Egreso.cuenta_id.is_(None))
                        .values(cuenta_id=cuenta.id)
                    )
                    db.session.commit()
                login_user(cuenta)
                flash("Cuenta creada. Ya puedes registrar tus egresos.", "success")
                return redirect(url_for("web.inicio"))

        return render_template(
            "registro.html",
            username=username,
            errores=errores,
        ), 400

    return render_template("registro.html", username="", errores=[])


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("web.inicio"))

    username = request.form.get("username", "").strip().lower()
    error = None
    if request.method == "POST":
        cuenta = db.session.scalar(select(Cuenta).where(Cuenta.username == username))
        password = request.form.get("password", "")
        if cuenta is None or not check_password_hash(cuenta.password_hash, password):
            error = "Usuario o contraseña incorrectos."
        else:
            login_user(cuenta)
            flash("Sesión iniciada correctamente.", "success")
            return redirect(url_for("web.inicio"))

    return render_template(
        "login.html",
        username=username,
        error=error,
    )


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for("auth.login"))


def _periodo_actual() -> Parametro:
    parametro = db.session.scalar(
        select(Parametro).order_by(Parametro.gestion.desc(), Parametro.mes.desc()).limit(1)
    )
    if parametro is None:
        abort(503, description="No hay un periodo contable configurado.")
    return parametro


def _formas_pago() -> list[FormaPago]:
    return list(
        db.session.scalars(
            select(FormaPago)
            .where(FormaPago.estado.is_(True))
            .order_by(FormaPago.desformapago)
        )
    )


def _valores_formulario(egreso: Egreso | None = None) -> dict[str, str]:
    if request.method == "POST":
        return {
            "detalle": request.form.get("detalle", "").strip(),
            "monto": request.form.get("monto", "").strip(),
            "fecha": request.form.get("fecha", "").strip(),
            "idformapago": request.form.get("idformapago", "").strip(),
        }
    if egreso is None:
        return {
            "detalle": "",
            "monto": "",
            "fecha": date.today().isoformat(),
            "idformapago": "",
        }
    return {
        "detalle": egreso.detalle,
        "monto": f"{egreso.monto:.2f}",
        "fecha": egreso.fecha.isoformat(),
        "idformapago": str(egreso.idformapago),
    }


def _validar_formulario() -> tuple[dict[str, object] | None, list[str]]:
    valores = _valores_formulario()
    errores: list[str] = []
    detalle = valores["detalle"]
    if not detalle:
        errores.append("El detalle es obligatorio.")
    elif len(detalle) > 50:
        errores.append("El detalle no puede superar los 50 caracteres.")

    try:
        monto = Decimal(valores["monto"])
        if not monto.is_finite() or monto <= 0:
            raise InvalidOperation
        if monto.as_tuple().exponent < -2 or monto > Decimal("99999999.99"):
            errores.append("El monto debe tener hasta dos decimales y no superar 99.999.999,99.")
    except (InvalidOperation, ValueError):
        monto = Decimal("0")
        errores.append("Ingresa un monto válido mayor que cero.")

    try:
        fecha = date.fromisoformat(valores["fecha"])
    except ValueError:
        fecha = date.today()
        errores.append("Ingresa una fecha válida.")

    try:
        idformapago = int(valores["idformapago"])
    except ValueError:
        idformapago = 0
        errores.append("Selecciona una forma de pago válida.")
    else:
        forma_pago = db.session.get(FormaPago, idformapago)
        if forma_pago is None or not forma_pago.estado:
            errores.append("La forma de pago seleccionada no está disponible.")

    if errores:
        return None, errores
    return {
        "detalle": detalle,
        "monto": monto,
        "fecha": fecha,
        "idformapago": idformapago,
    }, []


def _formulario_invalido(
    template: str,
    errores: list[str],
    egreso: Egreso | None = None,
    parametro: Parametro | None = None,
):
    valores = _valores_formulario(egreso)
    return (
        render_template(
            template,
            egreso=egreso,
            valores=valores,
            formas_pago=_formas_pago(),
            errores=errores,
            parametro=parametro,
        ),
        400,
    )


@bp.get("/")
@login_required
def inicio():
    parametro = _periodo_actual()
    egresos = db.session.scalars(
        select(Egreso)
        .options(joinedload(Egreso.forma_pago))
        .where(
            Egreso.gestion == parametro.gestion,
            Egreso.mes == parametro.mes,
            Egreso.cuenta_id == current_user.id,
        )
        .order_by(Egreso.fecha.desc(), Egreso.idegreso.desc())
    ).all()
    total = db.session.scalar(
        select(func.coalesce(func.sum(Egreso.monto), 0)).where(
            Egreso.gestion == parametro.gestion,
            Egreso.mes == parametro.mes,
            Egreso.cuenta_id == current_user.id,
        )
    )
    return render_template(
        "index.html",
        egresos=egresos,
        parametro=parametro,
        total=total,
    )


@bp.route("/egresos/crear", methods=["GET", "POST"])
@login_required
def crear_egreso():
    parametro = _periodo_actual()
    if request.method == "POST":
        datos, errores = _validar_formulario()
        if errores:
            return _formulario_invalido("crear.html", errores, parametro=parametro)

        egreso = Egreso(
            **datos,
            gestion=parametro.gestion,
            mes=parametro.mes,
            cuenta_id=current_user.id,
        )
        db.session.add(egreso)
        db.session.commit()
        flash("El egreso se creó correctamente.", "success")
        return redirect(url_for("web.inicio"))

    return render_template(
        "crear.html",
        parametro=parametro,
        valores=_valores_formulario(),
        formas_pago=_formas_pago(),
        errores=[],
    )


@bp.route("/egresos/editar/<int:idegreso>", methods=["GET", "POST"])
@login_required
def editar_egreso(idegreso: int):
    egreso = _egreso_de_usuario(idegreso)
    if request.method == "POST":
        datos, errores = _validar_formulario()
        if errores:
            return _formulario_invalido("editar.html", errores, egreso)

        for campo, valor in datos.items():
            setattr(egreso, campo, valor)
        db.session.commit()
        flash("El egreso se actualizó correctamente.", "success")
        return redirect(url_for("web.inicio"))

    return render_template(
        "editar.html",
        egreso=egreso,
        valores=_valores_formulario(egreso),
        formas_pago=_formas_pago(),
        errores=[],
    )


@bp.post("/egresos/eliminar/<int:idegreso>")
@login_required
def eliminar_egreso(idegreso: int):
    egreso = _egreso_de_usuario(idegreso)
    db.session.delete(egreso)
    db.session.commit()
    flash("El egreso se eliminó correctamente.", "success")
    return redirect(url_for("web.inicio"))


@bp.get("/egresos/buscar")
@login_required
def buscar_egreso():
    query = request.args.get("q", "").strip()
    parametro = _periodo_actual()
    egresos = []
    if query:
        egresos = db.session.scalars(
            select(Egreso)
            .where(
                Egreso.gestion == parametro.gestion,
                Egreso.mes == parametro.mes,
                Egreso.cuenta_id == current_user.id,
                func.lower(Egreso.detalle).contains(query.lower(), autoescape=True),
            )
            .options(joinedload(Egreso.forma_pago))
            .order_by(Egreso.fecha.desc(), Egreso.idegreso.desc())
        ).all()
    return render_template(
        "buscar.html",
        egresos=egresos,
        query=query,
        parametro=parametro,
    )
