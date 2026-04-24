# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class ResPartner(models.Model):
    _inherit = 'res.partner'

    birthdate = fields.Date(string='Birthdate')
    age = fields.Integer(string='Age', compute='_compute_age', store=False)
    special_needs = fields.Text(string='Special Needs')
    nationality_id = fields.Many2one('tursys.nationality', string='Nationality')
    language_id = fields.Many2one('tursys.language', string='Main Language')

    @api.depends('birthdate')
    def _compute_age(self):
        today = date.today()
        for record in self:
            if record.birthdate:
                record.age = today.year - record.birthdate.year - ((today.month, today.day) < (record.birthdate.month, record.birthdate.day))
            else:
                record.age = 0
