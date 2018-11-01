# -*- coding: utf-8 -*-

{
    'name': 'Argentinean Internal Tax Report',
    'version': '10.0.1.0',
    'category': 'Hidden/Dependency',
    'depends': ['purchase', 'sale_stock', 'l10n_ar_account', 'report_xls'],
    'description': """
Module for defining argentinian reports.
===============================================
    """,
    'data': [
        'data/report_paperformat.xml',
        'views/stock_picking_views.xml',
        'wizard/arg_internal_taxes_report_wizard_views.xml',
        'views/report_internal_taxes.xml',
        'views/arg_internal_tax_report.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': False,
}
