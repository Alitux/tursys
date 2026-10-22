# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Congela las tarifas por segmento en las reservas existentes y recalcula el total."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    Booking = env['tursys.booking']
    rates = Booking._get_price_rates()
    for booking in Booking.search([]):
        booking.write(dict(rates))
