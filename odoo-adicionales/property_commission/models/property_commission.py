# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
import time
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import Warning


class commmissionHistory(models.Model):
    _name = 'commission.commission'

    name = fields.Char(
        string='Name',
        required=True)
    commission_type = fields.Selection(
        selection=[('fixed', 'Fixed percentage'),
                   ('fixedcost', 'By Fixed Cost')],
        string='Type',
        required=True,
        default='fixed')
    fix_qty = fields.Float(
        string='Fixed Percentage(%)')
    fix_cost = fields.Float(
        string='Fixed Cost')
    active = fields.Boolean(
        default=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'commission.commission'))


class CommissionInvoice(models.Model):
    _name = "commission.invoice"
    _rec_name = 'number'

    @api.one
    @api.depends('commission_line.inv')
    def done_invoice_amt(self):
        #         self.invoiced = 0.0
        line_obj = self.env['commission.invoice.line']
        for data in self:
            line_ids = line_obj.search(
                [('commission_id', '=', data.id), ('inv', '=', True)])
            for d in line_ids:
                data.invoiced += d.amount

    @api.one
    @api.depends('commission_line.inv')
    def pending_invoice_amt(self):
        self.not_invoice = 0.0
        line_obj = self.env['commission.invoice.line']
        for data in self:
            line_ids = line_obj.search(
                [('commission_id', '=', data.id), ('inv', '=', False)])
            for d in line_ids:
                data.not_invoice += d.amount

    @api.one
    @api.depends('commission_line.amount')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        self.amount_total = 0.0
        for a in self:
            for data in a.commission_line:
                a.amount_total += data.amount

    number = fields.Char(
        string='Commission ID',
        default='/')
    patner_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant',
        help='Name of tenant where from commission is taken')
    date = fields.Date(
        String='Commission Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT))
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    description = fields.Text(
        string='Description')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    state = fields.Selection(
        [('draft', 'Open'),
         ('close', 'Close')
         ], 'State', readonly=True,
        default='draft')
    commission_ref = fields.Many2one(
        comodel_name="commission.commission",
        string="Commission")
    commission_line = fields.One2many(
        comodel_name='commission.invoice.line',
        inverse_name='commission_id',
        string='Commission')
    amount_total = fields.Float(
        string='Total',
        store=True,
        readonly=True,
        compute='_amount_all',
        track_visibility='always')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company Partner')
        # default=lambda self: self.env['res.company']._company_default_get(
        #     'commission.invoice'))
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        store=True,
        related='company_id.currency_id',
        string="Currency")
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    inv = fields.Boolean(
        string='INV')
    invoiced = fields.Float(
        string='Totals',
        store=True,
        compute='done_invoice_amt')
    not_invoice = fields.Float(
        string='Total',
        store=True,
        compute='pending_invoice_amt')
    color = fields.Integer('Color Index')
    account_id = fields.Many2one(
        comodel_name='account.account',
        related = 'property_id.commission_acc_id',
        store=True,
        string='Commission Account',
        help='Commission Account')

    @api.model
    def create(self, vals):
        res = super(CommissionInvoice, self).create(vals)
        if res:
            res.number = self.env['ir.sequence'].get('commission.invoice')
        return res

    @api.multi
    def button_close(self):
        """
        This button method is used to Change commission state to cancel.
        @param self: The object pointer
        """
        if not self.tenancy.state == 'close' or \
                self.tenancy.state == 'cancelled':
            raise Warning(_("Please First close " + str(
                self.tenancy.name) + " Tenancy!"))
        return self.write({'state': 'close'})


