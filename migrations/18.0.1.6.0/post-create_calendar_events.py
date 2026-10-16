# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Genera el evento de calendario de las excursiones que ya existían."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    excursions = env['tursys.excursion'].search([('state', '!=', 'cancelled')])
    excursions._sync_calendar_event()
