# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
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

    @api.depends('booking_ids', 'booking_ids.state')
    def _compute_capacity_used(self):
        for record in self:
            record.capacity_used = len(record.booking_ids.filtered(lambda b: b.state == 'confirmed'))

    @api.depends('capacity_total', 'capacity_used')
    def _compute_capacity_available(self):
        for record in self:
            record.capacity_available = record.capacity_total - record.capacity_used

    def action_done(self):
        self.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})