class CommissionInvoiceLine(models.Model):
    _name = "commission.invoice.line"
    _description = "Commission Invoice Line"
    _order = 'date desc, id desc'

    @api.multi
    @api.depends('commission_ref', 'paid_amount')
    def calculate_comission(self):
        for data in self:
            if data.commission_ref.commission_type == 'fixed':
                data.amount = data.paid_amount * (
                    data.commission_ref.fix_qty / 100.0)
            if data.commission_ref.commission_type == 'fixedcost':
                data.amount = data.commission_ref.fix_cost

    date = fields.Date(
        String='Commission Date',
        help='Tenancy Start Date')
    name = fields.Char(
        string="Description")
    commission_ref = fields.Many2one(
        comodel_name="commission.commission",
        string="Commission")
    rent_amt = fields.Float(
        string='Rent Amount')
    paid_amount = fields.Float(
        string='Paid Amount')
    p_date = fields.Date(
        string='Payment Date',
        help='Tenancy invoice paid date', )
    amount = fields.Float(
        compute="calculate_comission",
        string='Commission Amount',
        store=True,
        help="Commission Amount.")
    commission_id = fields.Many2one(
        comodel_name='commission.invoice',
        string='Commission')
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    inv = fields.Boolean(
        string='INV')
    rec = fields.Boolean(
        string='Received')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="OwnerCompany")
    # currency_id = fields.Many2one(
    #     comodel_name='res.currency',
    #     string='Currency',
    #     # store=True,
    #     # related='company_id.currency_id',
    #     required=True)
    invoice_date = fields.Date(
        string="Tenancy Invoice Date")
    rent_schedule = fields.Many2one(
        comodel_name='tenancy.rent.schedule',
        string='Rent Schedule')
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Payment')
    journal_name = fields.Char(
        string="Journal Name")

    @api.multi
    def create_invoice(self):
        for data in self:
            commission_acc = ''
            journal_ids = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.commission_id.company_id.parent_id.id)])
            if not data.commission_id.property_id.id:
                raise Warning(_("Please Select Property"))
            if not data.commission_id.account_id.id:
                raise Warning(_("Please select commission account."))
            if data.commission_id.number:
                code = data.commission_id.number
            else:
                code = ' '
            if data.commission_id.property_id.commission_acc_id:
                commission_acc = data.commission_id.property_id.\
                    commission_acc_id.id
            if data.commission_id.account_id:
                commission_acc = data.commission_id.account_id.id
            inv_line_values = {
                'name': 'Commission for ' + code or "",
                'origin': 'Commission',
                'quantity': 1,
                'account_id': commission_acc or False,
                'price_unit': data.amount or 0.00,
            }
            inv_values = {
                'name' :  'RECEIPT# ' + data.journal_name,
                'origin': 'Commission For ' + code or "",
                'type': 'out_invoice',
                'is_vender_bill': False,
                'date_invoice': data.p_date,
                'property_id': data.commission_id.property_id.id,
                'partner_id': data.commission_id.property_id.company_id.
                partner_id.id or False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                # 'date_invoice': data.invoice_date,
                'account_id': data.commission_id.property_id.company_id.
                partner_id.property_account_receivable_id.id or False,
                # 'journal_id': journal_ids and journal_ids.ids[0] or False,
                # 'company_id': data.commission_id.company_id.parent_id.sudo().id
            }
            acc_id = self.env['account.invoice'].create(inv_values)
            data.write({'inv': True, 'invc_id': acc_id.id})
            wiz_form_id = self.env['ir.model.data'].get_object_reference(
                'account', 'invoice_form')[1]
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': self._context,
        }

    @api.multi
    def open_invoice(self):
        """
        This Method is used to Open invoice from Commission record.
        ------------------------------------------------------------
        @param self: The object pointer
        """
        context = dict(self._context or {})
        wiz_form_id = self.env['ir.model.data'].get_object_reference(
            'account', 'invoice_form')[1]
        return {
            'view_type': 'form',
            'view_id': wiz_form_id,
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'res_id': self.invc_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
            'context': context,
        }


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    commission_free = fields.Boolean(
        string='Commission Free')

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        commission_obj = self.env['commission.invoice']
        for data in commission_obj.commission_line.browse(
                self._context.get('active_id')):
            if data:
                line_obj = self.env['commission.invoice.line'].search(
                    [('invc_id', '=', data.id)])
                for data1 in line_obj:
                    if data1.invc_id.state == 'paid':
                        data1.rec = True

        # Commission Creation
        for c in self:
            if c.invoice_ids:
                schedule = c.invoice_ids.schedule_id
                if schedule:
                    commission_obj = self.env['commission.invoice']
                    if not schedule.tenancy_id.commission_free:
               
                        commission_ids = commission_obj.search([('state', '=', 'draft'),
                                                                ('tenancy', '=', schedule.tenancy_id.id)])
                        line_lst = {
                            'date': schedule.start_date,
                            'invoice_date': c.invoice_ids.date_invoice,
                            'commission_ref': schedule.tenancy_id.commission_ref.id,
                            'rent_amt': schedule.amount,
                            'amount': 0.0,
                            'company_id': c.invoice_ids.property_id.company_id.id,
                            'rent_schedule': schedule.id,
                            'paid_amount': c.amount,
                            'p_date': c.payment_date,
                            'journal_name': c.move_name,

                            # 'currency_id': c.currency_id.id
                        }
                        if schedule.tenancy_id.commission_ref.commission_type == 'fixed':
                            p = c.amount * (
                                schedule.tenancy_id.commission_ref.fix_qty / 100.0)
                            line_lst.update({'amount': p})
                        if schedule.tenancy_id.commission_ref.commission_type == \
                                'fixedcost':
                            f = schedule.tenancy_id.commission_ref.fix_cost
                            line_lst.update({'amount': f})
                        vals2 = {
                            'commission_line': [(0, 0, line_lst)]
                        }
                        if vals2:
                            commission_ids.write(vals2)
                    else:
                        pass
        return res


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    commission_ref = fields.Many2one(
        comodel_name="commission.commission",
        string="Commission")
    # commission_create = fields.Boolean(
    #     'Create')
    commission_free = fields.Boolean(
        'Commission Free')

    # @api.multi
    # def button_to_create_commission(self):
    #     """
    #     This button method is used to Change Tenancy state to Open.
    #     @param self: The object pointer
    #     """
    #     self.env['commission.invoice'].create({
    #         'patner_id': self.tenant_id.id,
    #         'tenancy': self.id,
    #         'property_id': self.property_id.id,
    #         'company_id': self.company_id.id,
    #         'account_id': self.property_id.commission_acc_id.id,
    #     })
    #     self.write({'commission_create': True})
    @api.multi
    def button_start(self):
        """
        This button method is used to Change Tenancy state to Open.
        @param self: The object pointer
        """
        res = super(AccountAnalyticAccount, self).button_start()
        if self.commission_free == False:
            commission_obj = self.env['commission.invoice']
            commission_ids = commission_obj.search([('state', '=', 'close'),
                ('tenancy', '=', self.id)])
            if commission_ids:
                commission_ids.write({'state':'draft'})
            else:
                self.env['commission.invoice'].create({
                    'patner_id': self.tenant_id.id,
                    'tenancy': self.id,
                    'property_id': self.property_id.id,
                    'company_id': self.company_id.id,
                    'account_id': self.property_id.commission_acc_id.id,
                })
        return res

    @api.multi
    def button_close(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        res = super(AccountAnalyticAccount, self).button_close()
        commission_obj = self.env['commission.invoice']
        commission_ids = commission_obj.search([('state', '=', 'draft'),
                ('tenancy', '=', self.id)])
        commission_ids.write({'state':'close'})
        return res

    @api.multi
    def button_cancel_tenancy(self):
        """
        This button method is used to Change Tenancy state to Cancelled.
        @param self: The object pointer
        """
        res = super(AccountAnalyticAccount, self).button_cancel_tenancy()
        commission_obj = self.env['commission.invoice']
        commission_ids = commission_obj.search([('state', '=', 'draft'),
                ('tenancy', '=', self.id)])
        commission_ids.write({'state':'close'})
        return res
