# -*- coding: utf-8 -*-
# from odoo import http


# class Tursys(http.Controller):
#     @http.route('/tursys/tursys', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/tursys/tursys/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('tursys.listing', {
#             'root': '/tursys/tursys',
#             'objects': http.request.env['tursys.tursys'].search([]),
#         })

#     @http.route('/tursys/tursys/objects/<model("tursys.tursys"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('tursys.object', {
#             'object': obj
#         })

