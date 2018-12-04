# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class ContractReport(models.TransientModel):
    _name = 'contract.report'

    start_date = fields.Date(
        string='Start date',
        required=True)
    end_date = fields.Date(
        string='End date',
        required=True)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Expiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date:
                dt_from = datetime.strptime(
                    ver.start_date, DEFAULT_SERVER_DATE_FORMAT)
                dt_to = datetime.strptime(
                    ver.end_date, DEFAULT_SERVER_DATE_FORMAT)
                if dt_to < dt_from:
                    raise ValidationError(
                        'End date should be greater than Start date.')

    @api.multi
    def open_contract_expiry_tree(self):
        for data1 in self:
            data = data1.read([])[0]
            start_date = data['start_date']
            end_date = data['end_date']
            wiz_form_id = self.env['ir.model.data'].get_object_reference(
                'property_management', 'property_analytic_view_tree')[1]
            tenancy_ids = self.env["account.analytic.account"].search(
                [('date', '>=', start_date), ('date', '<=', end_date)])
        return {'name': 'Tenancy Contract Expiry',
                'view_mode': 'tree',
                'view_id': wiz_form_id,
                'view_type': 'tree',
                'res_model': 'account.analytic.account',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
                'domain': [('id', 'in', tenancy_ids.ids)],
                }

    @api.multi
    def print_report(self):
        if self._context is None:
            self._context = {}
        data = {
            'ids': self.ids,
            'model': 'account.asset.asset',
            'form': self.read(['start_date', 'end_date'])[0]
        }
        return self.env['report'].get_action(
            self, 'property_management.report_contract_expiry', data=data)
