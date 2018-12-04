# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from dateutil import parser
from odoo import api, fields, models


class SafetyCertificate(models.AbstractModel):
    _name = 'report.property_management.report_safety_certificate'

    def get_details(self, start_date, end_date):
        data_1 = []
        certificate_obj = self.env["property.safety.certificate"]
        certificate_ids = certificate_obj.search(
            [('expiry_date', '>=', start_date),
             ('expiry_date', '<=', end_date)])
        for data in certificate_ids:
            data_1.append({
                'name': data.name,
                'property_id': data.property_id.name,
                'contact_id': data.contact_id.name,
                'expiry_date': parser.parse(
                    data.expiry_date).strftime('%d/%m/%Y'),
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

        data_res = self.with_context(
            data['form'].get('used_context', {})).get_details(
                start_date, end_date)
        docargs = {
            'doc_ids': docids,
            'doc_model': self.model,
            'data': data['form'],
            'docs': docs,
            'time': time,
            'get_details': data_res,
        }
        docargs['data'].update({'end_date': parser.parse(
            docargs.get('data').get('end_date')).strftime('%d/%m/%Y')})
        docargs['data'].update({'start_date': parser.parse(
            docargs.get('data').get('start_date')).strftime('%d/%m/%Y')})
        return self.env['report'].render(
            'property_management.report_safety_certificate', docargs)
