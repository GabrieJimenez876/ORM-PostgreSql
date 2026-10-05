import unittest

from sqlalchemy import select

from app import create_app
from models import Cuenta, Egreso, FormaPago, db


class EgresosRoutesTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(
            {
                "TESTING": True,
                "SECRET_KEY": "test-secret",
                "SQLALCHEMY_DATABASE_URI": "sqlite://",
                "WTF_CSRF_ENABLED": False,
            }
        )
        self.client = self.app.test_client()
        with self.app.app_context():
            self.forma_pago_id = db.session.scalar(select(FormaPago.idformapago))

    def crear_cuenta(self, username="gabriel"):
        response = self.client.post(
            "/registro",
            data={
                "username": username,
                "password": "contraseña-segura-123",
                "password_confirm": "contraseña-segura-123",
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            return db.session.scalar(select(Cuenta).where(Cuenta.username == username)).id

    def test_pages_require_login_and_account_registration_hashes_password(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.headers["Location"])

        cuenta_id = self.crear_cuenta()
        with self.app.app_context():
            cuenta = db.session.get(Cuenta, cuenta_id)
            self.assertNotEqual(cuenta.password_hash, "contraseña-segura-123")

        response = self.client.post("/logout")
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            "/login",
            data={"username": "gabriel", "password": "contraseña-incorrecta"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("incorrectos", response.get_data(as_text=True))

        response = self.client.post(
            "/login",
            data={"username": "gabriel", "password": "contraseña-segura-123"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/")

    def test_crud_and_search(self):
        cuenta_id = self.crear_cuenta()
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("egresos", response.get_data(as_text=True))

        response = self.client.post(
            "/egresos/crear",
            data={
                "detalle": "Servicio de internet",
                "monto": "120.50",
                "fecha": "2026-10-05",
                "idformapago": str(self.forma_pago_id),
            },
        )
        self.assertEqual(response.status_code, 302)

        with self.app.app_context():
            egreso = db.session.scalar(select(Egreso))
            self.assertIsNotNone(egreso)
            egreso_id = egreso.idegreso
            self.assertEqual(egreso.cuenta_id, cuenta_id)

        response = self.client.post(
            f"/egresos/editar/{egreso_id}",
            data={
                "detalle": "Internet actualizado",
                "monto": "125.00",
                "fecha": "2026-10-06",
                "idformapago": str(self.forma_pago_id),
            },
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/egresos/buscar?q=actualizado")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Internet actualizado", response.data)

        response = self.client.post(f"/egresos/eliminar/{egreso_id}")
        self.assertEqual(response.status_code, 302)
        response = self.client.get("/")
        self.assertNotIn(b"Internet actualizado", response.data)

    def test_invalid_amount_is_rejected(self):
        self.crear_cuenta()
        response = self.client.post(
            "/egresos/crear",
            data={
                "detalle": "Egreso inválido",
                "monto": "-5",
                "fecha": "2026-10-05",
                "idformapago": str(self.forma_pago_id),
            },
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("monto válido".encode(), response.data)
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(select(Egreso)))

    def test_accounts_cannot_access_each_others_expenses(self):
        self.crear_cuenta("primero")
        response = self.client.post(
            "/egresos/crear",
            data={
                "detalle": "Gasto privado",
                "monto": "20.00",
                "fecha": "2026-10-05",
                "idformapago": str(self.forma_pago_id),
            },
        )
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            egreso_id = db.session.scalar(select(Egreso.idegreso))

        self.client.post("/logout")
        self.crear_cuenta("segundo")

        response = self.client.get("/")
        self.assertNotIn("Gasto privado", response.get_data(as_text=True))
        response = self.client.get(f"/egresos/editar/{egreso_id}")
        self.assertEqual(response.status_code, 404)
        response = self.client.post(f"/egresos/eliminar/{egreso_id}")
        self.assertEqual(response.status_code, 404)

    def test_registration_rejects_short_password(self):
        response = self.client.post(
            "/registro",
            data={
                "username": "gabriel",
                "password": "corta",
                "password_confirm": "corta",
            },
        )
        self.assertEqual(response.status_code, 400)
        with self.app.app_context():
            self.assertIsNone(db.session.scalar(select(Cuenta.id)))


if __name__ == "__main__":
    unittest.main()
