# -*- coding: utf-8 -*-
{
    'name': "TurSys - Gestión Profesional de Agencias de Turismo",

    'summary': """
        Administración integral de excursiones, reservas y logística de pasajeros.
    """,

    'description': """
Módulo avanzado para agencias de turismo que permite:
- Gestión de instancias de excursiones con control de capacidad.
- Registro ágil de pasajeros vinculados a contactos centralizados.
- Control de nacionalidades, idiomas y necesidades especiales/médicas.
- Generación de reportes profesionales de listas de pasajeros en formato PDF.
- Preparado para integración futura con ventas y códigos QR de control de acceso.
    """,

    'author': "Alitux",
    'website': "https://alitux.com.ar",
    'category': 'Operations/Tourism',
    'version': '18.0.1.10.4',
    'license': 'LGPL-3',

    'depends': ['base', 'product', 'mail', 'web', 'portal', 'calendar'],

    'data': [
        'security/tursys_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/nationality_data.xml',
        'data/language_data.xml',
        'data/activity_type_data.xml',
        'data/ir_cron_data.xml',
        'reports/excursion_reports.xml',
        'reports/booking_reports.xml',
        'data/mail_template_data.xml',
        'data/booking_source_data.xml',
        'data/config_parameter_data.xml',
        'views/configuration_views.xml',
        'views/res_config_settings_views.xml',
        'views/pickup_views.xml',
        'views/booking_source_views.xml',
        'views/excursion_views.xml',
        'views/booking_views.xml',
        'views/menus.xml',
        'views/portal_templates.xml',
    ],

    'assets': {
        'web.assets_frontend': [
            'tursys/static/src/js/portal_passenger_filter.js',
        ],
    },
    
    'application': True,
    'installable': True,
}
