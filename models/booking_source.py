# -*- coding: utf-8 -*-
from odoo import fields, models


class TursysBookingSource(models.Model):
    _name = 'tursys.booking.source'
    _description = 'Booking Source'
    _order = 'sequence, name'

    name = fields.Char(string='Name', required=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    commission_rate = fields.Float(
        string='Commission (%)', digits=(16, 2), default=0.0,
        help="Commission charged by this source, as a percentage of the gross sale price.",
    )
