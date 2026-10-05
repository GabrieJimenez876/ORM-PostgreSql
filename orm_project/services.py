from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import DetallePedido, Pedido, Producto, Usuario


def crear_usuario(session: Session, nombre: str, email: str, activo: bool = True) -> Usuario:
    usuario = Usuario(nombre=nombre, email=email, activo=activo)
    session.add(usuario)
    session.commit()
    session.refresh(usuario)
    return usuario


def listar_usuarios(session: Session):
    return session.execute(select(Usuario).order_by(Usuario.id)).scalars().all()


def buscar_usuario_por_id(session: Session, usuario_id: int):
    return session.get(Usuario, usuario_id)


def actualizar_usuario(session: Session, usuario_id: int, nombre: str | None = None, email: str | None = None, activo: bool | None = None) -> Usuario | None:
    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        return None

    if nombre is not None:
        usuario.nombre = nombre
    if email is not None:
        usuario.email = email
    if activo is not None:
        usuario.activo = activo

    session.commit()
    session.refresh(usuario)
    return usuario


def eliminar_usuario(session: Session, usuario_id: int) -> bool:
    usuario = session.get(Usuario, usuario_id)
    if usuario is None:
        return False

    session.delete(usuario)
    session.commit()
    return True


def crear_producto(session: Session, nombre: str, descripcion: str, precio: Decimal | float, stock: int) -> Producto:
    producto = Producto(
        nombre=nombre,
        descripcion=descripcion,
        precio=Decimal(str(precio)),
        stock=int(stock),
    )
    session.add(producto)
    session.commit()
    session.refresh(producto)
    return producto


def listar_productos(session: Session):
    return session.execute(select(Producto).order_by(Producto.id)).scalars().all()


def crear_pedido(session: Session, usuario_id: int, producto_id: int, cantidad: int) -> Pedido:
    usuario = session.get(Usuario, usuario_id)
    producto = session.get(Producto, producto_id)

    if usuario is None:
        raise ValueError("Usuario no encontrado")
    if producto is None:
        raise ValueError("Producto no encontrado")
    if cantidad <= 0:
        raise ValueError("La cantidad debe ser mayor que cero")

    subtotal = Decimal(str(producto.precio)) * cantidad
    pedido = Pedido(usuario_id=usuario_id, total=subtotal)
    session.add(pedido)
    session.flush()

    detalle = DetallePedido(
        pedido_id=pedido.id,
        producto_id=producto_id,
        cantidad=cantidad,
        subtotal=subtotal,
    )
    session.add(detalle)

    producto.stock = max(0, producto.stock - cantidad)

    session.commit()
    session.refresh(pedido)
    return pedido


def listar_pedidos(session: Session):
    return session.execute(select(Pedido).order_by(Pedido.id)).scalars().all()
