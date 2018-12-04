# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

{
    'name': 'Property Maintenance',
    'version': '2.1',
    'category': 'Real Estate',
    'description': """
    Property Maintenance
      This module gives the features for managing maintenance of each property
    , request for maintenance, scheduling the recurring maintenance,
        managing the maintenance team, assign the work..etc
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management', 'maintenance', 'hr'],
    'data': [
        "security/maint_security.xml",
        "security/ir.model.access.csv",
        "views/asset_view.xml",
        "views/maintenance_view.xml",
        "report/maintenance_report_template.xml",
        "report/invoice_to_owner_report_template.xml",
        "report/report_template.xml",
        "views/report_configuration.xml",
        "views/recurring_maintenance_view.xml",
        "wizard/maintenace_wizard_view.xml",
        "wizard/invoicetoowner_view.xml",
        "data/email_temaplate.xml", ],

    'demo': ["data/demo_data.xml"],

    'auto_install': False,
    'installable': True,
    'application': True,
}
