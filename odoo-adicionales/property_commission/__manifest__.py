# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

{
    'name': 'Property Commission',
    'version': '2.1',
    'category': 'Real Estate',
    'description': """
Property Commission

This module gives the features for managing calculating commission based on
the property and maintenance.
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management', 'property_maintenance'],
    'data': [
            'data/commission_seq.xml',
            'security/res_groups.xml',
            'security/ir.model.access.csv',
            'views/property_commission_view.xml',
            'report/commission_report_template2.xml',
            'report/commissiondetails_report_template.xml',
            'report/report_commission_invoice_owner_template.xml',
            'report/report_template.xml',
            'views/report_configuration.xml',
            'views/asset_view.xml',
            'wizard/commission_report_view.xml',
            'wizard/commission_invoice_owner_view.xml',
            'data/email_temaplate.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
