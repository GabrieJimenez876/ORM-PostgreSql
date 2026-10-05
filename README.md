# Gestor de egresos con Flask y PostgreSQL

Aplicación web para registrar, consultar, editar, eliminar y buscar egresos. Usa Flask, Flask-SQLAlchemy y PostgreSQL.

## Requisitos

- Python 3.11 o superior
- Docker Compose

## Inicio rápido con Docker

1. Copia `.env.example` a `.env` y cambia `SECRET_KEY` por una clave aleatoria. Por ejemplo, en PowerShell:

   ```powershell
   Copy-Item .env.example .env
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

   Copia el valor generado en `SECRET_KEY` dentro de `.env`. Las credenciales predeterminadas del ejemplo son únicamente para desarrollo local.

2. Levanta la aplicación y PostgreSQL:

   ```powershell
   docker compose up --build
   ```

3. Abre [http://localhost:5000](http://localhost:5000). Para detener los servicios, usa `Ctrl+C`; para eliminarlos conserva el volumen de datos con `docker compose down`.

La primera ejecución crea las tablas, un periodo para el mes actual y formas de pago iniciales (efectivo, tarjeta y transferencia). La base de datos escucha solo en `localhost`.

## Ejecutar Flask fuera de Docker

Levanta PostgreSQL:

```powershell
docker compose up -d postgres
```

Crea y activa un entorno virtual, instala las dependencias y configura `.env` como se indica arriba:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

La aplicación estará disponible en [http://127.0.0.1:5000](http://127.0.0.1:5000). Para ejecutar con Gunicorn en un entorno compatible:

```bash
gunicorn --bind 0.0.0.0:5000 "app:create_app()"
```

También puedes configurar `DATABASE_URL` en `.env` para sustituir `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `DB_NAME`.

## Funcionalidades

- Listado y total de egresos del periodo contable activo.
- Alta y edición con validación de detalle, monto, fecha y forma de pago.
- Eliminación protegida con confirmación.
- Búsqueda por detalle.
- Registro, inicio y cierre de sesión; cada cuenta solo puede ver y modificar sus egresos.
- Contraseñas almacenadas con hash seguro, nunca en texto plano.
- Protección CSRF en las operaciones que modifican datos.
- Formularios adaptables a pantallas pequeñas.

Abre `/registro` para crear la primera cuenta. Los egresos se asignan al periodo contable más reciente registrado en `parametro`. Si la tabla aún no tiene uno, se crea automáticamente el periodo actual. Las formas de pago iniciales se cargan únicamente cuando no existe ninguna.

Al arrancar, la aplicación añade `cuenta_id` a una tabla `egresos` existente si todavía no tiene esa columna, sin borrar registros. Los egresos antiguos sin propietario se asignan a la primera cuenta, para que sus datos no queden visibles a todas las cuentas nuevas. Usa un respaldo de la base de datos antes de actualizar una instalación existente.

## Pruebas

Con las dependencias instaladas, ejecuta las pruebas con:

```powershell
python -m unittest discover -s tests
```

## Configuración

Variables admitidas en `.env`:

| Variable | Valor local predeterminado | Descripción |
| --- | --- | --- |
| `SECRET_KEY` | Obligatoria | Clave de sesión y CSRF. Usa una clave aleatoria y privada. |
| `DATABASE_URL` | — | URL SQLAlchemy opcional; si existe, prevalece sobre las variables individuales. |
| `DB_USER` | `postgres` | Usuario PostgreSQL. |
| `DB_PASSWORD` | `postgres` | Contraseña PostgreSQL. |
| `DB_HOST` | `localhost` | Host PostgreSQL (Compose configura `postgres` para el contenedor web). |
| `DB_PORT` | `5432` | Puerto PostgreSQL. |
| `DB_NAME` | `orm_db` | Nombre de la base de datos. |
| `PORT` | `5000` | Puerto al ejecutar `python app.py`. |
| `FLASK_DEBUG` | Desactivado | Define `1` solo para depuración local. |

`db.create_all()` prepara las tablas que falten. La única migración automática de tablas existentes añade la columna `cuenta_id` a `egresos`; no actualiza otros cambios estructurales. Si tu base tiene un esquema anterior diferente, respáldala y prepara una migración antes de desplegar.

## Estructura

```text
.
├── app.py
├── config.py
├── models.py
├── routes.py
├── templates/
├── static/css/style.css
├── Dockerfile
└── docker-compose.yml
```
