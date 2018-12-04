# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class contract_expiry(models.AbstractModel):
    _name = 'report.property_maintenance.maintenance_report_template'

    @api.multi
    def get_data(self, start_date, end_date):
        result = []
        maint_obj = self.env["maintenance.request"]
        maint_ids = maint_obj.search(
            [('request_date', '<=', end_date),
             ('close_date', '>=', start_date),
             ('done', '=', True)])
        for details in maint_ids:
            result.append({
                'name': details.name,
                'property_name': details.property_id.name,
                'owner_company': details.property_id.company_id.name,
                'maintenance_type': details.maintenance_type,
                'close_date': parser.parse(
                    details.close_date).strftime('%d/%m/%Y'),
                'maintenance_cost': details.cost,
            })
        return result

    @api.multi
    def get_total(self, start_date, end_date):
        total_cost = 0.0
        maint_obj = self.env["maintenance.request"]
        maint_ids = maint_obj.search(
            [('request_date', '<=', end_date),
             ('close_date', '>=', start_date),
             ('done', '=', True)])
        for details in maint_ids:
            total_cost += details.cost
        return total_cost

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))

        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])

        data_res = self.with_context(
            data['form'].get('used_context', {})).get_data(
                start_date, end_date)
        data_tot = self.with_context(data['form'].get(
            'used_context', {})).get_total(start_date, end_date)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_data': data_res,
            'get_total': data_tot,
        }
        docargs['data'].update({'end_date': parser.parse(
            docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
        docargs['data'].update({'start_date': parser.parse(
            docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

        return self.env['report'].render(
            'property_maintenance.maintenance_report_template', docargs)
