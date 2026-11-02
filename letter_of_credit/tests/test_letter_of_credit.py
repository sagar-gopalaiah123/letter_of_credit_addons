
from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase


class TestLetterOfCredit(TransactionCase):
    """Automated tests for the Letter of Credit module."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.currency = cls.company.currency_id

        cls.partner = cls.env["res.partner"].create({
            "name": "LC Automated Test Partner",
        })

        cls.bank = cls.env["res.bank"].create({
            "name": "LC Automated Test Bank",
            "y_house_bank": True,
        })

    def create_letter_of_credit(self, **kwargs):
        """Create a Letter of Credit test record."""

        today = fields.Date.today()

        vals = {
            "y_name": "TEST-LC-001",
            "y_boe_id": "BOE-TEST-001",
            "y_description": "Automated test Letter of Credit",
            "y_transaction_type": "purchase",
            "y_partner_id": self.partner.id,
            "y_issuing_bank_id": self.bank.id,
            "y_company_id": self.company.id,
            "y_currency_id": self.currency.id,
            "y_exchange_rate": 1.25,
            "y_lc_boe_value": 1000.0,
            "y_date_of_issue": today,
            "y_expiry_date": today + timedelta(days=30),
        }

        vals.update(kwargs)

        return self.env["letter.of.credit"].create(vals)

    def test_01_create_letter_of_credit(self):
        """Check Letter of Credit creation."""

        lc = self.create_letter_of_credit()

        self.assertTrue(lc.id)
        self.assertEqual(lc.y_name, "TEST-LC-001")
        self.assertEqual(lc.y_boe_id, "BOE-TEST-001")
        self.assertEqual(lc.y_state, "draft")
        self.assertTrue(lc.active)

    def test_02_calculate_local_currency_value(self):
        """Check FCY to LCY conversion."""

        lc = self.create_letter_of_credit(
            y_lc_boe_value=1000.0,
            y_exchange_rate=1.25,
        )

        self.assertAlmostEqual(
            lc.y_lcy_value,
            1250.0,
            places=2,
        )

    def test_03_calculate_remaining_fcy_value(self):
        """Check remaining foreign currency value."""

        lc = self.create_letter_of_credit(
            y_lc_boe_value=1000.0,
            y_exchange_rate=1.25,
        )

        self.assertAlmostEqual(
            lc.y_remaining_fcy_value,
            1000.0,
            places=2,
        )

    def test_04_calculate_remaining_lcy_value(self):
        """Check remaining local currency value."""

        lc = self.create_letter_of_credit(
            y_lc_boe_value=1000.0,
            y_exchange_rate=1.25,
        )

        self.assertAlmostEqual(
            lc.y_remaining_lcy_value,
            1250.0,
            places=2,
        )

    def test_05_update_remaining_value_after_amount_change(self):
        """Check remaining values after changing LC amount."""

        lc = self.create_letter_of_credit()

        lc.write({
            "y_lc_boe_value": 2000.0,
        })

        self.assertAlmostEqual(
            lc.y_remaining_fcy_value,
            2000.0,
            places=2,
        )

        self.assertAlmostEqual(
            lc.y_lcy_value,
            2500.0,
            places=2,
        )

    def test_06_validate_issue_date_and_expiry_date(self):
        """Expiry date must not be earlier than issue date."""

        today = fields.Date.today()

        with self.assertRaises(ValidationError):
            self.create_letter_of_credit(
                y_date_of_issue=today + timedelta(days=5),
                y_expiry_date=today + timedelta(days=2),
            )

    def test_07_confirm_letter_of_credit(self):
        """Check the Confirm action."""

        lc = self.create_letter_of_credit()

        self.assertEqual(lc.y_state, "draft")

        lc.action_confirm()

        self.assertEqual(lc.y_state, "confirmed")

    def test_08_house_bank_field(self):
        """Check the custom House Bank field."""

        self.assertTrue(self.bank.y_house_bank)

    
    def test_09_expired_letter_of_credit_becomes_inactive(self):
        """Check expiry onchange logic."""

        today = fields.Date.today()
        expiry_date = today - timedelta(days=1)

        lc = self.create_letter_of_credit(
            y_date_of_issue=expiry_date - timedelta(days=30),
            y_expiry_date=expiry_date,
        )

        lc._onchange_active()

        self.assertFalse(lc.active)


    def test_10_valid_letter_of_credit_remains_active(self):
        """Check that a future expiry date keeps the LC active."""

        lc = self.create_letter_of_credit(
            y_expiry_date=fields.Date.today() + timedelta(days=30),
        )

        lc._onchange_active()

        self.assertTrue(lc.active)

    def test_11_purchase_order_integration_field(self):
        """Check the Purchase Order integration field exists."""

        self.assertIn(
            "y_letter_of_credit_id",
            self.env["purchase.order"]._fields,
        )

    def test_12_sale_order_integration_field(self):
        """Check the Sales Order integration field exists."""

        self.assertIn(
            "y_letter_of_credit_id",
            self.env["sale.order"]._fields,
        )

    def test_13_account_move_integration_field(self):
        """Check the Account Move integration field exists."""

        self.assertIn(
            "y_letter_of_credit_id",
            self.env["account.move"]._fields,
        )

    def test_14_bank_integration_field(self):
        """Check the Res Bank integration field exists."""

        self.assertIn(
            "y_house_bank",
            self.env["res.bank"]._fields,
        )
