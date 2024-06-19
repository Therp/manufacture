# Copyright 2024 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import datetime

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    update_expiration_date = fields.Boolean(
        string="Lot Expiration Date on Scheduled Date",
        help="Updates expiration date of lot based on planned date",
        default=True,
    )
    lot_producing_id_expiration_date = fields.Datetime(
        related="lot_producing_id.expiration_date",
        string="Lot Expiration Date",
        readonly=True,
    )

    def write(self, vals):
        res = super().write(vals)
        if not any(["date_planned_start" in vals, "lot_producing_id" in vals]):
            return res
        for production in self:
            if not production.update_expiration_date:
                continue
            expiration_set = (
                production.lot_producing_id.product_id.product_tmpl_id.use_expiration_date
            )
            if not expiration_set:
                continue
            expiration_time = (
                production.lot_producing_id.product_id.product_tmpl_id.expiration_time
            )
            production.lot_producing_id.expiration_date = (
                production.date_planned_start + datetime.timedelta(days=expiration_time)
            )
        return res
