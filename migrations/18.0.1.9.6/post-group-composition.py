# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

# Tipo de pasajero antiguo -> contador de la composición del grupo.
_TYPE_TO_COUNTER = {
    'infant': 'pax_infants',
    'child': 'pax_children',
    'adult': 'pax_adults',
}


def migrate(cr, version):
    """Completa la composición del grupo en las reservas existentes.

    Antes cada reserva tenía un único pasajero (pax_type). Ahora la reserva
    representa un grupo: el titular queda como 1 adulto, 1 niño o 1 infante
    según su tipo. Las reservas ya presentadas se marcan como 100% presentes.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})

    cr.execute("SELECT id, pax_type, state FROM tursys_booking")
    rows = cr.fetchall()

    Booking = env['tursys.booking']
    for booking_id, pax_type, state in rows:
        vals = {'pax_adults': 0, 'pax_children': 0, 'pax_infants': 0}
        counter = _TYPE_TO_COUNTER.get(pax_type)
        if counter:
            vals[counter] = 1
        else:
            vals['pax_adults'] = 1

        if state == 'attended':
            vals['attended_pax'] = (
                vals['pax_adults'] + vals['pax_children'] + vals['pax_infants']
            )

        Booking.browse(booking_id).write(vals)
