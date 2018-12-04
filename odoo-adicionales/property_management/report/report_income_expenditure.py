# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class IncomeExpenditure(models.AbstractModel):
    _name = 'report.property_management.report_income_expenditure'

    def get_details(self, start_date, end_date):
        report_rec = []
        total_in = 0.00
        total_ex = 0.00
        total_gr = 0.00
        property_obj = self.env['account.asset.asset']
        maintenance_obj = self.env["maintenance.request"]
        income_obj = self.env["tenancy.rent.schedule"]
        property_ids = property_obj.search([])
        for property_id in property_ids:
            tenancy_ids = []
            if property_id.tenancy_property_ids and \
                    property_id.tenancy_property_ids.ids:
                tenancy_ids += property_id.tenancy_property_ids.ids
            income_ids = income_obj.search(
                [('start_date', '>=', start_date),
                 ('start_date', '<=', end_date),
                 ('tenancy_id', 'in', tenancy_ids)])
            maintenance_ids = maintenance_obj.search(
                [('request_date', ">=", start_date),
                 ('request_date', "<=", end_date),
                 ('property_id', '=', property_id.id)])
            total_income = 0.00
            total_expence = 0.00
            for income_id in income_obj.browse(income_ids.ids):
                total_income += income_id.amount
            for expence_id in maintenance_ids:
                total_expence += expence_id.cost
            total_in += total_income
            total_ex += total_expence

            report_rec.append({
                'property': property_id.name,
                'total_income': total_income,
                'total_expence': total_expence,
                'total_in': '',
                'total_ex': '',
                'total_gr': '',
            })
        total_gr = total_in - total_ex
        if total_in and total_ex and total_gr:
            report_rec.append({
                'property': '',
                'total_income': '',
                'total_expence': '',
                'total_in': total_in,
                'total_ex': total_ex,
                'total_gr': total_gr,
            })
        return report_rec

    @api.model
    def render_html(self, docids, data=None):

        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', []))
        start_date = data['form'].get('start_date', fields.Date.today())
        end_date = data['form'].get(
            'end_date', str(datetime.now() + relativedelta(
                months=+1, day=1, days=-1))[:10])
        detail_res = self.with_context(
            data['form'].get('used_context', {})).get_details(
                start_date, end_date)

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
            'property_management.report_income_expenditure', docargs)
