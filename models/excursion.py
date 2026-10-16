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
    capacity_used = fields.Integer(string='Used Capacity', compute='_compute_capacity', store=True)
    capacity_available = fields.Integer(string='Available Capacity', compute='_compute_capacity', store=True)

    booking_count = fields.Integer(string='Total Bookings', compute='_compute_capacity', store=True)
    waiting_count = fields.Integer(string='Waiting List', compute='_compute_capacity', store=True)
    attended_count = fields.Integer(string='Attended', compute='_compute_capacity', store=True)
    no_show_count = fields.Integer(string='No Show', compute='_compute_capacity', store=True)

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

    @api.depends('booking_ids', 'booking_ids.state', 'capacity_total')
    def _compute_capacity(self):
        for record in self:
            bookings = record.booking_ids
            # Ocupan cupo las reservas confirmadas y las que ya se presentaron.
            used = len(bookings.filtered(lambda b: b.state in ('confirmed', 'attended')))
            record.capacity_used = used
            record.capacity_available = record.capacity_total - used
            record.booking_count = len(bookings.filtered(lambda b: b.state != 'cancelled'))
            record.waiting_count = len(bookings.filtered(lambda b: b.state == 'waiting'))
            record.attended_count = len(bookings.filtered(lambda b: b.state == 'attended'))
            record.no_show_count = len(bookings.filtered(lambda b: b.state == 'no_show'))

    def _promote_from_waitlist(self):
        """Asciende reservas de la lista de espera mientras haya cupo libre."""
        self.ensure_one()
        while self.capacity_available > 0:
            waiting = self.booking_ids.filtered(lambda b: b.state == 'waiting').sorted('create_date')[:1]
            if not waiting:
                break
            waiting.action_confirm()

    def action_done(self):
        for record in self:
            record.booking_ids.filtered(lambda b: b.state == 'confirmed').write({'state': 'no_show'})
            record.state = 'done'

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_open_bookings(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bookings'),
            'res_model': 'tursys.booking',
            'view_mode': 'list,form',
            'domain': [('excursion_id', '=', self.id)],
            'context': {'default_excursion_id': self.id, 'hide_excursion': True},
        }

    def action_open_checkin(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Check-in'),
            'res_model': 'tursys.booking',
            'view_mode': 'kanban,list,form',
            'domain': [('excursion_id', '=', self.id)],
            'context': {'default_excursion_id': self.id, 'hide_excursion': True},
        }

    @api.model
    def _cron_close_past_excursions(self):
        """Cierra excursiones vencidas y marca como Ausente a los que no hicieron check-in."""
        now = fields.Datetime.now()
        past = self.search([('state', '=', 'scheduled'), ('end_datetime', '<', now)])
        for excursion in past:
            excursion.booking_ids.filtered(lambda b: b.state == 'confirmed').write({'state': 'no_show'})
            excursion.state = 'done'
