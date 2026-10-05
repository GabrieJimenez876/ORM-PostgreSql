import unittest

from sqlalchemy import select

from app import create_app
from models import Egreso, FormaPago, db


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

    def test_crud_and_search(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Aún no hay egresos", response.get_data(as_text=True))

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


if __name__ == "__main__":
    unittest.main()
