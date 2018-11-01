# -*- coding: utf-8 -*-
{
    'name': 'Stock Picking Links with Invoices',
    'version': '10.0.1.0',
    'summary': 'Adds link between pickings and invoices',
    'author': 'Moogah',
    'website': 'http://www.moogah.com',
    'depends': [
        'sale_stock',
        'vitt_arg_einvoice_format',
        'vitt_official_stock_sequence'
    ],
    'data': [
        'views/stock_view.xml',
        'views/account_invoice_view.xml',
        'views/invoice_template.xml',
    ],
    'installable': True,
}
