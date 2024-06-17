# Copyright 2024 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "MRP Lot expiry date",
    "summary": "Compute expiration date of lot based on scheduled date.",
    "version": "16.0.1.0.0",
    "category": "Manufacturing",
    "website": "https://github.com/OCA/manufacture",
    "author": "Therp BV, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "mrp",
        "product_expiry",
    ],
    "data": [
        "views/mrp_production.xml",
    ],
}
