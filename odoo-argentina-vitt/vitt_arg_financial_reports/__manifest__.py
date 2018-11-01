# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2011 Cubic ERP - Teradata SAC. (http://cubicerp.com)

{
    'name': 'Argentina - Financial Reports',
    'version': '10.0.1.0',
    'description': """
Financial reports with ARG Chart of Accounts using Account Tags instead of account type.

    """,
    'author': ['Moogah'],
    'website': 'http://www.moogah.com',
    'category': 'Localization',
    'depends': ['base', 'account'],
    'data':[
        'data/arg_balance_report.xml'
    ],
}
