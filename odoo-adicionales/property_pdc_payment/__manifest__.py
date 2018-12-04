# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

{
    'name': 'Property PDC Payment',
    'version': '2.1',
    'category': 'Real Estate',
    'description': """
    Property PDC payment Module
      This module gives the features for managing Post dated Cheques
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management','account','account_check_printing'],
    'data': [
        "views/account_payment_view.xml"],

    'demo': [],

    'auto_install': False,
    'installable': True,
    'application': True,
}
