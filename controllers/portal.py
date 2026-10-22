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
        # El guía solo ve sus excursiones y solo mientras estén activas:
        # no se le muestran las finalizadas ni las canceladas.
        return [
            ('state', 'not in', ('done', 'cancelled')),
            '|', ('guide_id', '=', user.id), ('assistant_guide_ids', 'in', [user.id]),
        ]

    def _get_guide_excursion(self, excursion_id):
        """Excursión visible en el portal solo si el usuario es su guía.

        No se usa _document_check_access porque para usuarios de backend
        (administradores) ese método saltea las reglas de registro y dejaría
        ver o modificar excursiones ajenas desde el portal.
        """
        domain = self._get_excursion_domain() + [('id', '=', excursion_id)]
        return request.env['tursys.excursion'].sudo().search(domain, limit=1)

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
            'state_labels': dict(
                request.env['tursys.excursion'].fields_get(['state'])['state']['selection']
            ),
        })
        return request.render('tursys.portal_my_excursions', values)

    # ------------------------------------------------------------------
    # Detalle de la excursión + lista de pasajeros
    # ------------------------------------------------------------------
    @http.route(['/my/excursions/<int:excursion_id>'],
                type='http', auth='user', website=True)
    def portal_my_excursion(self, excursion_id, **kw):
        excursion = self._get_guide_excursion(excursion_id)
        if not excursion:
            return request.redirect('/my')

        bookings = excursion.booking_ids.filtered(
            lambda b: b.state in ('confirmed', 'attended', 'no_show')
        ).sorted('pax_name')

        user = request.env.user
        note_subtype = request.env.ref('mail.mt_note', raise_if_not_found=False)
        # Solo notas reales escritas por guías (se excluyen OdooBot, el
        # administrador y los mensajes automáticos sin contenido).
        guide_partner_ids = request.env['res.users'].sudo().search(
            [('is_tursys_guide', '=', True)]
        ).mapped('partner_id').ids
        comments = excursion.message_ids.filtered(
            lambda m: note_subtype
                and m.subtype_id == note_subtype
                and m.author_id.id in guide_partner_ids
                and (m.body or '').replace('<p></p>', '').strip()
        ).sorted('date', reverse=True)

        state_labels = dict(
            request.env['tursys.excursion'].fields_get(['state'])['state']['selection']
        )

        values = self._prepare_portal_layout_values()
        values.update({
            'page_name': 'excursion',
            'excursion': excursion,
            'bookings': bookings,
            'comments': comments,
            'state_labels': state_labels,
            'is_main_guide': excursion.guide_id.id == user.id,
        })
        return request.render('tursys.portal_excursion_page', values)

    # ------------------------------------------------------------------
    # Acciones de check-in desde el portal (móvil)
    # ------------------------------------------------------------------
    @http.route(['/my/excursions/<int:excursion_id>/booking/<int:booking_id>/<string:action>'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_booking_checkin(self, excursion_id, booking_id, action, **kw):
        redirect = '/my/excursions/%s' % excursion_id
        excursion = self._get_guide_excursion(excursion_id)
        if not excursion:
            return request.redirect('/my')

        # La excursión fue obtenida con las reglas del usuario: sólo puede acceder a las suyas.
        booking = excursion.booking_ids.filtered(lambda b: b.id == booking_id)
        if not booking:
            return request.redirect(redirect)

        booking = booking.sudo()
        try:
            if action == 'check_in':
                attended_pax = kw.get('attended_pax')
                try:
                    attended_pax = int(attended_pax) if attended_pax not in (None, '') else None
                except (TypeError, ValueError):
                    attended_pax = None
                booking.action_check_in(request.env.user, attended_pax=attended_pax)
            elif action == 'no_show':
                booking.action_mark_no_show()
            elif action == 'undo':
                booking.action_undo_check_in()
        except (ValidationError, AccessError):
            pass

        return request.redirect(redirect)

    # ------------------------------------------------------------------
    # Iniciar / finalizar la excursión desde el portal (guía responsable)
    # ------------------------------------------------------------------
    @http.route(['/my/excursions/<int:excursion_id>/<string:action>'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_excursion_action(self, excursion_id, action, **kw):
        redirect = '/my/excursions/%s' % excursion_id
        excursion = self._get_guide_excursion(excursion_id)
        if not excursion:
            return request.redirect('/my')

        try:
            if action == 'start':
                excursion.sudo().action_start_excursion(request.env.user)
            elif action == 'finish':
                excursion.sudo().action_finish_excursion(request.env.user)
        except (ValidationError, AccessError):
            pass

        return request.redirect(redirect)

    # ------------------------------------------------------------------
    # Notas del guía: se publican en el chatter de la excursión
    # ------------------------------------------------------------------
    @http.route(['/my/excursions/<int:excursion_id>/comment'],
                type='http', auth='user', website=True, methods=['POST'])
    def portal_excursion_comment(self, excursion_id, comment=None, **kw):
        redirect = '/my/excursions/%s' % excursion_id
        excursion = self._get_guide_excursion(excursion_id)
        if not excursion:
            return request.redirect('/my')

        body = (comment or '').strip()
        if body:
            excursion.sudo().message_post(
                body=body,
                author_id=request.env.user.partner_id.id,
                subtype_xmlid='mail.mt_note',
            )

        return request.redirect(redirect)
