# Copyright 2021 ForgeFlow S.L. (http://www.forgeflow.com)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import logging
import unittest

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tests.common import SavepointCase

from ..wizards.mrp_production_serial_matrix import MrpProductionSerialMatrix

_logger = logging.getLogger(__name__)


class TestMrpProductionSerialMatrix(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.mo_obj = cls.env["mrp.production"]
        cls.product_obj = cls.env["product.product"]
        cls.lot_obj = cls.env["stock.production.lot"]
        cls.quant_obj = cls.env["stock.quant"]
        cls.bom_obj = cls.env["mrp.bom"]
        cls.bom_line_obj = cls.env["mrp.bom.line"]
        cls.move_line_obj = cls.env["stock.move.line"]
        cls.wiz_obj = cls.env["mrp.production.serial.matrix"]

        cls.company = cls.env.ref("base.main_company")
        cls.stock_loc = cls.env.ref("stock.stock_location_stock")

        # Products and lots:
        cls.final_product = cls.product_obj.create(
            {
                "name": "Finished Product tracked by Serial Numbers",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.final_product_simple = cls.product_obj.create(
            {
                "name": "Finished Product tracked by Serial Numbers (simple version)",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.component_1_serial = cls.product_obj.create(
            {
                "name": "Component 1 tracked by Serial Numbers",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.serial_1_001 = cls._create_serial_number(cls.component_1_serial, "1-001")
        cls.serial_1_002 = cls._create_serial_number(cls.component_1_serial, "1-002")
        cls.serial_1_003 = cls._create_serial_number(cls.component_1_serial, "1-003")
        cls.component_2_serial = cls.product_obj.create(
            {
                "name": "Component 2 tracked by Serial Numbers",
                "type": "product",
                "tracking": "serial",
            }
        )
        cls.serial_2_001 = cls._create_serial_number(cls.component_2_serial, "2-001")
        cls.serial_2_002 = cls._create_serial_number(cls.component_2_serial, "2-002")
        cls.serial_2_003 = cls._create_serial_number(cls.component_2_serial, "2-003")
        cls.serial_2_004 = cls._create_serial_number(cls.component_2_serial, "2-004")
        cls.serial_2_005 = cls._create_serial_number(cls.component_2_serial, "2-005")
        cls.serial_2_006 = cls._create_serial_number(cls.component_2_serial, "2-006")
        cls.component_3_lot = cls.product_obj.create(
            {
                "name": "Component 3 tracked by Lots",
                "type": "product",
                "tracking": "lot",
            }
        )
        cls.lot_3_001 = cls._create_serial_number(
            cls.component_3_lot, "3-001", qty=10.0
        )
        cls.lot_3_002 = cls._create_serial_number(cls.component_3_lot, "3-002", qty=8.0)
        cls.lot_3_003 = cls._create_serial_number(
            cls.component_3_lot, "3-003", qty=12.0
        )
        cls.component_4_no_track = cls.product_obj.create(
            {
                "name": "Component 4 Not tracked",
                "type": "product",
                "tracking": "none",
            }
        )
        cls.quant_obj.create(
            {
                "product_id": cls.component_4_no_track.id,
                "location_id": cls.stock_loc.id,
                "quantity": 20.0,
            }
        )

        # BoM
        cls.bom_1 = cls.bom_obj.create(
            {
                "product_tmpl_id": cls.final_product.product_tmpl_id.id,
                "product_id": cls.final_product.id,
                "product_qty": 1.0,
            }
        )
        cls.bom_line_obj.create(
            {
                "bom_id": cls.bom_1.id,
                "product_id": cls.component_1_serial.id,
                "product_qty": 1.0,
            }
        )
        cls.bom_line_obj.create(
            {
                "bom_id": cls.bom_1.id,
                "product_id": cls.component_2_serial.id,
                "product_qty": 2.0,
            }
        )
        cls.bom_line_obj.create(
            {
                "bom_id": cls.bom_1.id,
                "product_id": cls.component_3_lot.id,
                "product_qty": 4.0,
            }
        )
        cls.bom_line_obj.create(
            {
                "bom_id": cls.bom_1.id,
                "product_id": cls.component_4_no_track.id,
                "product_qty": 1.0,
            }
        )
        # BoM 2 (simple BoM, only no tracking products)
        cls.bom_2 = cls.bom_obj.create(
            {
                "product_tmpl_id": cls.final_product_simple.product_tmpl_id.id,
                "product_id": cls.final_product_simple.id,
                "product_qty": 1.0,
            }
        )
        cls.bom_line_obj.create(
            {
                "bom_id": cls.bom_2.id,
                "product_id": cls.component_4_no_track.id,
                "product_qty": 4.0,
            }
        )

    @classmethod
    def _create_serial_number(cls, product, name, qty=1.0):
        lot = cls.lot_obj.create(
            {
                "product_id": product.id,
                "name": name,
                "company_id": cls.company.id,
            }
        )
        if qty > 0:
            cls.quant_obj.create(
                {
                    "product_id": product.id,
                    "location_id": cls.stock_loc.id,
                    "quantity": qty,
                    "lot_id": lot.id,
                }
            )
        return lot

    @classmethod
    def _create_mo(cls, product, qty):
        production_form = Form(cls.mo_obj)
        production_form.product_id = product
        production_form.bom_id = product.bom_ids[0]
        production_form.product_qty = qty
        production_form.product_uom_id = product.uom_id
        production_1 = production_form.save()
        production_1.action_confirm()
        production_1.action_assign()
        return production_1

    @classmethod
    def _find_move_lines(cls, mo, component):
        return cls.move_line_obj.search(
            [
                ("move_id.raw_material_production_id", "=", mo.id),
                ("product_id", "=", component.id),
            ]
        )

    def test_01_process_mo_with_matrix(self):
        """Extensive test including all the possibilities for components:
        - 1 tracked by serials.
        - 1 tracked by serials and needing more than one unit.
        - 1 tracked by lots.
        - 1 untracked.
        """
        production_1 = self._create_mo(self.final_product, 3.0)
        self.assertEqual(production_1.state, "confirmed")
        # Start matrix:
        wizard_form = Form(
            self.wiz_obj.with_context(
                active_id=production_1.id, active_model="mrp.production"
            )
        )
        expected = 3 * 3  # Only SN products (1 + 2 per finish unit)
        self.assertEqual(len(wizard_form.line_ids), expected)
        wizard_form.include_lots = True
        expected = 3 * 4
        self.assertEqual(len(wizard_form.line_ids), expected)
        self.assertEqual(wizard_form.lot_selection_warning_count, 0)
        serial_fp_1 = self._create_serial_number(self.final_product, "ABC101", qty=0)
        serial_fp_2 = self._create_serial_number(self.final_product, "ABC102", qty=0)
        wizard_form.finished_lot_ids.add(serial_fp_1)
        self.assertEqual(wizard_form.lot_selection_warning_count, 1)
        wizard_form.finished_lot_ids.add(serial_fp_2)
        self.assertEqual(wizard_form.lot_selection_warning_count, 2)
        wizard = wizard_form.save()
        lines = wizard.line_ids
        # Fill first row:
        cell_1_1 = lines.filtered(
            lambda l: l.finished_lot_id == serial_fp_1
            and l.component_id == self.component_1_serial
        )
        cell_1_1.component_lot_id = self.serial_1_001
        cell_1_2and3 = lines.filtered(
            lambda l: l.finished_lot_id == serial_fp_1
            and l.component_id == self.component_2_serial
        )
        self.assertEqual(len(cell_1_2and3), 2)
        for n, cell in enumerate(cell_1_2and3):
            if n == 0:
                cell.component_lot_id = self.serial_2_001
            elif n == 1:
                cell.component_lot_id = self.serial_2_002
        cell_1_4 = lines.filtered(
            lambda l: l.finished_lot_id == serial_fp_1
            and l.component_id == self.component_3_lot
        )
        cell_1_4.component_lot_id = self.lot_3_003

        # Fill second row:
        cell_2_1 = lines.filtered(
            lambda l: l.finished_lot_id == serial_fp_2
            and l.component_id == self.component_1_serial
        )
        # Simulate a mistake and select the same lot than before:
        cell_2_1.component_lot_id = self.serial_1_001
        cell_2_2and3 = lines.filtered(
            lambda l: l.finished_lot_id == serial_fp_2
            and l.component_id == self.component_2_serial
        )
        self.assertEqual(len(cell_2_2and3), 2)
        for n, cell in enumerate(cell_2_2and3):
            if n == 0:
                cell.component_lot_id = self.serial_2_005
            elif n == 1:
                cell.component_lot_id = self.serial_2_004
        cell_2_4 = lines.filtered(
            lambda l: l.finished_lot_id == serial_fp_2
            and l.component_id == self.component_3_lot
        )
        cell_2_4.component_lot_id = self.lot_3_002

        # There should be an error:
        self.assertEqual(wizard.lot_selection_warning_count, 1)
        with self.assertRaises(UserError):
            wizard.button_validate()

        # Fix error:
        cell_2_1.component_lot_id = self.serial_1_003

        # Validate and check result:
        wizard.button_validate()
        mos = production_1.procurement_group_id.mrp_production_ids
        self.assertEqual(len(mos), 3)
        mo_1 = mos.filtered(lambda mo: mo.lot_producing_id == serial_fp_1)
        self.assertEqual(mo_1.state, "done")
        ml_c1 = self._find_move_lines(mo_1, self.component_1_serial)
        self.assertEqual(ml_c1.qty_done, 1.0)
        self.assertEqual(ml_c1.lot_id, self.serial_1_001)
        ml_c2 = self._find_move_lines(mo_1, self.component_2_serial)
        self.assertEqual(len(ml_c2), 2)
        for ml in ml_c2:
            self.assertEqual(ml.qty_done, 1.0)
        self.assertEqual(ml_c2.mapped("lot_id"), self.serial_2_001 + self.serial_2_002)
        ml_c3 = self._find_move_lines(mo_1, self.component_3_lot)
        self.assertEqual(ml_c3.qty_done, 4.0)
        self.assertEqual(ml_c3.lot_id, self.lot_3_003)
        ml_c4 = self._find_move_lines(mo_1, self.component_4_no_track)
        self.assertEqual(ml_c4.qty_done, 1.0)
        self.assertFalse(ml_c4.lot_id)

        mo_2 = mos.filtered(lambda mo: mo.lot_producing_id == serial_fp_2)
        self.assertEqual(mo_2.state, "done")
        ml_c1 = self._find_move_lines(mo_2, self.component_1_serial)
        self.assertEqual(ml_c1.qty_done, 1.0)
        self.assertEqual(ml_c1.lot_id, self.serial_1_003)
        ml_c2 = self._find_move_lines(mo_2, self.component_2_serial)
        self.assertEqual(len(ml_c2), 2)
        for ml in ml_c2:
            self.assertEqual(ml.qty_done, 1.0)
        self.assertEqual(ml_c2.mapped("lot_id"), self.serial_2_005 + self.serial_2_004)
        ml_c3 = self._find_move_lines(mo_2, self.component_3_lot)
        self.assertEqual(ml_c3.qty_done, 4.0)
        self.assertEqual(ml_c3.lot_id, self.lot_3_002)
        ml_c4 = self._find_move_lines(mo_2, self.component_4_no_track)
        self.assertEqual(ml_c4.qty_done, 1.0)
        self.assertFalse(ml_c4.lot_id)

        # MO holding the remaining qty
        mo_3 = mos.filtered(lambda mo: not mo.lot_producing_id)
        self.assertEqual(mo_3.state, "confirmed")
        self.assertEqual(mo_3.product_qty, 1.0)

    def test_02_process_matrix_simple(self):
        """Simple test:
        - 1 product that is serially tracked
        - Consisting of 1 component that is not serially tracked
        - Produce 4 times
        """
        product = self.final_product_simple
        production_1 = self._create_mo(product, 4.0)
        self.assertEqual(production_1.state, "confirmed")
        serial1 = self._create_serial_number(product, "ABC201", qty=0)
        serial2 = self._create_serial_number(product, "ABC202", qty=0)
        serial3 = self._create_serial_number(product, "ABC203", qty=0)
        serial4 = self._create_serial_number(product, "ABC204", qty=0)

        wizard = self.wiz_obj.with_context(
            active_id=production_1.id, active_model="mrp.production"
        ).create({})
        lots = serial1 + serial2 + serial3 + serial4
        self.assertEqual(len(lots), 4)
        wizard.finished_lot_ids = lots
        self.assertEqual(wizard.product_id, self.final_product_simple)
        self.assertEqual(wizard.finished_lot_ids, lots)
        wizard.button_validate()

        mos = production_1.procurement_group_id.mrp_production_ids
        self.assertEqual(len(mos), 4)
        mo_1 = mos.filtered(lambda mo: mo.lot_producing_id == serial1)
        self.assertEqual(mo_1.state, "done")
        mo_2 = mos.filtered(lambda mo: mo.lot_producing_id == serial2)
        self.assertEqual(mo_2.state, "done")
        mo_3 = mos.filtered(lambda mo: mo.lot_producing_id == serial3)
        self.assertEqual(mo_3.state, "done")
        mo_4 = mos.filtered(lambda mo: mo.lot_producing_id == serial4)
        self.assertEqual(mo_4.state, "done")

    def test_03_process_matrix_partially(self):  # , fake_single_mo):
        """Simulate the case of one MO in the batch failing to confirm.
        In this case what should happen is that the process is stopped,
        and only the MO's that were successful so far, remain confirmed.
        The user should solve the problem and then be able to resume.
        """
        self.env["ir.config_parameter"].set_param(
            "mrp_production_serial_matrix.mrp_serial_matrix_allow_exceptions", True
        )
        product = self.final_product_simple
        production_1 = self._create_mo(product, 4.0)
        self.assertEqual(production_1.state, "confirmed")
        serial1 = self._create_serial_number(product, "ABC201", qty=0)
        serial2 = self._create_serial_number(product, "ABC202", qty=0)
        serial3 = self._create_serial_number(product, "ABC203", qty=0)
        serial4 = self._create_serial_number(product, "ABC204", qty=0)

        wizard = self.wiz_obj.with_context(
            active_id=production_1.id, active_model="mrp.production"
        ).create({})
        lots = serial1 + serial2 + serial3 + serial4
        wizard.finished_lot_ids = lots

        # Pretend to fail at the third serial
        def fail_decorator(method_to_decorate):
            def wrapper(self, *args, **kwargs):
                if args[1] == serial3:
                    raise Exception()
                return method_to_decorate(self, *args, **kwargs)

            return wrapper

        mocked = fail_decorator(MrpProductionSerialMatrix._validate_single_mo)
        with unittest.mock.patch.object(
            MrpProductionSerialMatrix, "_validate_single_mo", mocked
        ):
            res = wizard.button_validate()

        mos = production_1.procurement_group_id.mrp_production_ids
        self.assertEqual(len(mos), 3)
        mo_1 = mos.filtered(lambda mo: mo.lot_producing_id == serial1)
        self.assertEqual(mo_1.state, "done")
        mo_2 = mos.filtered(lambda mo: mo.lot_producing_id == serial2)
        self.assertEqual(mo_2.state, "done")
        mo_3 = mos.filtered(lambda mo: not mo.lot_producing_id)
        self.assertEqual(mo_3.product_qty, 2.0)
        self.assertEqual(res["res_id"], mo_3.id)
