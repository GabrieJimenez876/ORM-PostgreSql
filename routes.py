from datetime import date
from decimal import Decimal, InvalidOperation

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from models import Egreso, FormaPago, Parametro, db

bp = Blueprint("web", __name__)


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
def inicio():
    parametro = _periodo_actual()
    egresos = db.session.scalars(
        select(Egreso)
        .options(joinedload(Egreso.forma_pago))
        .where(Egreso.gestion == parametro.gestion, Egreso.mes == parametro.mes)
        .order_by(Egreso.fecha.desc(), Egreso.idegreso.desc())
    ).all()
    total = db.session.scalar(
        select(func.coalesce(func.sum(Egreso.monto), 0)).where(
            Egreso.gestion == parametro.gestion,
            Egreso.mes == parametro.mes,
        )
    )
    return render_template(
        "index.html",
        egresos=egresos,
        parametro=parametro,
        total=total,
    )


@bp.route("/egresos/crear", methods=["GET", "POST"])
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
def editar_egreso(idegreso: int):
    egreso = db.get_or_404(Egreso, idegreso)
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
def eliminar_egreso(idegreso: int):
    egreso = db.get_or_404(Egreso, idegreso)
    db.session.delete(egreso)
    db.session.commit()
    flash("El egreso se eliminó correctamente.", "success")
    return redirect(url_for("web.inicio"))


@bp.get("/egresos/buscar")
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
