# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import timedelta

class TursysExcursion(models.Model):
    _name = 'tursys.excursion'
    _description = 'Excursion Instance'
    _order = 'start_datetime desc'

    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    product_id = fields.Many2one(
        'product.product', string='Service', required=True, 
        domain=[('type', '=', 'service')]
    )
    
    start_datetime = fields.Datetime(string='Start Date & Time', required=True, default=fields.Datetime.now)
    duration = fields.Float(string='Duration (Hours)', default=1.0)
    end_datetime = fields.Datetime(string='End Date & Time', compute='_compute_end_datetime', store=True)

    capacity_total = fields.Integer(string='Total Capacity', required=True, default=10)
    capacity_used = fields.Integer(string='Used Capacity', compute='_compute_capacity_used', store=True)
    capacity_available = fields.Integer(string='Available Capacity', compute='_compute_capacity_available', store=True)
    
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('done', 'Finished'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True)

    booking_ids = fields.One2many('tursys.booking', 'excursion_id', string='Bookings')

    @api.depends('start_datetime', 'duration')
    def _compute_end_datetime(self):
        for record in self:
            if record.start_datetime:
                record.end_datetime = record.start_datetime + timedelta(hours=record.duration or 0)
            else:
                record.end_datetime = False

    @api.depends('product_id', 'start_datetime')
    def _compute_name(self):
        for record in self:
            if record.product_id and record.start_datetime:
                record.name = f"{record.product_id.name} - {record.start_datetime.strftime('%d-%m-%Y %H:%M')}"
            else:
                record.name = "New Excursion"

    @api.depends('booking_ids', 'booking_ids.state', 'booking_ids.pax_count')
    def _compute_capacity_used(self):
        for record in self:
            record.capacity_used = sum(record.booking_ids.filtered(lambda b: b.state == 'confirmed').mapped('pax_count'))

    @api.depends('capacity_total', 'capacity_used')
    def _compute_capacity_available(self):
        for record in self:
            record.capacity_available = record.capacity_total - record.capacity_used

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})


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

class TursysPassenger(models.Model):
    _name = 'tursys.passenger'
    _description = 'Passenger'

    booking_id = fields.Many2one('tursys.booking', string='Booking', required=True, ondelete='cascade')
    name = fields.Char(string='Passenger Name', required=True)
    document_number = fields.Char(string='ID / Passport')
    age = fields.Integer(string='Age')
    observations = fields.Text(string='Observations')
