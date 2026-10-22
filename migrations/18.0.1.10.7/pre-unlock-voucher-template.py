# -*- coding: utf-8 -*-


def migrate(cr, version):
    """El template del voucher quedó con noupdate y por eso el -u no lo actualizaba.

    Se destraba el xmlid y se limpian las traducciones viejas para que el XML
    (ahora en español) sea la fuente de verdad.
    """
    cr.execute("""
        UPDATE mail_template
           SET subject   = jsonb_build_object('en_US', subject->>'en_US'),
               body_html = jsonb_build_object('en_US', body_html->>'en_US')
         WHERE model_id = (SELECT id FROM ir_model WHERE model = 'tursys.booking')
    """)
    cr.execute("""
        UPDATE ir_model_data
           SET noupdate = false
         WHERE module = 'tursys' AND name = 'email_template_booking_voucher'
    """)
