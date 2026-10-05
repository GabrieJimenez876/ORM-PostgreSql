import argparse
from decimal import Decimal

from orm_project.database import SessionLocal, create_tables
from orm_project.services import (
    crear_pedido,
    crear_producto,
    crear_usuario,
    listar_productos,
    listar_usuarios,
)


def cargar_datos_demo() -> None:
    with SessionLocal() as session:
        usuarios = listar_usuarios(session)
        if not usuarios:
            usuario1 = crear_usuario(session, "Ana García", "ana@correo.com")
            usuario2 = crear_usuario(session, "Luis Pérez", "luis@correo.com")
        else:
            usuario1 = usuarios[0]
            usuario2 = usuarios[1] if len(usuarios) > 1 else usuarios[0]

        productos = listar_productos(session)
        if not productos:
            teclado = crear_producto(session, "Teclado mecánico", "Teclado RGB para gaming", Decimal("79.99"), 20)
            monitor = crear_producto(session, "Monitor 27\"", "Pantalla IPS Full HD", Decimal("249.99"), 8)
        else:
            teclado = productos[0]
            monitor = productos[1] if len(productos) > 1 else productos[0]

        try:
            crear_pedido(session, usuario1.id, teclado.id, 2)
            crear_pedido(session, usuario2.id, monitor.id, 1)
        except ValueError as exc:
            print(f"No se pudo crear el pedido de demostración: {exc}")

        print("\nUsuarios registrados:")
        for usuario in listar_usuarios(session):
            print(f"- {usuario.id}: {usuario.nombre} ({usuario.email})")

        print("\nProductos registrados:")
        for producto in listar_productos(session):
            print(f"- {producto.id}: {producto.nombre} - ${producto.precio} - Stock: {producto.stock}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Proyecto ORM con PostgreSQL")
    parser.add_argument("--init-db", action="store_true", help="Crear las tablas de la base de datos")
    parser.add_argument("--demo", action="store_true", help="Genera datos de ejemplo")
    parser.add_argument("--list-users", action="store_true", help="Lista todos los usuarios")
    parser.add_argument("--list-products", action="store_true", help="Lista todos los productos")
    args = parser.parse_args()

    if args.init_db:
        create_tables()
        print("Tablas creadas correctamente.")
        return

    if args.demo:
        cargar_datos_demo()
        return

    if args.list_users:
        with SessionLocal() as session:
            for usuario in listar_usuarios(session):
                print(f"{usuario.id} | {usuario.nombre} | {usuario.email} | activo={usuario.activo}")
        return

    if args.list_products:
        with SessionLocal() as session:
            for producto in listar_productos(session):
                print(f"{producto.id} | {producto.nombre} | ${producto.precio} | stock={producto.stock}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
