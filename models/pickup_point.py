# -*- coding: utf-8 -*-
from odoo import models, fields


class TursysPickupPoint(models.Model):
    _name = 'tursys.pickup.point'
    _description = 'Pickup Point'
    _order = 'name'

    name = fields.Char(
        string='Name', required=True,
        help="Name of the place (hotel, hostel, meeting point...).",
    )
    address = fields.Char(
        string='Address',
        help="Address of the pickup point.",
    )
    active = fields.Boolean(string='Active', default=True)
