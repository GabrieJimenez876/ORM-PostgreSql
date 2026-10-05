# ORM con PostgreSQL

Proyecto desarrollado en Python con SQLAlchemy para gestionar datos en PostgreSQL usando un ORM.

## Descripción

Este proyecto implementa una pequeña aplicación CRUD para manejar usuarios, productos y pedidos. La capa de acceso a datos se resuelve con SQLAlchemy ORM y PostgreSQL como motor de base de datos.

## Tecnologías

- Python 3.11+
- SQLAlchemy 2.x
- psycopg2-binary
- PostgreSQL 16
- Docker Compose para levantar la base de datos

## Estructura del proyecto

- `orm_project/config.py`: configuración de la conexión.
- `orm_project/database.py`: engine y sesión de SQLAlchemy.
- `orm_project/models.py`: modelos ORM.
- `orm_project/services.py`: CRUD y lógica de negocio.
- `app.py`: script principal para ejecutar la aplicación.

## Requisitos

1. Python instalado.
2. Docker y Docker Compose (opcional, para levantar PostgreSQL localmente).
3. PostgreSQL corriendo en `localhost:5432` o un contenedor local.

## Configuración

1. Crea un entorno virtual:

   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```

2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Crea un archivo `.env` con los datos de la base de datos:

   ```bash
   copy .env.example .env
   ```

   Ajusta los valores si necesitas cambiar usuario, contraseña o nombre de la base.

## Levantar PostgreSQL con Docker

```bash
docker compose up -d
```

Esto levantará PostgreSQL en `localhost:5432` con los datos:

- Usuario: `postgres`
- Contraseña: `postgres`
- Base de datos: `orm_db`

## Ejecutar el proyecto

Crear las tablas:

```bash
python app.py --init-db
```

Insertar datos de ejemplo:

```bash
python app.py --demo
```

Listar usuarios:

```bash
python app.py --list-users
```

Listar productos:

```bash
python app.py --list-products
```

## Modelo de datos

- Usuario: id, nombre, email, activo, creado_en
- Producto: id, nombre, descripcion, precio, stock
- Pedido: id, usuario_id, fecha, total
- DetallePedido: id, pedido_id, producto_id, cantidad, subtotal

## Ejemplo de flujo

La aplicación permite:

- Crear usuarios
- Consultar usuarios
- Actualizar datos de usuarios
- Eliminar usuarios
- Registrar productos
- Generar pedidos con detalle

## Uso en producción

En un entorno real se recomienda:

- Usar variables de entorno seguras
- Añadir validaciones con Pydantic o FastAPI
- Crear migraciones con Alembic
- Ejecutar pruebas unitarias e integración

## Autor

Proyecto realizado como ejercicio de ORM con PostgreSQL.
