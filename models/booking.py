# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TursysBooking(models.Model):
    _name = 'tursys.booking'
    _description = 'Excursion Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    qr_uuid = fields.Char(string='QR UUID', readonly=True, copy=False, default=lambda self: str(uuid.uuid4()))
    
    excursion_id = fields.Many2one('tursys.excursion', string='Excursion', required=True, tracking=True)
    
    # Technical field for billing, pre-filled with passenger
    partner_id = fields.Many2one('res.partner', string='Customer / Payer', tracking=True)
    
    # The Passenger is the main actor
    passenger_id = fields.Many2one('res.partner', string='Passenger', required=True, tracking=True)
    
    # Related fields from the partner record
    passenger_vat = fields.Char(related='passenger_id.vat', string='ID / VAT', readonly=False, store=True)
    passenger_birthdate = fields.Date(related='passenger_id.birthdate', string='Birthdate', readonly=False, store=True)
    passenger_nationality_id = fields.Many2one(related='passenger_id.nationality_id', string='Nationality', readonly=False, store=True)
    passenger_language_id = fields.Many2one(related='passenger_id.language_id', string='Language', readonly=False, store=True)
    passenger_special_needs = fields.Text(related='passenger_id.special_needs', string='Medical / Dietary Needs', readonly=False, store=True)
    
    observations = fields.Text(string='Booking Observations')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tursys.booking') or _('New')
            if not vals.get('qr_uuid'):
                vals['qr_uuid'] = str(uuid.uuid4())
        return super().create(vals_list)

    @api.onchange('passenger_id')
    def _onchange_passenger_id(self):
        if self.passenger_id and not self.partner_id:
            self.partner_id = self.passenger_id

    def action_confirm(self):
        for record in self:
            if record.excursion_id.capacity_available < 1:
                raise ValidationError(_("Not enough capacity available in this excursion!"))
            record.state = 'confirmed'

    def action_cancel(self):
        self.write({'state': 'cancelled'})
