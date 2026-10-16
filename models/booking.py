# -*- coding: utf-8 -*-
import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import date


class TursysBooking(models.Model):
    _name = 'tursys.booking'
    _description = 'Excursion Booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Booking Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    qr_uuid = fields.Char(string='QR UUID', readonly=True, copy=False, default=lambda self: str(uuid.uuid4()))

    excursion_id = fields.Many2one('tursys.excursion', string='Excursion', required=True, tracking=True)

    passenger_id = fields.Many2one('res.partner', string='Linked Passenger', readonly=True, copy=False)

    pax_name = fields.Char(string='Passenger Name', required=True, tracking=True)
    pax_vat = fields.Char(string='ID / VAT', required=True, tracking=True)
    pax_email = fields.Char(string='Email', tracking=True)
    pax_phone = fields.Char(string='Phone', tracking=True)
    pax_birthdate = fields.Date(string='Birthdate')
    pax_age = fields.Integer(string='Age', compute='_compute_pax_age', store=True)

    pax_nationality_id = fields.Many2one('tursys.nationality', string='Nationality')
    pax_language_id = fields.Many2one('tursys.language', string='Language')
    pax_special_needs = fields.Text(string='Medical / Dietary Needs')

    observations = fields.Text(string='Booking Observations')

    pickup_place = fields.Char(
        string='Pickup Point', tracking=True,
        help="Name of the place where the passenger will be picked up (hotel, hostel, etc.).",
    )
    pickup_address = fields.Char(
        string='Pickup Address', tracking=True,
        help="Address of the pickup point, when it applies.",
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting List'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

    payment_status = fields.Selection([
        ('unpaid', 'Not Paid'),
        ('deposit', 'Deposit'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ], string='Payment Status', default='unpaid', tracking=True)

    cancellation_reason = fields.Selection([
        ('customer', 'Customer decision'),
        ('agency', 'Agency decision'),
        ('min_not_reached', 'Minimum not reached'),
        ('weather', 'Weather conditions'),
        ('other', 'Other'),
    ], string='Cancellation Reason', tracking=True)
    cancellation_note = fields.Text(string='Cancellation Note')

    checkin_datetime = fields.Datetime(string='Check-in Time', readonly=True, copy=False)
    checked_in_by = fields.Many2one('res.users', string='Checked in by', readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('pax_birthdate')
    def _compute_pax_age(self):
        today = date.today()
        for record in self:
            if record.pax_birthdate:
                record.pax_age = today.year - record.pax_birthdate.year - (
                    (today.month, today.day) < (record.pax_birthdate.month, record.pax_birthdate.day)
                )
            else:
                record.pax_age = 0

    @api.onchange('pax_vat')
    def _onchange_pax_vat(self):
        if self.pax_vat:
            partner = self.env['res.partner'].search([('vat', '=', self.pax_vat)], limit=1)
            if partner:
                self.pax_name = partner.name
                self.pax_email = partner.email
                self.pax_phone = partner.phone
                self.pax_birthdate = partner.birthdate
                self.pax_nationality_id = partner.nationality_id
                self.pax_language_id = partner.language_id
                self.pax_special_needs = partner.special_needs
                return {
                    'warning': {
                        'title': _("Passenger Found"),
                        'message': _("A passenger with this ID already exists. Data has been pre-filled.")
                    }
                }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tursys.booking') or _('New')
            if not vals.get('qr_uuid'):
                vals['qr_uuid'] = str(uuid.uuid4())
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _lock_excursion(self):
        """Bloqueo pesimista de la excursión para evitar sobreventa por concurrencia."""
        self.ensure_one()
        self.env.cr.execute(
            "SELECT id FROM tursys_excursion WHERE id = %s FOR UPDATE",
            (self.excursion_id.id,),
        )
        self.excursion_id.invalidate_recordset(['capacity_used', 'capacity_available'])

    def _find_or_create_partner(self):
        """Busca el contacto por DNI/VAT y lo vincula, sin pisar datos ya cargados."""
        self.ensure_one()
        Partner = self.env['res.partner']
        partner = Partner.search([('vat', '=', self.pax_vat)], limit=1)

        partner_vals = {
            'name': self.pax_name,
            'vat': self.pax_vat,
            'email': self.pax_email,
            'phone': self.pax_phone,
            'birthdate': self.pax_birthdate,
            'nationality_id': self.pax_nationality_id.id,
            'language_id': self.pax_language_id.id,
            'special_needs': self.pax_special_needs,
            'is_company': False,
        }

        if partner:
            partner_vals = {key: value for key, value in partner_vals.items() if not partner[key]}
            if partner_vals:
                partner.write(partner_vals)
        else:
            partner = Partner.create(partner_vals)

        self.passenger_id = partner.id

    # ------------------------------------------------------------------
    # Workflow
    # ------------------------------------------------------------------
    def action_confirm(self):
        for record in self:
            if record.state not in ('draft', 'waiting'):
                continue

            record._lock_excursion()

            if record.excursion_id.capacity_available < 1:
                raise ValidationError(_("Not enough capacity available in this excursion!"))

            record._find_or_create_partner()
            record.write({'state': 'confirmed'})

    def action_waitlist(self):
        self.filtered(lambda b: b.state == 'draft').write({'state': 'waiting'})

    def action_check_in(self, user=None):
        now = fields.Datetime.now()
        user = user or self.env.user
        for record in self:
            if record.state != 'confirmed':
                continue
            record.write({
                'state': 'attended',
                'checkin_datetime': now,
                'checked_in_by': user.id,
            })

    def action_undo_check_in(self):
        self.filtered(lambda b: b.state == 'attended').write({
            'state': 'confirmed',
            'checkin_datetime': False,
            'checked_in_by': False,
        })

    def action_mark_no_show(self):
        for record in self:
            if record.state not in ('confirmed', 'attended'):
                continue
            record.write({'state': 'no_show'})
        self.excursion_id._promote_from_waitlist()

    def action_cancel(self):
        for record in self:
            if record.state == 'cancelled':
                continue
            freed_seat = record.state in ('confirmed', 'attended')
            record.write({'state': 'cancelled'})
            if freed_seat:
                record.excursion_id._promote_from_waitlist()

    def action_reset_draft(self):
        self.filtered(lambda b: b.state != 'draft').write({
            'state': 'draft',
            'checkin_datetime': False,
            'checked_in_by': False,
        })

    def action_send_voucher_email(self):
        self.ensure_one()
        template_id = self.env.ref('tursys.email_template_booking_voucher', raise_if_not_found=False)
        if not template_id:
            raise ValidationError(_("Email template not found! Please update the module."))

        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': {
                'default_model': 'tursys.booking',
                'default_res_id': self.id,
                'default_use_template': True,
                'default_template_id': template_id.id,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }
