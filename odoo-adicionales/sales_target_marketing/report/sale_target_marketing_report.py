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

from odoo import api, models
from datetime import datetime


class sale_target_marketing_report(models.AbstractModel):
    _name = 'report.sales_target_marketing.sale_target_marketing_report'

    @api.multi
    def render_html(self, docids, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('sales_target_marketing.sale_target_marketing_report')
        docargs = {
            'doc_ids': self.env['wizard.sales.target.marketing'].browse(data['id']),
            'doc_model': report.model,
            'docs': self,
            'get_column': self._get_column,
            'get_cust_list': self._get_cust_list,
            'get_total_purchase': self._get_total_purchase
        }
        return report_obj.render('sales_target_marketing.sale_target_marketing_report', docargs)

    def _get_column(self, obj):
        ids = []
        if obj.report_by == 'categ':
            ids = [each_id for each_id in obj.category_ids]
        else:
            ids = [each_id for each_id in obj.product_ids]
        return ids

    def _get_cust_list(self, obj):
        if obj.start_date and obj.end_date:
            sql = """SELECT distinct so.partner_id as partner_id, rp.name as cust_name FROM sale_order so
                    LEFT JOIN res_partner rp on so.partner_id = rp.id
                    WHERE so.date_order::timestamp::date >= '%s'
                    AND so.date_order::timestamp::date <= '%s'
                    AND so.state not in ('draft', 'sent', 'cancel')
                    """ % (obj.start_date, obj.end_date)
        elif obj.start_date and not obj.end_date:
            sql = """SELECT distinct so.partner_id as partner_id, rp.name as cust_name FROM sale_order so
                    LEFT JOIN res_partner rp on so.partner_id = rp.id
                    WHERE so.date_order::timestamp::date >= '%s'
                    AND so.state not in ('draft', 'sent', 'cancel')
                    """ % (obj.start_date)
        elif not obj.start_date and obj.end_date:
            sql = """SELECT distinct so.partner_id as partner_id, rp.name as cust_name FROM sale_order so
                    LEFT JOIN res_partner rp on so.partner_id = rp.id
                    WHERE so.date_order::timestamp::date <= '%s'
                    AND so.state not in ('draft', 'sent', 'cancel')
                    """ % (obj.end_date)
        else:
            sql = """SELECT distinct so.partner_id as partner_id, rp.name as cust_name FROM sale_order so
                    LEFT JOIN res_partner rp on so.partner_id = rp.id
                    WHERE so.state not in ('draft', 'sent', 'cancel')"""
        self.env.cr.execute(sql)
        result = self.env.cr.dictfetchall()
        return result

    def _get_total_purchase(self, obj, partner_id, column_id):
        if obj.report_by == 'categ':
            sql = """SELECT sum(product_uom_qty) FROM sale_order_line sol
                    LEFT JOIN sale_order so on sol.order_id = so.id
                    LEFT JOIN product_product pp on sol.product_id = pp.id
                    LEFT JOIN product_template pt on pp.product_tmpl_id = pt.id
                    WHERE so.state not in ('draft', 'sent', 'cancel')
                    AND pt.categ_id = %s
                    AND sol.order_partner_id = %s """ % (column_id.id, partner_id)
        else:
            sql = """SELECT sum(product_uom_qty) FROM sale_order_line sol
                    LEFT JOIN sale_order so on sol.order_id = so.id
                    WHERE so.state not in ('draft', 'sent', 'cancel')
                    AND sol.product_id = %s
                    AND sol.order_partner_id = %s """ % (column_id.id, partner_id)
        self.env.cr.execute(sql)
        return self.env.cr.fetchone()[0] or 0

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: