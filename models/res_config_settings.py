# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tursys_child_price_rate = fields.Float(
        string='Child Price (%)', default=50.0,
        config_parameter='tursys.child_price_rate',
        help="Percentage of the adult price that a child (3 to 12 years old) pays.",
    )
    tursys_infant_price_rate = fields.Float(
        string='Infant Price (%)', default=0.0,
        config_parameter='tursys.infant_price_rate',
        help="Percentage of the adult price that an infant (0 to 2 years old) pays.",
    )
    tursys_retiree_price_rate = fields.Float(
        string='Retiree Price (%)', default=80.0,
        config_parameter='tursys.retiree_price_rate',
        help="Percentage of the adult price that a retiree pays.",
    )
    tursys_disabled_price_rate = fields.Float(
        string='Disabled Price (%)', default=100.0,
        config_parameter='tursys.disabled_price_rate',
        help="Percentage of the adult price that a person with a disability pays.",
    )
