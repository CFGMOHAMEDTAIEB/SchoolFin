import os
import tempfile
import unittest

from schoolfin.services.payment_service import (
    compute_due_amount,
    create_class,
    create_student,
    format_payment_frequency,
    list_students_by_class,
    normalize_payment_frequency,
)


class PaymentPeriodHelpersTests(unittest.TestCase):
    def test_normalize_payment_frequency(self):
        self.assertEqual(normalize_payment_frequency("Mensuel"), "monthly")
        self.assertEqual(normalize_payment_frequency("Trimestriel"), "quarterly")
        self.assertEqual(normalize_payment_frequency("Annuel"), "yearly")

    def test_format_payment_frequency(self):
        self.assertEqual(format_payment_frequency("monthly"), "Mensuel")
        self.assertEqual(format_payment_frequency("quarterly"), "Trimestriel")
        self.assertEqual(format_payment_frequency("yearly"), "Annuel")

    def test_compute_due_amount_by_frequency(self):
        self.assertEqual(compute_due_amount("monthly"), 300.0)
        self.assertEqual(compute_due_amount("quarterly"), 900.0)
        self.assertEqual(compute_due_amount("yearly"), 3600.0)

    def test_create_student_persists_profile_details(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            os.environ["SCHOOLFIN_DB_PATH"] = os.path.join(tmpdir, "schoolfin.sqlite")
            from schoolfin.db.db import init_db

            init_db()
            class_id = create_class("Classe A")
            student_id = create_student(
                class_id,
                "Amina Ben Ali",
                "22123456",
                "monthly",
                address="12 rue de la Liberté",
                birth_date="2005-05-10",
                parent_name="Samir Ben Ali",
                parent_phone="98765432",
                notes="Transport scolaire",
            )

            rows = list_students_by_class()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["id"], student_id)
            self.assertEqual(rows[0]["address"], "12 rue de la Liberté")
            self.assertEqual(rows[0]["birth_date"], "2005-05-10")
            self.assertEqual(rows[0]["parent_name"], "Samir Ben Ali")
            self.assertEqual(rows[0]["parent_phone"], "98765432")
            self.assertEqual(rows[0]["notes"], "Transport scolaire")


if __name__ == "__main__":
    unittest.main()
