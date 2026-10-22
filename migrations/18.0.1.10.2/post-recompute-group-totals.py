# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Recalcula personas y totales: las categorias de precio son aditivas."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    bookings = env['tursys.booking'].search([])
    bookings._compute_pax_count()
    bookings._compute_amounts()
