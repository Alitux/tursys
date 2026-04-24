# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date

class TursysBooking(models.Model):
    _name = 'tursys.booking'
    _description = 'Excursion Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    qr_uuid = fields.Char(string='QR UUID', readonly=True, copy=False, default=lambda self: str(uuid.uuid4()))
    
    excursion_id = fields.Many2one('tursys.excursion', string='Excursion', required=True, tracking=True)
    
    passenger_id = fields.Many2one('res.partner', string='Linked Passenger', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Payer', groups="base.group_no_one")

    pax_name = fields.Char(string='Passenger Name', required=True, tracking=True)
    pax_vat = fields.Char(string='ID / VAT', required=True, tracking=True)
    pax_email = fields.Char(string='Email', tracking=True)
    pax_phone = fields.Char(string='Phone', tracking=True)
    pax_birthdate = fields.Date(string='Birthdate')
    pax_age = fields.Integer(string='Age', compute='_compute_pax_age')
    
    pax_nationality_id = fields.Many2one('tursys.nationality', string='Nationality')
    pax_language_id = fields.Many2one('tursys.language', string='Language')
    pax_special_needs = fields.Text(string='Medical / Dietary Needs')
    
    observations = fields.Text(string='Booking Observations')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    @api.depends('pax_birthdate')
    def _compute_pax_age(self):
        today = date.today()
        for record in self:
            if record.pax_birthdate:
                record.pax_age = today.year - record.pax_birthdate.year - ((today.month, today.day) < (record.pax_birthdate.month, record.pax_birthdate.day))
            else:
                record.pax_age = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tursys.booking') or _('New')
            if not vals.get('qr_uuid'):
                vals['qr_uuid'] = str(uuid.uuid4())
        return super().create(vals_list)

    def action_confirm(self):
        Partner = self.env['res.partner']
        for record in self:
            if record.excursion_id.capacity_available < 1:
                raise ValidationError(_("Not enough capacity available in this excursion!"))
            
            partner = Partner.search([('vat', '=', record.pax_vat)], limit=1)
            
            partner_vals = {
                'name': record.pax_name,
                'vat': record.pax_vat,
                'email': record.pax_email,
                'phone': record.pax_phone,
                'birthdate': record.pax_birthdate,
                'nationality_id': record.pax_nationality_id.id,
                'language_id': record.pax_language_id.id,
                'special_needs': record.pax_special_needs,
                'is_company': False,
            }
            
            if partner:
                partner.write(partner_vals)
            else:
                partner = Partner.create(partner_vals)
            
            record.write({
                'passenger_id': partner.id,
                'partner_id': partner.id,
                'state': 'confirmed'
            })

    def action_cancel(self):
        self.write({'state': 'cancelled'})
