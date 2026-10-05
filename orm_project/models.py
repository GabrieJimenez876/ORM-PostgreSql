from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import relationship

from .database import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    email = Column(String(150), unique=True, nullable=False, index=True)
    activo = Column(Boolean, default=True, nullable=False)
    creado_en = Column(DateTime, default=datetime.utcnow, nullable=False)

    pedidos = relationship("Pedido", back_populates="usuario")


class Producto(Base):
    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(150), nullable=False, index=True)
    descripcion = Column(String(300), nullable=True)
    precio = Column(Numeric(10, 2), nullable=False)
    stock = Column(Integer, nullable=False, default=0)

    detalles = relationship("DetallePedido", back_populates="producto")


class Pedido(Base):
    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow, nullable=False)
    total = Column(Numeric(10, 2), nullable=False, default=0)

    usuario = relationship("Usuario", back_populates="pedidos")
    detalles = relationship("DetallePedido", back_populates="pedido", cascade="all, delete-orphan")


class DetallePedido(Base):
    __tablename__ = "detalle_pedido"

    id = Column(Integer, primary_key=True, index=True)
    pedido_id = Column(Integer, ForeignKey("pedidos.id"), nullable=False)
    producto_id = Column(Integer, ForeignKey("productos.id"), nullable=False)
    cantidad = Column(Integer, nullable=False, default=1)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)

    pedido = relationship("Pedido", back_populates="detalles")
    producto = relationship("Producto", back_populates="detalles")
