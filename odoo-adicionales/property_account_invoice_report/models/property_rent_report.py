# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Serpent Consulting Services Pvt. Ltd.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from odoo import fields, models, api
from odoo.tools import amount_to_text_en
# from odoo.tools.amount_to_text import amount_to_text
# import inflect
# p = inflect.engine()
to_19 = ('Zero',  'One',   'Two',  'Three', 'Four',   'Five',   'Six',
         'Seven', 'Eight', 'Nine', 'Ten',   'Eleven', 'Twelve', 'Thirteen',
         'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen')
tens = ('Twenty', 'Thirty', 'Forty', 'Fifty',
        'Sixty', 'Seventy', 'Eighty', 'Ninety')
denom = ('',
         'Thousand',     'Million',         'Billion',       'Trillion',       'Quadrillion',
         'Quintillion',  'Sextillion',      'Septillion',    'Octillion',      'Nonillion',
         'Decillion',    'Undecillion',     'Duodecillion',  'Tredecillion',   'Quattuordecillion',
         'Sexdecillion', 'Septendecillion', 'Octodecillion', 'Novemdecillion', 'Vigintillion')


def _convert_nn(val):
    """convert a value < 100 to English.
    """
    if val < 20:
        return to_19[val]
    for (dcap, dval) in ((k, 20 + (10 * v)) for (v, k) in enumerate(tens)):
        if dval + 10 > val:
            if val % 10:
                return dcap + '-' + to_19[val % 10]
            return dcap


def _convert_nnn(val):
    """
    convert a value < 1000 to english, special cased because it is the level that kicks 
    off the < 100 special case.  The rest are more general.  This also allows you to
    get strings in the form of 'forty-five hundred' if called directly.
    """
    word = ''
    (mod, rem) = (val % 100, val // 100)
    if rem > 0:
        word = to_19[rem] + ' Hundred'
        if mod > 0:
            word += ' '
    if mod > 0:
        word += _convert_nn(mod)
    return word


def english_number(val):
    if val < 100:
        return _convert_nn(val)
    if val < 1000:
        return _convert_nnn(val)
    for (didx, dval) in ((v - 1, 1000 ** v) for v in range(len(denom))):
        if dval > val:
            mod = 1000 ** didx
            l = val // mod
            r = val - (l * mod)
            ret = _convert_nnn(l) + ' ' + denom[didx]
            if r > 0:
                ret = ret + ', ' + english_number(r)
            return ret


def amount_to_text222(number, currency, floating):
    number = '%.3f' % number
    units_name = currency

    f = floating
    list = str(number).split('.')
    start_word = english_number(int(list[0]))
    end_word = english_number(int(list[1]))
    cents_number = int(list[1])
    # cents_name = (cents_number > 1) and 'Cents' or 'Cent'
    cents_name = ''
    if f:
        return ' ' .join(filter(None, [units_name, start_word, (units_name or start_word) and (end_word or cents_name) and 'and ' + f, end_word, cents_name + 'only']))
    else:
        return ' ' .join(filter(None, [start_word, units_name, (start_word or units_name) and (end_word or cents_name) and 'and', end_word, cents_name]))


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    amount_to_text = fields.Char(
        compute='_amount_in_words',
        string='In Words',
        help="The amount in words")

    @api.model
    def default_get(self, default_fields):
        res = super(AccountInvoice, self).default_get(default_fields)
        if res:
            company_id = self.env['res.company']._company_default_get(
                'taccount.invoice')
            if company_id:
                if company_id.bank_id:
                    bank_id = company_id.bank_id
                    res.update({'partner_bank_id': bank_id.id, })
        return res

    @api.one
    @api.depends('amount_total', 'partner_id', 'partner_id.lang')
    def _amount_in_words(self):
        for data in self:
            if data:
                data.amount_to_text = amount_to_text222(
                    data.amount_total, data.currency_id.label, data.currency_id.floating)


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    label = fields.Char()
    floating = fields.Char(string='Floating Label')


class ResBank(models.Model):
    _inherit = 'res.bank'

    branch = fields.Char(
        string="Branch Name")


class ResCompany(models.Model):
    _inherit = 'res.company'
    _description = 'Description'

    bank_id = fields.Many2one(
        comodel_name='res.partner.bank',
        string='Bank Account')
