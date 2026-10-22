# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

RATES = {
    'booking_source_web': 0.0,
    'booking_source_gyg': 25.0,
    'booking_source_viator': 20.0,
    'booking_source_other_agency': 0.0,
}


def migrate(cr, version):
    """Comisiones por origen + precio/comisión congelados en reservas existentes."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, rate in RATES.items():
        source = env.ref('tursys.%s' % xmlid, raise_if_not_found=False)
        if source:
            source.write({'commission_rate': rate})

    for booking in env['tursys.booking'].search([]):
        vals = {}
        if not booking.price_unit:
            vals['price_unit'] = booking.excursion_id.product_id.lst_price or 0.0
        if not booking.commission_rate and booking.source_id:
            vals['commission_rate'] = booking.source_id.commission_rate
        if vals:
            booking.write(vals)
