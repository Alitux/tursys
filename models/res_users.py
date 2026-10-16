# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    is_tursys_guide = fields.Boolean(
        string='TurSys Guide',
        compute='_compute_is_tursys_guide',
        store=True,
        help="Marca al usuario como guía de TurSys (puede asignársele excursiones). Puede ser un usuario de backend o un usuario portal.",
    )

    @api.depends('groups_id')
    def _compute_is_tursys_guide(self):
        guide_group = self.env.ref('tursys.group_tursys_guide', raise_if_not_found=False)
        for user in self:
            user.is_tursys_guide = bool(guide_group and guide_group in user.groups_id)
