# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class CommissionInvoiceOwner(models.AbstractModel):
    _name = 'report.property_commission.commission_invoice_owner'

    @api.multi
    def get_data(self, start_date, end_date, company_id):
        data_1 = []
        taxamount = 0.0
        comm_obj = self.env['commission.invoice.line'].search(
            [('inv', '=', True),
             ('p_date', '>=', start_date),
             ('p_date', '<=', end_date),
             ('commission_id.company_id', '=', company_id)
             ], order='p_date asc')
        for data in comm_obj:
            for invoice in data.invc_id.invoice_line_ids:
                invoice_id = {
                    'desc': data.journal_name,
                    'tenancy': data.commission_id.tenancy.name,
                    'date': invoice.invoice_id.date_invoice,
                    'invoice_num': invoice.invoice_id.number,
                    'source' : invoice.name,
                    'property' : invoice.invoice_id.property_id.name,
                    'quantity' : invoice.quantity,
                    'unit_price' : invoice.price_unit,
                    'tax': invoice.invoice_line_tax_ids,
                    'amount': invoice.price_subtotal,
                }
                invoice_id.update({'date': parser.parse(invoice_id.get('date')).strftime('%d/%m/%Y')})
            data_1.append(invoice_id)
            taxamt = taxamount
            invoice_id.update({'tax1':taxamt})
       
        return data_1

    @api.multi
    def get_tax(self, start_date, end_date, company_id):
        taxamount = 0.0
        comm_obj = self.env['commission.invoice.line'].search(
            [('inv', '=', True),
             ('p_date', '>=', start_date),
             ('p_date', '<=', end_date),
             ('commission_id.company_id', '=', company_id)
             ])
        for data in comm_obj:
            for invoice in data.invc_id.invoice_line_ids:
                taxamount+=invoice.invoice_id.amount_tax
        return taxamount

    @api.multi
    def get_total(self, start_date, end_date, company_id):
        all_total = 0.0
        comm_obj = self.env['commission.invoice.line'].search(
            [('inv', '=', True),
             ('p_date', '>=', start_date),
             ('p_date', '<=', end_date),
             ('commission_id.company_id', '=', company_id)
             ])
        for data in comm_obj:
            for invoice in data.invc_id.invoice_line_ids:
                all_total+=invoice.invoice_id.amount_total
        return all_total

    @api.multi
    def get_sub_total(self, start_date, end_date, company_id):
        sub_total = 0.0
        comm_obj = self.env['commission.invoice.line'].search(
            [('inv', '=', True),
             ('p_date', '>=', start_date),
             ('p_date', '<=', end_date),
             ('commission_id.company_id', '=', company_id)
             ])
        for data in comm_obj:
            for invoice in data.invc_id.invoice_line_ids:
                sub_total+=invoice.invoice_id.amount_untaxed
        return sub_total

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
            data_tax = self.with_context(
                i['form'].get('used_context', {})).get_tax(
                    start_date, end_date, company_id)
            data_total = self.with_context(
                i['form'].get('used_context', {})).get_total(
                    start_date, end_date, company_id)
            get_sub_total = self.with_context(
                i['form'].get('used_context', {})).get_sub_total(
                    start_date, end_date, company_id)

            docargs = {
                'doc_ids': docids,
                'doc_model': self.model,
                'data': i['form'],
                'docs': docs,
                'time': time,
                'get_data': data_res,
                'get_tax': data_tax,
                'get_total':data_total,
                'get_sub_total':get_sub_total
            }
            docargs['data'].update({'end_date': parser.parse(
                docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
            docargs['data'].update({'start_date': parser.parse(
                docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

            return self.env['report'].render(
                'property_commission.commission_invoice_owner', docargs)

        else:
            start_date = data['form'].get('start_date', fields.Date.today())
            end_date = data['form'].get(
                'end_date', str(datetime.now() + relativedelta(
                    months=+1, day=1, days=-1))[:10])
            company_id = data['form'].get('company_id')[1]
            data_res = self.with_context(
                data['form'].get('used_context', {})).get_data(
                    start_date, end_date, company_id)
            data_tax = self.with_context(
                data['form'].get('used_context', {})).get_tax(
                    start_date, end_date, company_id)
            # aa = self.get_data(start_date, end_date, company_id)
            docs = self.env[self.model].browse(
                self.env.context.get('active_ids', []))
            data_total = self.with_context(
                data['form'].get('used_context', {})).get_total(
                    start_date, end_date, company_id)
            get_sub_total = self.with_context(
                data['form'].get('used_context', {})).get_sub_total(
                    start_date, end_date, company_id)
            docargs = {
                'doc_ids': docids,
                'doc_model': self.model,
                'data': data['form'],
                'docs': docs,
                'time': time,
                'get_data': data_res,
                'get_tax': data_tax,
                'get_total':data_total,
                'get_sub_total':get_sub_total


            }
            docargs['data'].update({'end_date': parser.parse(
                docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
            docargs['data'].update({'start_date': parser.parse(
                docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})

            return self.env['report'].render(
                'property_commission.commission_invoice_owner', docargs)
