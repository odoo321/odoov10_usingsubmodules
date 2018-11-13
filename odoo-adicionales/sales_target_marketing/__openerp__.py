# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013-Present Tryon InfoSoft <www.tryoninfosoft.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    'name': 'Sales Target Marketing',
    'version': '10.0.1.0.0',
    'author': 'Tryon InfoSoft',
    'category': 'Sales',
    'description': """
        Sales target marketing module is based on sales. with this user can identify which type of product category
        is selling more and which type of product category is not selling. 
        This is mainly for Target Marketing. User can get idea about which type of product category we have to target
        for our customer.
    """,
    'website': 'https://www.tryoninfosoft.com',
    'summary': 'Used for target marketing.',
    'depends': ['base', 'sales_team', 'sale', 'product'],
    'data': [
             'report.xml',
             'wizard/wizard_sales_target_marketing.xml',
             'report/sale_target_marketing_report.xml'
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: