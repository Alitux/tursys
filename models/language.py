# -*- coding: utf-8 -*-
from odoo import models, fields

class TursysLanguage(models.Model):
    _name = 'tursys.language'
    _description = 'Language'
    _order = 'name'

    name = fields.Char(string='Name', required=True, translate=True)
    code = fields.Char(string='Code')
