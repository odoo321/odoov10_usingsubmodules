# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time
from datetime import datetime
from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    _order = 'ref'

    @api.multi
    @api.depends('account_move_line_ids')
    def _total_deb_cre_amt_calc(self):
        """
        This method is used to calculate Total income amount.
        @param self: The object pointer
        """
        total = 0.0
        for tenancy_brw in self:
            total = tenancy_brw.total_debit_amt - tenancy_brw.total_credit_amt
            tenancy_brw.total_deb_cre_amt = total

    @api.multi
    @api.depends('account_move_line_ids')
    def _total_credit_amt_calc(self):
        """
        This method is used to calculate Total credit amount.
        @param self: The object pointer
        """
        total = 0.0
        for tenancy_brw in self:
            if tenancy_brw.account_move_line_ids and \
                    tenancy_brw.account_move_line_ids.ids:
                for debit_amt in tenancy_brw.account_move_line_ids:
                    total += debit_amt.credit
            tenancy_brw.total_credit_amt = total

    @api.multi
    @api.depends('account_move_line_ids')
    def _total_debit_amt_calc(self):
        """
        This method is used to calculate Total debit amount.
        @param self: The object pointer
        """
        total = 0.0
        for tenancy_brw in self:
            if tenancy_brw.account_move_line_ids and \
                    tenancy_brw.account_move_line_ids.ids:
                for debit_amt in tenancy_brw.account_move_line_ids:
                    total += debit_amt.debit
            tenancy_brw.total_debit_amt = total

    @api.one
    @api.depends('rent_schedule_ids', 'rent_schedule_ids.amount')
    def _total_amount_rent(self):
        """
        This method is used to calculate Total Rent of current Tenancy.
        @param self: The object pointer
        @return: Calculated Total Rent.
        """
        tot = 0.00
        if self.rent_schedule_ids and self.rent_schedule_ids.ids:
            for propety_brw in self.rent_schedule_ids:
                tot += propety_brw.amount
        self.total_rent = tot

    # @api.multi
    # @api.depends('deposit')
    # def _get_deposit(self):
    #     """
    #     This method is used to set deposit return and deposit received
    #     boolean field accordingly to current Tenancy.
    #     @param self: The object pointer
    #     """
    #     for tennancy in self:
    #         payment_ids = self.env['account.payment'].search(
    #             [('tenancy_id', '=', tennancy.id), ('state', '=', 'posted')])
    #         if payment_ids and payment_ids.ids:
    #             for payment in payment_ids:
    #                 if payment.payment_type == 'inbound':
    #                     # if payment.deposite_rec == True:
    #                     tennancy.deposit_received = True

    @api.one
    @api.depends('prop_id', 'multi_prop')
    def _total_prop_rent(self):
        tot = 0.00
        if self._context.get('is_tenancy_rent'):
            prop_val = self.prop_ids.ground_rent or 0.0
        else:
            prop_val = self.property_id.ground_rent or 0.0
        for pro_record in self:
            if self.multi_prop:
                for prope_ids in pro_record.prop_id:
                    tot += prope_ids.ground
                pro_record.rent = tot + prop_val
            else:
                pro_record.rent = prop_val

    contract_attachment = fields.Binary(
        string='Tenancy Contract',
        help='Contract document attachment for selected property')
    is_property = fields.Boolean(
        string='Is Property?')
    rent_entry_chck = fields.Boolean(
        string='Rent Entries Check',
        default=False)
    tenancy_cancelled = fields.Boolean(
        string='Tanency Cancelled',
        default=False)
    deposit_received = fields.Boolean(
        string='Deposit Received?',
        default=False,
        # multi='deposit',
        # compute='_get_deposit',
        help="True if deposit amount received for current Tenancy.")
    deposit_return = fields.Boolean(
        string='Deposit Returned?',
        default=False,
        multi='deposit',
        type='boolean',
        compute='amount_return_compute',
        help="True if deposit amount returned for current Tenancy.")
    ref = fields.Char(
        string='Reference',
        default="/")
    doc_name = fields.Char(
        string='Filename')
    date = fields.Date(
        string='Expiration Date',
        index=True,
        help="Tenancy contract end date.")
    date_start = fields.Date(
        string='Start Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        help="Tenancy contract start date .")
    ten_date = fields.Date(
        string='Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        index=True,
        help="Tenancy contract creation date.")
    amount_fee_paid = fields.Integer(
        string='Amount of Fee Paid')
    manager_id = fields.Many2one(
        comodel_name='res.users',
        string='Account Manager',
        help="Manager of Tenancy.")
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help="Name of Property.")
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant',
        domain="[('tenant', '=', True)]",
        help="Tenant Name of Tenancy.")
    contact_id = fields.Many2one(
        comodel_name='res.partner',
        string='Contact',
        help="Contact person name.")
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        help="The optional other currency if it is a multi-currency entry.")
    rent_schedule_ids = fields.One2many(
        comodel_name='tenancy.rent.schedule',
        inverse_name='tenancy_id',
        string='Rent Schedule')
    account_move_line_ids = fields.One2many(
        comodel_name='account.move.line',
        inverse_name='analytic_account_id',
        string='Entries',
        readonly=True,
        states={'draft': [('readonly', False)]})
    rent = fields.Monetary(
        string='Tenancy Rent',
        default=0.0,
        currency_field='currency_id',
        help="Tenancy rent for selected property per Month.")
    deposit = fields.Monetary(
        string='Deposit',
        default=0.0,
        currency_field='currency_id',
        help="Deposit amount for tenancy.")
    total_rent = fields.Monetary(
        string='Total Rent',
        store=True,
        readonly=True,
        currency_field='currency_id',
        compute='_total_amount_rent',
        help='Total rent of this Tenancy.')
    amount_return = fields.Monetary(
        string='Deposit Returned',
        default=0.0,
        currency_field='currency_id',
        help="Deposit Returned amount for Tenancy.")
    total_debit_amt = fields.Monetary(
        string='Total Debit Amount',
        default=0.0,
        compute='_total_debit_amt_calc',
        currency_field='currency_id')
    total_credit_amt = fields.Monetary(
        string='Total Credit Amount',
        default=0.0,
        compute='_total_credit_amt_calc',
        currency_field='currency_id')
    total_deb_cre_amt = fields.Monetary(
        string='Total Expenditure',
        default=0.0,
        compute='_total_deb_cre_amt_calc',
        currency_field='currency_id')
    description = fields.Text(
        string='Description',
        help='Additional Terms and Conditions')
    duration_cover = fields.Text(
        string='Duration of Cover',
        help='Additional Notes')
    acc_pay_dep_rec_id = fields.Many2one(
        comodel_name='account.payment',
        string='Account Manager',
        help="Manager of Tenancy.")
    acc_pay_dep_ret_id = fields.Many2one(
        comodel_name='account.payment',
        string='Account Manager',
        help="Account Manager of Tenancy.")
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type')
    deposit_scheme_type = fields.Selection(
        [('insurance', 'Insurance-based')],
        'Type of Scheme')
    state = fields.Selection(
        [('template', 'Template'),
         ('draft', 'New'),
         ('open', 'In Progress'),
         ('pending', 'To Renew'),
         ('cancelled', 'Cancelled'),
         ('close', 'Closed')],
        string='Status',
        required=True,
        copy=False,
        default='draft')
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    multi_prop = fields.Boolean(
        string='Multiple Property',
        help="Check this box Multiple property.")
    active = fields.Boolean(
        string="Active")
    water_meter = fields.Char(
        string='Water Meter Serial Number')
    ec_meter = fields.Char(
        string='Electricity Meter Serial Number')
    gate_pass = fields.Char(
        string='Gate Pass Number')

    @api.constrains('date_start', 'date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Expiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.date_start and ver.date:
                dt_from = datetime.strptime(
                    ver.date_start, DEFAULT_SERVER_DATE_FORMAT)
                dt_to = datetime.strptime(ver.date, DEFAULT_SERVER_DATE_FORMAT)
                if dt_to < dt_from:
                    raise ValidationError(
                        'Expiration date should be greater then Start Date.')

    @api.model
    def create(self, vals):
        """
        This Method is used to overrides ORM create method,
        to change state and tenant of related property.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if 'tenant_id' in vals:
            vals.update({'is_property': True})
        if 'property_id' in vals:
            prop_brw = self.env['account.asset.asset'].browse(
                vals['property_id'])
            prop_brw.write(
                {'current_tenant_id': vals['tenant_id'], 'state': 'book'})
        res = super(AccountAnalyticAccount, self).create(vals)
        res.ref = self.env['ir.sequence'].get(
                'account.analytic.account')
        return res

    @api.multi
    def write(self, vals):
        """
        This Method is used to overrides ORM write method,
        to change state and tenant of related property.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        rec = super(AccountAnalyticAccount, self).write(vals)
        for tenancy_rec in self:
            if vals.get('state'):
                if vals['state'] == 'draft':
                    tenancy_rec.write({
                        'tenancy_cancelled': False})
                if vals['state'] == 'open':
                    tenancy_rec.property_id.write({
                        'current_tenant_id':
                        tenancy_rec.tenant_id.id,
                        'state': 'normal'})
                if vals['state'] == 'close':
                    tenancy_rec.property_id.write(
                        {'state': 'draft', 'current_tenant_id': False})
        return rec

    @api.multi
    def unlink(self):
        """
        Overrides ORM unlink method,
        @param self: The object pointer
        @return: True/False.
        """
        rent_ids = []
        for tenancy_rec in self:
            if tenancy_rec.state == 'open':
                raise Warning(
                    _('You cannot delete Tenancy record if its in Inprogress \
                    state.'))
            analytic_ids = self.env['account.analytic.line'].search(
                [('account_id', '=', tenancy_rec.id)])
            if analytic_ids and analytic_ids.ids:
                analytic_ids.unlink()
            rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', tenancy_rec.id)])
            if rent_ids:
                rent_ids.unlink()
            if tenancy_rec.property_id.property_manager and \
                    tenancy_rec.property_id.property_manager.id:
                releted_user = tenancy_rec.property_id.property_manager.id
                new_ids = self.env['res.users'].search(
                    [('partner_id', '=', releted_user)])
                if releted_user and new_ids and new_ids.ids:
                    new_ids.write(
                        {'tenant_ids': [(3, tenancy_rec.tenant_id.id)]})
            tenancy_rec.property_id.write(
                {'state': 'draft', 'current_tenant_id': False})
        return super(AccountAnalyticAccount, self).unlink()

    @api.multi
    @api.depends('amount_return')
    def amount_return_compute(self):
        """
        When you change Deposit field value, this method will change
        amount_fee_paid field value accordingly.
        @param self: The object pointer
        """
        for data in self:
            if data.amount_return > 0.00:
                data.deposit_return = True

    @api.onchange('property_id')
    def onchange_property_id(self):
        """
        This Method is used to set property related fields value,
        on change of property.
        @param self: The object pointer
        """
        if self.property_id:
            self.rent = self.property_id.ground_rent or False
            self.rent_type_id = self.property_id.rent_type_id and \
                self.property_id.rent_type_id.id or False

    @api.multi
    def button_receive(self):
        """
        This button method is used to open the related
        account payment form view.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        if not self._ids:
            return []
        for tenancy_rec in self:
            jonral_type = self.env['account.journal'].search(
                [('type', '=', 'cash')])
            if tenancy_rec.acc_pay_dep_rec_id and \
                    tenancy_rec.acc_pay_dep_rec_id.id:
                acc_pay_form_id = self.env[
                    'ir.model.data'].get_object_reference(
                        'account', 'view_account_payment_form')[1]
                return {
                    'view_type': 'form',
                    'view_id': acc_pay_form_id,
                    'view_mode': 'form',
                    'res_model': 'account.payment',
                    'res_id': self.acc_pay_dep_rec_id.id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': self._context,
                }
            if tenancy_rec.deposit == 0.00:
                raise Warning(_('Please Enter Deposit amount.'))
            if tenancy_rec.deposit < 0.00:
                raise Warning(
                    _('The deposit amount must be strictly positive.'))
            if not tenancy_rec.property_id.income_acc_id.id:
                raise Warning(
                    _('Please Configure Income Account from Property.'))
            ir_id = self.env['ir.model.data']._get_id(
                'account', 'view_account_payment_form')
            ir_rec = self.env['ir.model.data'].browse(ir_id)
            return {
                'view_mode': 'form',
                'view_id': [ir_rec.res_id],
                'view_type': 'form',
                'res_model': 'account.payment',
                'type': 'ir.actions.act_window',
                'nodestroy': True,
                'target': 'current',
                'domain': '[]',
                'context': {
                    'default_partner_id': tenancy_rec.tenant_id.parent_id.id,
                    'default_partner_type': 'customer',
                    'default_journal_id':  jonral_type and
                        jonral_type.ids[0] or False,
                    'default_payment_type': 'inbound',
                    'default_communication': 'Deposit Received',
                    'default_tenancy_id': tenancy_rec.id,
                    'default_amount': tenancy_rec.deposit,
                    'default_property_id': tenancy_rec.property_id.id,
                    'default_deposite_rec' : True,
                    'close_after_process': True,
                }
            }

    @api.multi
    def button_return(self):
        for data in self:
            account_jrnl_obj = self.env['account.journal'].search(
                [('type', '=', 'purchase')])
            inv_line_values = {
                'name': 'Deposit Return' or "",
                'origin': 'account.analytic.account' or "",
                'quantity': 1,
                'account_id': data.property_id.expense_account_id.id or False,
                'price_unit': data.deposit or 0.00,
                'account_analytic_id': data.id or False,
            }

            inv_values = {
                'origin': 'Deposit Return For ' + data.name or "",
                'type': 'in_invoice',
                'property_id': data.property_id.id,
                'partner_id': data.tenant_id.parent_id.id or False,
                'account_id':
                    data.tenant_id.parent_id.property_account_payable_id.id or
                    False,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'date_invoice': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'new_tenancy_id': data and data.id,
                'reference': data.ref,
                'journal_id': account_jrnl_obj and account_jrnl_obj.ids[0] or
                False,
            }

            acc_id = self.env['account.invoice'].create(inv_values)
            data.write({'invc_id': acc_id.id})
            wiz_form_id = self.env['ir.model.data'].get_object_reference(
                'account', 'invoice_supplier_form')[1]
            return {
                'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': data.invc_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': self._context,
            }

    @api.multi
    def button_start(self):
        """
        This button method is used to Change Tenancy state to Open.
        @param self: The object pointer
        """
        for current_rec in self:
            if current_rec.property_id.property_manager and \
                    current_rec.property_id.property_manager.id:
                releted_user = current_rec.property_id.property_manager.id
                new_ids = self.env['res.users'].search(
                    [('partner_id', '=', releted_user)])
                if releted_user and new_ids and new_ids.ids:
                    new_ids.write(
                        {'tenant_ids': [(4, current_rec.tenant_id.id)]})
        return self.write({'state': 'open', 'rent_entry_chck': False})

    @api.multi
    def button_close(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        self.write({'state': 'close'})
        # return True

    @api.multi
    def inactive_record_t(self):
        return self.write({'active': False})

    @api.multi
    def active_record_t(self):
        return self.write({'active': True})

    @api.multi
    def button_cancel_tenancy(self):
        """
        This button method is used to Change Tenancy state to Cancelled.
        @param self: The object pointer
        """
        for record in self:
            self.write(
                {'state': 'cancelled', 'tenancy_cancelled': True})
            self.property_id.write(
                {'state': 'draft'})
            rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', record.id),
                 ('paid', '=', False),
                 ('move_check', '=', False)])
            for value in rent_ids:
                value.write({'is_readonly': True})
        return True

    @api.multi
    def button_set_to_renew(self):
        """
        This Method is used to open Tenancy renew wizard.
        @param self: The object pointer
        @return: Dictionary of values.
        """
        cr, uid, context = self.env.args
        context = dict(context)
        for tenancy_brw in self:
            tenancy_rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', tenancy_brw.id),
                 ('move_check', '=', False)])
            # if len(tenancy_rent_ids.ids) > 0:
            #     raise Warning(
            #         _('In order to Renew a Tenancy, Please make all related \
            #         Rent Schedule entries posted.'))
            context.update({'edate': tenancy_brw.date})
            return {
                'name': ('Tenancy Renew Wizard'),
                'res_model': 'renew.tenancy',
                'type': 'ir.actions.act_window',
                'view_id': False,
                'view_mode': 'form',
                'view_type': 'form',
                'target': 'new',
                'context': {'default_start_date': context.get('edate')}
            }

    # @api.model
    # def cron_property_states_changed(self):
    #     """
    #     This Method is called by Scheduler for change property state
    #     according to tenancy state.
    #     @param self: The object pointer
    #     """
    #     curr_date = datetime.now().date()
    #     tncy_ids = self.search([('date_start', '<=', curr_date),
    #                             ('date', '>=', curr_date),
    #                             ('state', '=', 'open'),
    #                             ('is_property', '=', True)])
    #     if len(tncy_ids.ids) != 0:
    #         for tncy_data in tncy_ids:
    #             if tncy_data.property_id and tncy_data.property_id.id:
    #                 tncy_data.property_id.write(
    #                     {'state': 'normal', 'color': 7})
    #     return True

    @api.model
    def cron_property_tenancy(self):
        """
        This Method is called by Scheduler to send email
        to tenant as a reminder for rent payment.
        @param self: The object pointer
        """
        tenancy_ids = []
        due_date = datetime.now().date() + relativedelta(days=7)
        tncy_ids = self.search(
            [('is_property', '=', True), ('state', '=', 'open')])
        for tncy_data in tncy_ids:
            tncy_rent_ids = self.env['tenancy.rent.schedule'].search(
                [('tenancy_id', '=', tncy_data.id),
                 ('start_date', '=', due_date)])
            if tncy_rent_ids and tncy_rent_ids.ids:
                tenancy_ids.append(tncy_data.id)
        tenancy_sort_ids = list(set(tenancy_ids))
        model_data_id = self.env['ir.model.data'].get_object_reference(
            'property_management', 'property_email_template')[1]
        template_brw = self.env['mail.template'].browse(model_data_id)
        for tenancy in tenancy_sort_ids:
            template_brw.send_mail(
                tenancy, force_send=True, raise_exception=False)
        return True

    @api.multi
    def create_rent_schedule(self):
        """
        This button method is used to create rent schedule Lines.
        @param self: The object pointer
        """
        rent_obj = self.env['tenancy.rent.schedule']
        for tenancy_rec in self:
            d1 = datetime.strptime(
                    tenancy_rec.date_start, DEFAULT_SERVER_DATE_FORMAT)
            d2 = datetime.strptime(
                    tenancy_rec.date, DEFAULT_SERVER_DATE_FORMAT)
            if tenancy_rec.rent_type_id.renttype == 'Weekly':
                interval = int(tenancy_rec.rent_type_id.name)
                if d2 < d1:
                    raise Warning(
                        _('End date must be greater than start date.'))
                wek_diff = (d2 - d1)
                wek_tot1 = (wek_diff.days) / (interval * 7)
                if wek_diff.days == 0:
                    wek_tot1 = 1
                if wek_tot1 > 0:
                    for wek_rec in range(wek_tot1):
                        wek_date = d1 + relativedelta(weeks=wek_rec)
                        exist_ids = rent_obj.search(
                            [('start_date', '=', wek_date.strftime(
                                DEFAULT_SERVER_DATE_FORMAT)),
                             ('tenancy_id', '=', tenancy_rec.id)])
                        exist_ids.unlink()
                        rent_obj.create({
                            'start_date': wek_date.strftime(
                                DEFAULT_SERVER_DATE_FORMAT),
                            'amount': tenancy_rec.rent * interval or 0.0,
                            'property_id': tenancy_rec.property_id and
                            tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id,
                            'company_id': tenancy_rec.company_id.id
                                })
            elif tenancy_rec.rent_type_id.renttype != 'Weekly':
                if tenancy_rec.rent_type_id.renttype == 'Monthly':
                    interval = int(tenancy_rec.rent_type_id.name)
                if tenancy_rec.rent_type_id.renttype == 'Yearly':
                    interval = int(tenancy_rec.rent_type_id.name) * 12
                diff = abs((d1.year - d2.year) * 12 + (d1.month - d2.month))
                tot_rec = diff / interval
                tot_rec2 = diff % interval
                if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                    tot_rec2 += 1
                if diff == 0:
                    tot_rec2 = 1
                if tot_rec > 0:
                    # print"range(tot_rec)=====================>", range(tot_rec)
                    # print"range=====================>", tot_rec
                    for rec in range(tot_rec):
                        print type(rec)
                        exist_ids = rent_obj.search(
                            [('start_date', '=', d1.strftime(
                                DEFAULT_SERVER_DATE_FORMAT)), (
                                    'tenancy_id', '=', tenancy_rec.id)])

                        exist_ids.unlink()
                        rent_obj.create({
                            'start_date': d1.strftime(
                                DEFAULT_SERVER_DATE_FORMAT),
                            'amount': tenancy_rec.rent * interval or 0.0,
                            'property_id': tenancy_rec.property_id and
                            tenancy_rec.property_id.id or False,
                            'tenancy_id': tenancy_rec.id,
                            'currency_id': tenancy_rec.currency_id.id or False,
                            'rel_tenant_id': tenancy_rec.tenant_id.id,
                            'company_id': tenancy_rec.company_id.id

                            })
                        d1 = d1 + relativedelta(months=interval)
                if tot_rec2 > 0:
                    rent_obj.create({
                        'start_date': d1.strftime(DEFAULT_SERVER_DATE_FORMAT),
                        'amount': tenancy_rec.rent * tot_rec2 or 0.0,
                        'property_id': tenancy_rec.property_id and
                        tenancy_rec.property_id.id or False,
                        'tenancy_id': tenancy_rec.id,
                        'currency_id': tenancy_rec.currency_id.id or False,
                        'rel_tenant_id': tenancy_rec.tenant_id.id,
                        'company_id': tenancy_rec.company_id.id

                    })
        return tenancy_rec.write({'rent_entry_chck': True})
