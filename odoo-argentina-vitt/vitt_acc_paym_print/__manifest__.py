# -*- coding: utf-8 -*-
{
    'name': "Formato de Impresion para Pagos y Recibos",

    'summary': """Localizacion impresion de pagos y recibos""",

    'description': """
        impresion de pagos y recibos ARG
    """,
    'author': "Moogah",
    'website': "http://www.Moogah.com",
    'category': 'Uncategorized',
    'version': '10.0.1.0',
    'depends': [
        'account_payment_group',
        'account_check',
        'vitt_val2words',
    ],
    'data': [
        #'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'demo': [],
    'application': True,
}