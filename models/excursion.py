# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError
from datetime import timedelta


class TursysExcursion(models.Model):
    _name = 'tursys.excursion'
    _description = 'Excursion Instance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
        ('in_progress', 'In Progress'),
        ('done', 'Finished'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True, tracking=True)

    actual_start_datetime = fields.Datetime(string='Actual Start', readonly=True, copy=False)
    actual_end_datetime = fields.Datetime(string='Actual End', readonly=True, copy=False)
    started_by = fields.Many2one('res.users', string='Started by', readonly=True, copy=False)
    ended_by = fields.Many2one('res.users', string='Finished by', readonly=True, copy=False)

    booking_ids = fields.One2many('tursys.booking', 'excursion_id', string='Bookings')

    service_name = fields.Char(string='Service Name', compute='_compute_service_name', store=True)

    guide_id = fields.Many2one('res.users', string='Responsible Guide', tracking=True)
    assistant_guide_ids = fields.Many2many(
        'res.users', 'tursys_excursion_assistant_guide_rel',
        'excursion_id', 'user_id', string='Assistant Guides', tracking=True,
    )
    calendar_event_id = fields.Many2one(
        'calendar.event', string='Calendar Event', readonly=True, copy=False,
    )

    _CALENDAR_FIELDS = {
        'start_datetime', 'duration', 'product_id',
        'guide_id', 'assistant_guide_ids', 'state',
    }

    # ------------------------------------------------------------------
    # Guías: actividades automáticas al asignar
    # ------------------------------------------------------------------
    def _guide_users(self):
        self.ensure_one()
        return self.guide_id | self.assistant_guide_ids

    def _schedule_guide_activity(self, users):
        """Crea una actividad (y su notificación) para cada guía recién asignado."""
        self.ensure_one()
        users = users.filtered(lambda u: u and u.active)
        if not users:
            return
        activity_type = self.env.ref('tursys.mail_activity_type_excursion_assigned', raise_if_not_found=False)
        deadline = self.start_datetime.date() if self.start_datetime else fields.Date.context_today(self)
        for user in users:
            self.sudo().activity_schedule(
                activity_type_id=activity_type.id if activity_type else False,
                user_id=user.id,
                summary=_('Excursion assigned: %s') % self.name,
                note=_('You have been assigned to the excursion "%s".') % self.name,
                date_deadline=deadline,
            )

    def _remove_guide_activity(self, users):
        """Elimina las actividades pendientes de guías que fueron desasignados."""
        self.ensure_one()
        users = users.filtered(lambda u: u)
        if not users:
            return
        pending = self.sudo().activity_ids.filtered(lambda a: a.user_id in users)
        if pending:
            pending.unlink()

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            record._schedule_guide_activity(record._guide_users())
        records._sync_calendar_event()
        return records

    def write(self, vals):
        guides_changed = 'guide_id' in vals or 'assistant_guide_ids' in vals
        previous = {record.id: record._guide_users() for record in self} if guides_changed else {}
        result = super().write(vals)
        if guides_changed:
            for record in self:
                before = previous.get(record.id, self.env['res.users'])
                after = record._guide_users()
                record._schedule_guide_activity(after - before)
                record._remove_guide_activity(before - after)
        if self._CALENDAR_FIELDS & set(vals):
            self._sync_calendar_event()
        return result

    # ------------------------------------------------------------------
    # Calendario: evento automático por excursión
    # ------------------------------------------------------------------
    def _calendar_attendee_partners(self):
        self.ensure_one()
        return (self.guide_id | self.assistant_guide_ids).mapped('partner_id')

    def _sync_calendar_event(self):
        """Crea o actualiza el evento de calendario de cada excursión (o lo borra si se canceló)."""
        Event = self.env['calendar.event'].sudo()
        model_id = self.env['ir.model']._get_id('tursys.excursion')
        for record in self:
            if record.state == 'cancelled':
                record.calendar_event_id.sudo().unlink()
                continue
            if not record.start_datetime:
                continue
            stop = record.end_datetime or (record.start_datetime + timedelta(hours=1))
            if stop <= record.start_datetime:
                stop = record.start_datetime + timedelta(hours=1)
            vals = {
                'name': record.product_id.name or record.name,
                'start': record.start_datetime,
                'stop': stop,
                'description': record.name,
                'user_id': (record.guide_id or self.env.user).id,
                'partner_ids': [(6, 0, record._calendar_attendee_partners().ids)],
                'res_model_id': model_id,
                'res_id': record.id,
            }
            if record.calendar_event_id:
                record.calendar_event_id.sudo().with_context(dont_notify=True).write(vals)
            else:
                record.calendar_event_id = Event.with_context(dont_notify=True).create(vals)

    @api.depends('start_datetime', 'duration')
    def _compute_end_datetime(self):
        for record in self:
            if record.start_datetime:
                record.end_datetime = record.start_datetime + timedelta(hours=record.duration or 0)
            else:
                record.end_datetime = False

    @api.depends('product_id')
    def _compute_name(self):
        for record in self:
            record.name = record.product_id.name or "New Excursion"

    @api.depends('product_id', 'product_id.name')
    def _compute_service_name(self):
        for record in self:
            record.service_name = record.product_id.name

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

    def _ensure_can_manage(self, user):
        """Sólo el guía responsable (o un usuario interno) puede iniciar/finalizar."""
        self.ensure_one()
        if user.has_group('base.group_user'):
            return
        if self.guide_id != user:
            raise AccessError(_("Only the responsible guide can start or finish this excursion."))

    def action_start_excursion(self, user=None):
        """El guía responsable inicia la excursión y se registra la hora real de inicio."""
        user = user or self.env.user
        for record in self:
            if record.state != 'scheduled':
                continue
            record._ensure_can_manage(user)
            record.write({
                'state': 'in_progress',
                'actual_start_datetime': fields.Datetime.now(),
                'started_by': user.id,
            })

    def action_finish_excursion(self, user=None):
        """Finaliza la excursión: registra la hora real y marca Ausente a los que no se presentaron."""
        user = user or self.env.user
        for record in self:
            if record.state not in ('scheduled', 'in_progress'):
                continue
            record._ensure_can_manage(user)
            record.booking_ids.filtered(lambda b: b.state == 'confirmed').write({'state': 'no_show'})
            record.write({
                'state': 'done',
                'actual_end_datetime': fields.Datetime.now(),
                'ended_by': user.id,
            })

    def action_done(self):
        """Botón 'Finish' del backend: delega en el cierre con registro de hora real."""
        self.action_finish_excursion()

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

    def action_open_portal_preview(self):
        """Abre la vista del portal (la que ve el guía) para esta excursión."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/my/excursions/%s' % self.id,
            'target': 'new',
        }

    @api.model
    def _cron_close_past_excursions(self):
        """Cierra excursiones vencidas y marca como Ausente a los que no hicieron check-in."""
        now = fields.Datetime.now()
        past = self.search([('state', 'in', ('scheduled', 'in_progress')), ('end_datetime', '<', now)])
        for excursion in past:
            excursion.booking_ids.filtered(lambda b: b.state == 'confirmed').write({'state': 'no_show'})
            excursion.write({
                'state': 'done',
                'actual_end_datetime': excursion.actual_end_datetime or now,
            })
