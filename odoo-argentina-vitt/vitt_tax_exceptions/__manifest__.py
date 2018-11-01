# -*- coding: utf-8 -*-
{
    'name': 'Tax Withholding Exceptions',
    'description': 'Tax Withholding Exceptions',
    'summary': 'WARNING, replacing whole WHolding calculations',
    'author': 'Moogah',
    'website': 'www.moogah.com',
    'category': 'Accounting & Finance',
    'data': [
        'security/ir.model.access.csv',
        'data/account_tax_exceptions.xml',
        'views/tax_exceptions.xml',
    ],
    'depends': [
        'l10n_ar_account_withholding',
    ],
    'installable': True,
    'name': 'Taxes Exceptions',
    'test': [],
    'version': '10.0.1.0.0',
}
