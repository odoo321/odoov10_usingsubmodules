# -*- coding: utf-8 -*-
###############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2011-Today Serpent Consulting Services PVT LTD
#    (<http://www.serpentcs.com>)
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models, _
from odoo.exceptions import UserError


class AccountPartnerLedger(models.TransientModel):
    _inherit = "account.report.partner.ledger"

    # partner_ids = fields.Many2many('res.partner', 'partner_ledger_partner_rel', 'id', 'partner_id', string='Partners')
    partner_ids = fields.Many2one('res.partner', string='Partners')
    analytic_account_id = fields.Many2one(
        'account.analytic.account', 'Tenancy')
    initial_balance = fields.Boolean(string='Include Initial Balances',
                                     help='If you selected date, this field allow you to add a row to display the amount of debit/credit/balance that precedes the filter you\'ve set.',  default=True)
    exclude_deposits = fields.Boolean(string='Exclude Deposits',
                                      help='If you selected then you can not see the deposite received entry',  default=True)
    reconciled = fields.Boolean('Reconciled Entries', default=True)

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({
            'reconciled': self.reconciled,
            'amount_currency': self.amount_currency,
            'partner_ids': self.partner_ids.id,
            # 'analytic_account_ids': self.analytic_account_id.ids,
            'tenancy_ids': self.analytic_account_id.id,
            'property_ids': str(self.analytic_account_id.property_id.name),
            'deposite': self.exclude_deposits,
            # 'initial_balance': self.initial_balance
        })
        # data['form'].update(self.read(['exclude_deposits'])[0])
        data['form'].update(self.read(['initial_balance'])[0])
        if data['form'].get('initial_balance') and not data['form'].get('date_from'):
            raise UserError(_("You must define a Start Date."))
        if data['form'].get('initial_balance') and not data['form'].get('partner_ids'):
            raise UserError(_("You must define a Partner."))
        # self.read(['partner_ids'])[0]
        # if data['form'].get('partner_ids'):
            # raise UserError(_("You must define a Start Date and Partner."))

        return self.env['report'].get_action(self, 'account.report_partnerledger', data=data)
