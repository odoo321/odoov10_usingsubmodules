# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    obj_bool = fields.Boolean(string="Objected",translate=True,index=True)
    obj_value = fields.Float(string="Objected Value",translate=True)

    @api.onchange('obj_bool')
    def obj_bool_onchange(self):
        if self.obj_bool:
            self.obj_value = self.amount_total


class AccountPaymentGroup(models.Model):
    _inherit = 'account.payment.group'

    objected_invoices_ids = fields.One2many('account.invoice.objected','apg_id',ondelete='cascade')

    @api.onchange('partner_id', 'partner_type', 'company_id')
    def _refresh_payments_and_move_lines(self):
        super(AccountPaymentGroup, self)._refresh_payments_and_move_lines()
#    @api.onchange('partner_id')
#    def _objected_onchange(self):
        #self.invalidate_cache(['objected_invoices_ids'])
        #if self.objected_invoices_ids:
        #    self.objected_invoices_ids = (5, False, False)
        if self.partner_id:
            invs = self.env['account.invoice'].search([('partner_id','=',self.partner_id.id),('obj_bool','=',True)])

            self.objected_invoices_ids = False
            lines = []
            for inv in invs:
                lines.append( (0, 0, {'inv_id': inv.id,
                                                      'objected_amount': inv.obj_value,
                                                      'residual_amount': inv.residual,
                                                      'amount_currency': inv.amount_total,
                                                      'residual_amount_currency': inv.residual,
                                                      'currency_id': inv.currency_id.id,
                                                      'date': inv.date,
                                                      'duedate': inv.date_due,
                                                      'invoice_number': inv.display_name2,
                                                      'partner_id': inv.partner_id.id,
                                                      'total_amount': inv.amount_total}))
            print lines
            self.objected_invoices_ids = lines



class AccountInvoiceObjected(models.Model):
    _name = 'account.invoice.objected'

    date = fields.Date(string="Date",translate=True)
    duedate = fields.Date(string="Due Date",translate=True)
    invoice_number = fields.Char(string="Invoice Number",translate=True)
    total_amount = fields.Monetary(string="Total Amount",translate=True,currency_field='currency_id')
    objected_amount = fields.Float(string="Objected Amount",translate=True)
    residual_amount = fields.Float(string="Residual Amount",translate=True)
    amount_currency = fields.Char(string="Amount Currencyt",translate=True)
    residual_amount_currency = fields.Char(string="Residual Amount Currencyt",translate=True)
    inv_id = fields.Many2one('account.invoice')
    partner_id = fields.Many2one('res.partner',string="partner",translate=True)
    currency_id = fields.Many2one('res.currency')
    apg_id = fields.Many2one('account.payment.group')
