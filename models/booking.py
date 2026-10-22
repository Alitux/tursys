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
    pax_type = fields.Selection([
        ('infant', 'Infant'),
        ('child', 'Child'),
        ('adult', 'Adult'),
    ], string='Passenger Type', compute='_compute_pax_type', store=True, readonly=False,
        help="Calculated from the birthdate: infant (0-2), child (3-12), adult (13+). "
             "You can change it manually.")
    pax_adults = fields.Integer(
        string='Adults', default=1, required=True, tracking=True,
        help="Adults in the group, including the holder.",
    )
    pax_children = fields.Integer(
        string='Children (3-12)', default=0, required=True, tracking=True,
    )
    pax_infants = fields.Integer(
        string='Infants (0-2)', default=0, required=True, tracking=True,
    )
    pax_retired = fields.Integer(
        string='Retirees', default=0, required=True, tracking=True,
        help="Retirees in the group. They are also counted as adults.",
    )
    pax_disabled = fields.Integer(
        string='Disabled', default=0, required=True, tracking=True,
        help="People with disabilities in the group, at any age.",
    )
    pax_count = fields.Integer(
        string='Total People', compute='_compute_pax_count', store=True,
        help="People in the group: adults + children + infants.",
    )
    pax_breakdown = fields.Char(
        string='Group Composition', compute='_compute_pax_breakdown',
        help="Group composition, ready to show in lists, reports and the portal.",
    )
    attended_pax = fields.Integer(
        string='People Present', default=0, copy=False, tracking=True,
        help="People who actually showed up. It can be lower than the total.",
    )
    no_show_pax = fields.Integer(
        string='People Absent', compute='_compute_no_show_pax', store=True,
    )

    pax_nationality_id = fields.Many2one('tursys.nationality', string='Nationality')
    pax_language_id = fields.Many2one('tursys.language', string='Language')
    pax_special_needs = fields.Text(string='Medical / Dietary Needs')

    observations = fields.Text(string='Booking Observations')

    source_id = fields.Many2one(
        'tursys.booking.source', string='Booking Source', tracking=True,
        ondelete='restrict',
        help="Where the booking came from (web, GYG, Viator, another agency...).",
    )

    pickup_place = fields.Many2one(
        'tursys.pickup.point', string='Pickup Point', tracking=True,
        ondelete='restrict',
        help="Pickup point from the catalog (hotel, hostel, meeting point...).",
    )
    pickup_free_place = fields.Char(
        string='Free Pickup Point', tracking=True,
        help="Pickup point that is not in the catalog. Enter its address manually.",
    )
    pickup_address = fields.Char(
        string='Pickup Address', tracking=True,
        help="Address of the pickup point. It is filled from the catalog, but you can edit it.",
    )
    pickup_display = fields.Char(
        string='Pickup', compute='_compute_pickup_display', store=True,
        help="Effective pickup point shown in lists, reports and the guide portal.",
    )

    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    price_unit = fields.Float(
        string='Unit Price', digits=(16, 2), tracking=True,
        help="Price per person. It is taken from the service when the booking is created and kept frozen if the service price changes later.",
    )
    amount_total = fields.Float(
        string='Total', compute='_compute_amounts', store=True, digits=(16, 2),
    )
    commission_rate = fields.Float(
        string='Commission (%)', digits=(16, 2), tracking=True,
        help="Commission charged by the booking source. It is copied from the source when the booking is created.",
    )
    commission_amount = fields.Float(
        string='Commission', compute='_compute_amounts', store=True, digits=(16, 2),
    )
    amount_net = fields.Float(
        string='Net Revenue', compute='_compute_amounts', store=True, digits=(16, 2),
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting List'),
        ('confirmed', 'Confirmed'),
        ('attended', 'Attended'),
        ('no_show', 'No Show'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)

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

    @api.depends('pax_birthdate')
    def _compute_pax_type(self):
        today = date.today()
        for record in self:
            if not record.pax_birthdate:
                record.pax_type = 'adult'
                continue
            born = record.pax_birthdate
            age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
            if age < 3:
                record.pax_type = 'infant'
            elif age <= 12:
                record.pax_type = 'child'
            else:
                record.pax_type = 'adult'

    @api.depends('pax_adults', 'pax_children', 'pax_infants')
    def _compute_pax_count(self):
        for record in self:
            record.pax_count = (
                (record.pax_adults or 0)
                + (record.pax_children or 0)
                + (record.pax_infants or 0)
            )

    @api.depends('pax_adults', 'pax_children', 'pax_infants', 'pax_retired', 'pax_disabled')
    def _compute_pax_breakdown(self):
        labels = (
            ('pax_adults', _('Adult'), _('Adults')),
            ('pax_children', _('Child'), _('Children')),
            ('pax_infants', _('Infant'), _('Infants')),
            ('pax_retired', _('Retiree'), _('Retirees')),
            ('pax_disabled', _('Disabled'), _('Disabled people')),
        )
        for record in self:
            parts = []
            for field_name, singular, plural in labels:
                count = record[field_name]
                if count:
                    parts.append('%s %s' % (count, singular if count == 1 else plural))
            record.pax_breakdown = ' \u00b7 '.join(parts)

    @api.depends('state', 'pax_count', 'attended_pax')
    def _compute_no_show_pax(self):
        for record in self:
            if record.state == 'no_show':
                record.no_show_pax = record.pax_count
            elif record.state == 'attended':
                record.no_show_pax = max(record.pax_count - record.attended_pax, 0)
            else:
                record.no_show_pax = 0

    @api.depends('pickup_place', 'pickup_free_place')
    def _compute_pickup_display(self):
        for record in self:
            record.pickup_display = record.pickup_free_place or record.pickup_place.name

    @api.onchange('pickup_place')
    def _onchange_pickup_place(self):
        if self.pickup_place:
            self.pickup_free_place = False
            self.pickup_address = self.pickup_place.address

    @api.onchange('pickup_free_place')
    def _onchange_pickup_free_place(self):
        if self.pickup_free_place:
            self.pickup_place = False

    @api.depends('price_unit', 'pax_count', 'commission_rate')
    def _compute_amounts(self):
        for record in self:
            total = (record.price_unit or 0.0) * (record.pax_count or 0)
            record.amount_total = total
            record.commission_amount = total * (record.commission_rate or 0.0) / 100.0
            record.amount_net = total - record.commission_amount

    @api.onchange('source_id')
    def _onchange_source_id(self):
        self.commission_rate = self.source_id.commission_rate if self.source_id else 0.0

    @api.onchange('excursion_id')
    def _onchange_excursion_id(self):
        if self.excursion_id and not self.price_unit:
            self.price_unit = self.excursion_id.product_id.lst_price

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

    @api.constrains('pax_adults', 'pax_children', 'pax_infants',
                    'pax_retired', 'pax_disabled', 'attended_pax')
    def _check_pax_counts(self):
        for record in self:
            counters = (record.pax_adults, record.pax_children, record.pax_infants,
                        record.pax_retired, record.pax_disabled)
            if any(count < 0 for count in counters):
                raise ValidationError(_("The number of people cannot be negative."))
            if record.pax_count < 1:
                raise ValidationError(_("A booking must include at least one person."))
            if record.pax_retired > record.pax_adults:
                raise ValidationError(_("Retirees cannot exceed the number of adults."))
            if record.pax_disabled > record.pax_count:
                raise ValidationError(_("People with disabilities cannot exceed the total number of people."))
            if not 0 <= record.attended_pax <= record.pax_count:
                raise ValidationError(_("People present must be between 0 and the total number of people."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('tursys.booking') or _('New')
            if not vals.get('qr_uuid'):
                vals['qr_uuid'] = str(uuid.uuid4())
            # Precio y comisión congelados al momento de la reserva.
            if 'price_unit' not in vals and vals.get('excursion_id'):
                excursion = self.env['tursys.excursion'].browse(vals['excursion_id'])
                vals['price_unit'] = excursion.product_id.lst_price or 0.0
            if 'commission_rate' not in vals:
                source = self.env['tursys.booking.source'].browse(vals['source_id']) if vals.get('source_id') else False
                vals['commission_rate'] = source.commission_rate if source else 0.0
            if not vals.get('currency_id'):
                vals['currency_id'] = self.env.company.currency_id.id
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

            if record.excursion_id.capacity_available < record.pax_count:
                raise ValidationError(_("Not enough capacity available in this excursion!"))

            record._find_or_create_partner()
            record.write({'state': 'confirmed'})

    def action_waitlist(self):
        self.filtered(lambda b: b.state == 'draft').write({'state': 'waiting'})

    def action_check_in(self, user=None, attended_pax=None):
        """Marca la reserva como presente, aunque se presenten sólo algunos del grupo."""
        now = fields.Datetime.now()
        user = user or self.env.user
        for record in self:
            if record.state != 'confirmed':
                continue
            present = record.pax_count if attended_pax is None else attended_pax
            present = min(max(int(present), 0), record.pax_count)
            record.write({
                'state': 'attended',
                'attended_pax': present,
                'checkin_datetime': now,
                'checked_in_by': user.id,
            })

    def action_undo_check_in(self):
        self.filtered(lambda b: b.state == 'attended').write({
            'state': 'confirmed',
            'attended_pax': 0,
            'checkin_datetime': False,
            'checked_in_by': False,
        })

    def action_mark_no_show(self):
        for record in self:
            if record.state not in ('confirmed', 'attended'):
                continue
            record.write({'state': 'no_show', 'attended_pax': 0})
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
