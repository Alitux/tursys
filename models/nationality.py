# -*- coding: utf-8 -*-
from odoo import models, fields

class TursysNationality(models.Model):
    _name = 'tursys.nationality'
    _description = 'Nationality'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
