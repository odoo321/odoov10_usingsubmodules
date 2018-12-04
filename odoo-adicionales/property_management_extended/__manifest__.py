# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2011-Today Serpent Consulting Services PVT LTD
#    (<http://www.serpentcs.com>)
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'Property Management Extended',
    'version': '2.0',
    'category': 'Real Estate',
    'description': """
    Property Management System(PHASE 2)

    Odoo Property Management System will help you to manage your real estate
    portfolio with Property valuation, Maintenance, Insurance, Utilities and
    Rent management with reminders for each KPIs. ODOO's easy to use Content
    management system help you to display available property on website with
    its gallery and other details to reach easily to end users. With the help
    of inbuilt Business Intelligence system it will be more easy to get various
    analytical reports and take strategical decisions.
     """,
    'author': 'Serpent Consulting Services Pvt. Ltd.',
    'website': 'http://www.serpentcs.com',
    'depends': ['property_management', 'report'],
    'data': [
            'views/furniture_details_views.xml',
            'views/property_management_view.xml',
            'report/tenancy_report_actions.xml',
            'report/tenancy_contract_report.xml',
            'report/tenancy_furniture_details_report.xml',
            'report/base_genral_ledger_inherit.xml',
            'report/tenant_handover_document.xml',
            'report/base_report_partnerledger_inherit.xml',
            'report/account_report_inherit.xml',
            'views/analytic_views.xml',
            'wizard/account_report_general_ledger_view.xml',
            'security/ir.model.access.csv',
            'data/property_schedular_new.xml',
    ],
    # 'qweb': [
    #     'static/src/xml/account_report_backend_inherit.xml',
    # ],
    'auto_install': False,
    'installable': True,
    'application': True,
}
