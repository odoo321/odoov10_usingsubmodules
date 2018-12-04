# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016  BACG S.A. de C.V.  (http://www.bacgroup.net)
#    All Rights Reserved.
#
##############################################################################
{
    'name': 'VITT ARG History Checks Reports',
    'description': 'Adds History Checks Reports for previous states',
    'summary': '',
    'author': "Moogah",
    'website': "http://www.Moogah.com",
    'version': '10.0.1.0.1',
    'license': 'Other proprietary',
    'maintainer': 'Osvaldo Jorge Gentile',
    'contributors': '',
    'category': 'Localization',
    'depends': ['account', 'account_check','vitt_cashin_cashout'],
    'data': [
        'data/issue.checks.states.csv',
        'data/third.checks.states.csv',
        'views/views.xml',
        'views/templates.xml',
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'application': True,
}
