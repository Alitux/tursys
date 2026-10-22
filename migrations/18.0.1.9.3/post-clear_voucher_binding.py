# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """El voucher deja de aparecer en el menú Print de lista/kanban.

    Se imprime solo desde el botón del formulario (oculto en borrador y
    cancelado). Quitar el campo del XML no lo borra en la DB, por eso se
    limpia explícitamente. binding_type es NOT NULL, así que solo se quita
    binding_model_id (el menú Print se arma con ese campo).
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    report = env.ref('tursys.action_report_booking_voucher', raise_if_not_found=False)
    if report:
        report.write({'binding_model_id': False})
