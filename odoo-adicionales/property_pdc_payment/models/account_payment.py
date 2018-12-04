# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _inherit = 'account.payment'


    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date', help='Effective date of PDC', copy=False, default=False)

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        if self._context.get('asset') or self._context.get('openinvoice'):
            cheque_no = ''
            if self.cheque_reference:
                cheque_no = self.cheque_reference
            invoice_id = self._context.get('active_id')
            if invoice_id:
                tenan_rent = self.env['tenancy.rent.schedule'].search(
                            [('invc_id', '=', invoice_id)])
                if tenan_rent:
                    if tenan_rent.cheque_detail:
                        tenan_rent.cheque_detail.name = cheque_no
                        tenan_rent.cheque_detail.state = 'paid'
        return res

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        tenan_rent_obj = self.env['tenancy.rent.schedule']
        invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
        if invoice_defaults and len(invoice_defaults) == 1:
            invoice = invoice_defaults[0]
            invoice_current_id = invoice['id']
            if invoice_current_id:
                tenant_rent = tenan_rent_obj.search(
                                       [('invc_id', '=', invoice_current_id)])
                if tenant_rent:
                    if tenant_rent.cheque_detail:
                        rec['cheque_reference'] = tenant_rent.cheque_detail[0].name
                        rec['bank_reference'] = tenant_rent.cheque_detail[0].bank_name
                        rec['effective_date'] = tenant_rent.cheque_detail[0].date
                    if tenant_rent.tenancy_id:
                        rec['property_id'] = tenant_rent.tenancy_id.property_id.id
                        rec['tenancy_id'] = tenant_rent.tenancy_id.id

        return rec

#   Gives Credit amount line
    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        if vals and self.tenancy_id and self.tenancy_id.id:
            if self.payment_type in ('inbound', 'outbound'):
                vals.update({
                    'analytic_account_id': False,
                    'cheque_reference': self.cheque_reference,
                    
                    })
        return vals

#   Gives Debit amount line
    def _get_liquidity_move_line_vals(self, amount):
        vals = super(
            AccountPayment, self)._get_liquidity_move_line_vals(amount)
        if vals and self.tenancy_id and self.tenancy_id.id:
            if self.payment_type in ('inbound', 'outbound'):
                vals.update({
                    'analytic_account_id': self.tenancy_id.id,
                    'cheque_reference': self.cheque_reference,    
                    })
        return vals

    def _get_move_vals(self, journal=None):
        """
        Return dict to create the payment move
        """
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'),
                            _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
        if self.payment_method_code =='pdc':
            date = self.effective_date
        else:
            date = self.payment_date
        return {
            'name': name,
            'date': date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
        }


class AccountRegisterPayments(models.TransientModel):
    _inherit = "account.register.payments"

    bank_reference = fields.Char(copy=False)
    cheque_reference = fields.Char(copy=False)
    effective_date = fields.Date('Effective Date', help='Effective date of PDC', copy=False, default=False)

    def get_payment_vals(self):
        res = super(AccountRegisterPayments, self).get_payment_vals()
        if self.payment_method_id == self.env.ref('account_check_printing.account_payment_method_check'):
            res.update({
                'check_amount_in_words': self.check_amount_in_words,
                'check_manual_sequencing': self.check_manual_sequencing,
                'effective_date': self.effective_date,
            })
        return res

