# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time

from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class invoice_to_owner_maint(models.AbstractModel):
    _name = 'report.property_maintenance.invoice_to_owner_report_template'

    @api.multi
    def get_data(self, start_date, end_date, company_id):
        datas = []
        maint_obj = self.env['maintenance.request']
        maint_ids = maint_obj.search([('date_invoice', '<=', end_date),
                                      ('date_invoice', '>=', start_date),
                                      ('invc_check', '=', True),
                                      ('renters_fault','=', False),
                                      ('property_id.company_id', '=', company_id)], order='date_invoice asc')
        for m in maint_ids:
            for i in m.invc_id:
                invoice_id = {
                    'desc': i.journal_name_p,
                    'tenant': m.tenant_id.name,
                    'date': m.date_invoice,
                    'invoice_num': i.number,
                    'source' : i.origin,
                    'property' : m.property_id.name,
                    'amount': i.amount_total,
                }
                invoice_id.update({'date': parser.parse(invoice_id.get('date')).strftime('%d/%m/%Y')})
            datas.append(invoice_id)
        return datas

    @api.multi
    def get_total(self, start_date, end_date, company_id):
        all_total = 0.0
        maint_obj = self.env['maintenance.request']
        maint_ids = maint_obj.search([('date_invoice', '<=', end_date),
                                      ('date_invoice', '>=', start_date),
                                      ('invc_check', '=', True),
                                      ('renters_fault','=', False),
                                      ('property_id.company_id', '=', company_id)], order='date_invoice asc')
        
        for data in maint_ids:
            for invoice in data.invc_id:
                all_total+=invoice.amount_total
        return all_total

    @api.model
    def render_html(self, docids, data=None,):
        i = self._context.get('data')
        self.model = self.env.context.get('active_model')
        if i:
            start_date = i['form'].get('start_date', fields.Date.today())
            end_date = i['form'].get(
                'end_date', str(datetime.now() + relativedelta(
                    months=+1, day=1, days=-1))[:10])
            company_id = i['form'].get('company_id')[1]

            data_res = self.with_context(
                i['form'].get('used_context', {})).get_data(
                    start_date, end_date, company_id)
            docs = self.env[self.model].browse(
                self.env.context.get('active_ids', []))
            data_total = self.with_context(
                i['form'].get('used_context', {})).get_total(
                    start_date, end_date, company_id)
            docargs = {
                'doc_ids': docids,
                'doc_model': self.model,
                'data': i['form'],
                'docs': docs,
                'time': time,
                'get_data': data_res,
                'get_total':data_total,

            }
            docargs['data'].update({'end_date': parser.parse(
                docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
            docargs['data'].update({'start_date': parser.parse(
                docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

            return self.env['report'].render(
                'property_maintenance.invoice_to_owner_report_template',
                docargs)

        else:
            start_date = data['form'].get('start_date', fields.Date.today())
            end_date = data['form'].get(
                'end_date', str(datetime.now() + relativedelta(
                    months=+1, day=1, days=-1))[:10])
            company_id = data['form'].get('company_id')[1]
            data_res = self.with_context(
                data['form'].get('used_context', {})).get_data(
                    start_date, end_date, company_id)
            docs = self.env[self.model].browse(
                self.env.context.get('active_ids', []))
            data_total = self.with_context(
                data['form'].get('used_context', {})).get_total(
                    start_date, end_date, company_id)
            docargs = {
                'doc_ids': docids,
                'doc_model': self.model,
                'data': data['form'],
                'docs': docs,
                'time': time,
                'get_data': data_res,
                'get_total':data_total,
            }
                        
            docargs['data'].update({'end_date': parser.parse(
                docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
            docargs['data'].update({'start_date': parser.parse(
                docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

            return self.env['report'].render(
                'property_maintenance.invoice_to_owner_report_template',
                docargs)
