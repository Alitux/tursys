# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Completa el tipo de pasajero de las reservas existentes según su fecha de nacimiento."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    bookings = env['tursys.booking'].search([])
    bookings._compute_pax_type()
