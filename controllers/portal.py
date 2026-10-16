# -*- coding: utf-8 -*-
from odoo import http, _
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class TursysPortal(CustomerPortal):

    # ------------------------------------------------------------------
    # Home del portal: contador de excursiones asignadas
    # ------------------------------------------------------------------
    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'excursion_count' in counters:
            values['excursion_count'] = request.env['tursys.excursion'].search_count(
                self._get_excursion_domain()
            )
        return values

    def _get_excursion_domain(self):
        user = request.env.user
        return ['|', ('guide_id', '=', user.id), ('assistant_guide_ids', 'in', [user.id])]

    # ------------------------------------------------------------------
    # Listado de excursiones asignadas al guía
    # ------------------------------------------------------------------
    @http.route(['/my/excursions', '/my/excursions/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_excursions(self, page=1, **kw):
        Excursion = request.env['tursys.excursion']
        domain = self._get_excursion_domain()
        excursion_count = Excursion.search_count(domain)
        pager = portal_pager(
            url='/my/excursions',
            total=excursion_count,
            page=page,
            step=self._items_per_page,
        )
        excursions = Excursion.search(
            domain, order='start_datetime desc',
            limit=self._items_per_page, offset=pager['offset'],
        )
        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'excursion',
            'default_url': '/my/excursions',
            'excursions': excursions,
            'pager': pager,
            'excursion_count': excursion_count,
        })
        return request.render('tursys.portal_my_excursions', values)

    # ------------------------------------------------------------------
    # Detalle de la excursión + lista de pasajeros
    # ------------------------------------------------------------------
    @http.route(['/my/excursions/<int:excursion_id>'],
                type='http', auth='user', website=True)
    def portal_my_excursion(self, excursion_id, **kw):
        try:
            excursion = self._document_check_access('tursys.excursion', excursion_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        bookings = excursion.booking_ids.filtered(
            lambda b: b.state in ('confirmed', 'attended', 'no_show')
        ).sorted('pax_name')

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'excursion',
            'excursion': excursion,
            'bookings': bookings,
        })
        return request.render('tursys.portal_excursion_page', values)

    # ------------------------------------------------------------------
    # Acciones de check-in desde el portal (móvil)
    # ------------------------------------------------------------------
    @http.route(['/my/excursions/<int:excursion_id>/booking/<int:booking_id>/<string:action>'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_booking_checkin(self, excursion_id, booking_id, action, **kw):
        redirect = '/my/excursions/%s' % excursion_id
        try:
            excursion = self._document_check_access('tursys.excursion', excursion_id)
        except (AccessError, MissingError):
            return request.redirect('/my')

        # La excursión fue obtenida con las reglas del usuario: sólo puede acceder a las suyas.
        booking = excursion.booking_ids.filtered(lambda b: b.id == booking_id)
        if not booking:
            return request.redirect(redirect)

        booking = booking.sudo()
        try:
            if action == 'check_in':
                booking.action_check_in(request.env.user)
            elif action == 'no_show':
                booking.action_mark_no_show()
            elif action == 'undo':
                booking.action_undo_check_in()
        except (ValidationError, AccessError):
            pass

        return request.redirect(redirect)
