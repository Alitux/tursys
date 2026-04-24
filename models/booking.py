# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TursysBooking(models.Model):
    _name = 'tursys.booking'
    _description = 'Excursion Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    excursion_id = fields.Many2one('tursys.excursion', string='Excursion', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    pax_count = fields.Integer(string='PAX Count', compute='_compute_pax_count', store=True, tracking=True)
    pax_ids = fields.One2many('tursys.passenger', 'booking_id', string='Passengers')
    
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
        return super().create(vals_list)

    @api.depends('pax_ids')
    def _compute_pax_count(self):
        for record in self:
            record.pax_count = len(record.pax_ids)

    def action_confirm(self):
        for record in self:
            if record.excursion_id.capacity_available < record.pax_count:
                raise ValidationError(_("Not enough capacity available in this excursion!"))
            record.state = 'confirmed'

    def action_cancel(self):
        self.write({'state': 'cancelled'})
