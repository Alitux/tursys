# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Elimina el menú backoffice 'Check-in', que ya no se usa.

    Quitar el <menuitem> del XML no borra el registro existente en la DB
    durante un upgrade, así que lo eliminamos explícitamente.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    menu = env.ref('tursys.menu_tursys_checkin', raise_if_not_found=False)
    if menu:
        menu.unlink()
