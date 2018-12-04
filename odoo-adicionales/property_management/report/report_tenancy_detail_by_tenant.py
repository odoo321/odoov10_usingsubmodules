# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models
from odoo.tools import ustr


class TenancyDetailByTenant(models.AbstractModel):
    _name = 'report.property_management.report_tenancy_by_tenant'

    def get_details(self, start_date, end_date, tenant_id):
        data_1 = []
        tenancy_obj = self.env["account.analytic.account"]
        tenancy_ids = tenancy_obj.search(
            [('tenant_id', '=', tenant_id[0]),
             ('date_start', '>=', start_date),
             ('date_start', '<=', end_date),
             ('is_property', '=', True)])
        for data in tenancy_ids:
            if data.currency_id:
                cur = data.currency_id.symbol
            data_1.append({
                'property_id': data.property_id.name,
                'date_start': parser.parse(
                    data.date_start).strftime('%d/%m/%Y'),
                'date': parser.parse(data.date).strftime('%d/%m/%Y'),
                'rent': cur + ustr(data.rent),
                'deposit': cur + ustr(data.deposit),
                'rent_type_id': data.rent_type_id.name,
                'rent_type_month': data.rent_type_id.renttype,
                'state': data.state
            })
        return data_1

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))

        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])
        tenant_id = data['form'].get('tenant_id')

        detail_res = self.with_context(
            data['form'].get('used_context', {})).get_details(
                start_date, end_date, tenant_id)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_details': detail_res,
        }
        docargs['data'].update({'end_date': parser.parse(
            docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
        docargs['data'].update({'start_date': parser.parse(
            docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})
        return self.env['report'].render(
            'property_management.report_tenancy_by_tenant', docargs)
