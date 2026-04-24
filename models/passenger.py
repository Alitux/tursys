# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TursysPassenger(models.Model):
    _name = 'tursys.passenger'
    _description = 'Passenger'

    booking_id = fields.Many2one('tursys.booking', string='Booking', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Passenger (Contact)', required=True)
    
    # Related fields to facilitate data entry and visibility
    name = fields.Char(related='partner_id.name', readonly=False, store=True)
    vat = fields.Char(related='partner_id.vat', string='ID / VAT', readonly=False, store=True)
    birthdate = fields.Date(related='partner_id.birthdate', readonly=False, store=True)
    
    observations = fields.Text(string='Observations')
