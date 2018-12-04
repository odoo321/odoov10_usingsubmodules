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
###############################################################################*-
import time
import logging
from datetime import datetime
from odoo import api, models, _
from odoo.exceptions import UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta
from dateutil import parser


_logger = logging.getLogger(__name__)


class ReportPartnerLedger(models.AbstractModel):
    _inherit = 'report.account.report_partnerledger'

    def _lines(self, data, partner):
        analytic_id = self.env['account.analytic.account'].browse(data[
                                                                  'tenancy_ids'])
        full_account = []
        currency = self.env['res.currency']
        uc = data['form'].get('used_context', {})
        uc.update({'tenancy_ids': analytic_id})
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".reconciled = false '
        params = [partner.id, tuple(data['computed']['move_state']), tuple(
            data['computed']['account_ids'])] + query_get_data[2]
        query = """
            SELECT "account_move_line".id,"account_move_line".tenancy_id,"account_move_line".date, j.code,
            acc.code as a_code, acc.name as a_name, "account_move_line".ref,
            m.name as move_name, "account_move_line".name, "account_move_line".cheque_reference,
            "account_move_line".debit, "account_move_line".credit, 
            "account_move_line".amount_currency,
            "account_move_line".deposite,
            "account_move_line".currency_id, c.symbol AS currency_code
            FROM """ + query_get_data[0] + """
            LEFT JOIN account_journal j ON ("account_move_line".journal_id = j.id)
            LEFT JOIN account_account acc ON ("account_move_line".account_id = acc.id)
            LEFT JOIN res_currency c ON ("account_move_line".currency_id=c.id)
            LEFT JOIN account_move m ON (m.id="account_move_line".move_id)  
            WHERE  "account_move_line".partner_id = %s
                AND m.state IN %s
                AND "account_move_line".account_id IN %s AND """ + query_get_data[1] + reconcile_clause + """
                ORDER BY "account_move_line".date"""
        self.env.cr.execute(query, tuple(params))
        res = self.env.cr.dictfetchall()

        existing_ids = [mv_line_dict['id']
                        for mv_line_dict in res if 'id' in mv_line_dict]
        if data['inital_line']:
            sum = 0.0 + data['inital_line'][0]['balance']
        else:
            sum = 0.0
        lang_code = self.env.context.get('lang') or 'en_US'
        lang = self.env['res.lang']
        lang_id = lang._lang_get(lang_code)
        date_format = lang_id.date_format
        for r in res:
            r['date'] = datetime.strptime(
                r['date'], DEFAULT_SERVER_DATE_FORMAT).strftime(date_format)
            r['displayed_name'] = '-'.join(
                r[field_name] for field_name in ('move_name', 'ref', 'name')
                if r[field_name] not in (None, '', '/')
            )
            sum += r['debit'] - r['credit']
            r['progress'] = sum
            r['currency_id'] = currency.browse(r.get('currency_id'))
            full_account.append(r)
        return full_account

    def _get_intial_balance(self, data, partner, accounts):
        result = 0.0
        analytic_id = self.env['account.analytic.account'].browse(data[
                                                                  'tenancy_ids'])
        uc = data['form'].get('used_context', {})
        uc.update({'tenancy_ids': analytic_id})
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = dict(map(lambda x: (x, []), data[
                          'computed']['account_ids']))
        if data['init_balance']:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False, initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace(
                'account_move_line__move_id', 'm').replace('account_move_line', 'l')
            if data['tenancy_ids']:
                sql = ("""SELECT 0 AS lid, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance,\
                    '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                    NULL AS currency_id,\
                    '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                    '' AS partner_name\
                    FROM account_move_line l\
                    LEFT JOIN account_move m ON (l.move_id=m.id)\
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                    JOIN account_journal j ON (l.journal_id=j.id)\
                    WHERE l.partner_id = %s
                    AND m.state IN %s
                    AND l.tenancy_id = %s
                    AND l.account_id IN %s
                    """ + filters )
                params = (partner.id, tuple(data['computed']['move_state']), data[
                          'tenancy_ids'], tuple(data['computed']['account_ids']),) + tuple(init_where_params)
            if not data['tenancy_ids']:
                sql = ("""SELECT 0 AS lid, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance,\
                    '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                    NULL AS currency_id,\
                    '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                    '' AS partner_name\
                    FROM account_move_line l\
                    LEFT JOIN account_move m ON (l.move_id=m.id)\
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    LEFT JOIN account_invoice i ON (m.id =i.move_id)\
                    JOIN account_journal j ON (l.journal_id=j.id)\
                    WHERE l.partner_id = %s
                    AND m.state IN %s
                    AND l.account_id IN %s
                    """ + filters )
                params = (partner.id, tuple(data['computed']['move_state']), tuple(
                    data['computed']['account_ids']),) + tuple(init_where_params)
            self.env.cr.execute(sql, params)
            row = self.env.cr.dictfetchall()
            for row in cr.dictfetchall():
                move_lines[row.pop('account_id')].append(row)
            return row

    def _sum_partner(self, data, partner, field):
        if field not in ['debit', 'credit', 'balance']:
            return
        result = 0.0
        analytic_id = self.env['account.analytic.account'].browse(data[
                                                                  'tenancy_ids'])
        uc = data['form'].get('used_context', {})
        uc.update({'tenancy_ids': analytic_id})
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".reconciled = false '
        params = [partner.id, tuple(data['computed']['move_state']), tuple(
            data['computed']['account_ids'])] + query_get_data[2]
        query = """SELECT sum(""" + field + """)
                FROM """ + query_get_data[0] + """, account_move AS m
                WHERE "account_move_line".partner_id = %s
                    AND m.id = "account_move_line".move_id
                    AND m.state IN %s
                    AND account_id IN %s
                    AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        contemp = self.env.cr.fetchone()
        if contemp is not None:
            result = contemp[0] or 0.0
        return result

    @api.model
    def render_html(self, docids, data=None):
        self.model = self.env.context.get('active_model')
        docs = self.env[self.model].browse(
            self.env.context.get('active_ids', [])).id

        data['computed'] = {}
        self.reconcil = True
        obj_partner = self.env['res.partner']
        query_get_data = self.env['account.move.line'].with_context(
            data['form'].get('used_context', {}))._query_get()
        data['computed']['move_state'] = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            data['computed']['move_state'] = ['posted']
        result_selection = data['form'].get('result_selection', 'customer')
        if result_selection == 'supplier':
            data['computed']['ACCOUNT_TYPE'] = ['payable']
        elif result_selection == 'customer':
            data['computed']['ACCOUNT_TYPE'] = ['receivable']
        else:
            data['computed']['ACCOUNT_TYPE'] = ['payable', 'receivable']

        self.env.cr.execute("""
            SELECT a.id
            FROM account_account a
            WHERE a.internal_type IN %s
            AND NOT a.deprecated""", (tuple(data['computed']['ACCOUNT_TYPE']),))
        data['computed']['account_ids'] = [
            a for (a,) in self.env.cr.fetchall()]
        params = [tuple(data['computed']['move_state']), tuple(
            data['computed']['account_ids'])] + query_get_data[2]
        reconcile_clause = "" if data['form'][
            'reconciled'] else ' AND "account_move_line".reconciled = false '
        query = """
            SELECT DISTINCT "account_move_line".partner_id
            FROM """ + query_get_data[0] + """, account_account AS account, account_move AS am
            WHERE "account_move_line".partner_id IS NOT NULL
                AND "account_move_line".account_id = account.id
                AND am.id = "account_move_line".move_id
                AND am.state IN %s
                AND "account_move_line".account_id IN %s
                AND NOT account.deprecated
                AND """ + query_get_data[1] + reconcile_clause
        self.env.cr.execute(query, tuple(params))
        if data['form']['partner_ids']:
            partner_ids = data['form']['partner_ids']
        else:
            partner_ids = [res['partner_id']
                           for res in self.env.cr.dictfetchall()]

        data['tenancy_ids'] = data['form']['tenancy_ids']
        data['init_balance'] = data['form'].get('initial_balance', True)
        data['deposite'] = data['form']['deposite']
        if data['deposite'] == True:
            ctx2 = data['form'].get('used_context', {})
            ctx2.update({'deposite': True})
        partners = obj_partner.browse(partner_ids)
        accounts = data['computed']['account_ids']
        # accounts = docs if self.model == 'account.account' else self.env['account.account'].search([])
        partner = partners
        data['inital_line'] = self.with_context(data['form'].get(
            'used_context', {}))._get_intial_balance(data, partner, accounts)
        partners = sorted(partners, key=lambda x: (x.ref, x.name))
        docargs = {
            'doc_ids': partner_ids,
            'doc_model': self.env['res.partner'],
            'data': data,
            'docs': partners,
            'time': time,
            'get_intial_balance': data['inital_line'],
            'lines': self._lines,
            'sum_partner': self._sum_partner,
        }
        date_t = data['form'].get('date_to')
        date_f = data['form'].get('date_from')

        if date_t and date_f:
            docargs['data']['form'].update({'date_to': parser.parse(
                docargs['data']['form'].get('date_to')).strftime('%d/%m/%Y')})
            docargs['data']['form'].update({'date_from': parser.parse(
                docargs['data']['form'].get('date_from')).strftime('%d/%m/%Y')})
        return self.env['report'].render('account.report_partnerledger', docargs)
