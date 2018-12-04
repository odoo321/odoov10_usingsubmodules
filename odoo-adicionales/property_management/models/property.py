# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import re
import threading
from datetime import datetime, date
from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, api, _, sql_db
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

# import date


class TenantPartner(models.Model):
    _name = "tenant.partner"
    _inherits = {'res.partner': 'parent_id'}

    doc_name = fields.Char(
        string='Filename')
    id_attachment = fields.Binary(
        string='Identity Proof')
    tenancy_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='tenant_id',
        string='Tenancy Details',
        help='Tenancy Details')
    parent_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner',
        required=True,
        index=True,
        ondelete='cascade')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='agent_tenant_rel',
        column1='agent_id',
        column2='tenant_id',
        string='Tenant Details',
        domain=[('customer', '=', True), ('agent', '=', False)])
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        index=True)
    nationality_id = fields.Many2one(
        comodel_name='res.country',
        string='Nationality')
    passport_no = fields.Char(
        string="Passport No")
    identity_number = fields.Char(
        string='ID Number')
    sponsor_name = fields.Char(
        string='Sponsor Name')
    sponsor_mobile = fields.Char(
        string='Mobile',
        size=15)
    sponsor_Phone = fields.Char(
        string='Phone',
        size=15)
    sponsor_street = fields.Char(
        string='Street')
    sponsor_street2 = fields.Char(
        string='Street2')
    sponsor_city = fields.Char(
        # comodel_name='city.city',
        string='City')
    sponsor_state_id = fields.Char(
        string='State')
    sponsor_country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country')
    sponsor_zip = fields.Char(
        string='Zip')

    # mobiler = fields.Char(
    #     realated='mobile',
    #     string='Mobile')

    @api.model
    def default_get(self, fields):
        """
        This method is used to gets default values for tenant.
        @param self: The object pointer
        @param fields: Names of fields.
        @return: Dictionary of values.
        """
        context = dict(self._context or {})
        res = super(TenantPartner, self).default_get(fields)
        if context.get('tenant', False):
            res.update({'tenant': context['tenant']})
        res.update({'customer': True})
        return res

    @api.multi
    def unlink(self):
        """
        Overrides orm unlink method.
        @param self: The object pointer
        @return: True/False.
        """
        for tenant_rec in self:
            for tenancy in tenant_rec.tenancy_ids:
                if tenancy.state == 'open':
                    raise Warning(
                        _('You cannot delete Tenant record of tenancy in Inprogress state.'))
            if tenant_rec.parent_id and tenant_rec.parent_id.id:
                releted_user = tenant_rec.parent_id.id
                new_user_rec = self.env['res.users'].search(
                    [('partner_id', '=', releted_user)])
                if releted_user and new_user_rec and new_user_rec.ids:
                    new_user_rec.unlink()
        return super(TenantPartner, self).unlink()

    @api.multi
    def inactive_record(self):
        return self.write({'active': False})

    @api.multi
    def active_record(self):
        return self.write({'active': True})

    @api.multi
    @api.onchange('state_id')
    def state_details_change(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id


class PropertyType(models.Model):
    _name = "property.type"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class RentType(models.Model):
    _name = "rent.type"
    _order = 'sequence_in_view'

    @api.multi
    @api.depends('name', 'renttype')
    def name_get(self):
        res = []
        for rec in self:
            rec_str = ''
            if rec.name:
                rec_str += rec.name
            if rec.renttype:
                rec_str += ' ' + rec.renttype
            res.append((rec.id, rec_str))
        return res

    @api.model
    def name_search(self, name='', args=[], operator='ilike', limit=100):
        args += ['|', ('name', operator, name), ('renttype', operator, name)]
        cuur_ids = self.search(args, limit=limit)
        return cuur_ids.name_get()

    name = fields.Selection(
        [('1', '1'), ('2', '2'), ('3', '3'),
         ('4', '4'), ('5', '5'), ('6', '6'),
         ('7', '7'), ('8', '8'), ('9', '9'),
         ('10', '10'), ('11', '11'), ('12', '12')])

    renttype = fields.Selection(
        [('Monthly', 'Monthly'),
         ('Yearly', 'Yearly'),
         ('Weekly', 'Weekly')],
        string='Rent Type')
    sequence_in_view = fields.Integer(
        string='Sequence')


class RoomType(models.Model):
    _name = "room.type"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class Utility(models.Model):
    _name = "utility"

    name = fields.Char(
        string='Name',
        size=50,
        required=True)


class PlaceType(models.Model):
    _name = 'place.type'

    name = fields.Char(
        string='Place Type',
        size=50,
        required=True)


class PropertyPhase(models.Model):
    _name = "property.phase"

    end_date = fields.Date(
        string='End Date')
    start_date = fields.Date(
        string='Beginning Date')
    commercial_tax = fields.Float(
        string='Commercial Tax %')
    occupancy_rate = fields.Float(
        string='Occupancy Rate %')
    lease_price = fields.Float(
        string='Sales/lease Price Per Month')
    phase_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    operational_budget = fields.Float(
        string='Operational Budget %')
    company_income = fields.Float(
        string='Company Income Tax CIT %')
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        default=lambda self: self.env['res.country'].search(
            [('code', '=', 'OM')]))

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller
        than the Expiration date.
        ----------------------------------------------------------------
        @param self : object pointer
        """
        dte_fr = datetime.strptime(
            self.start_date, DEFAULT_SERVER_DATE_FORMAT)
        dte_to = datetime.strptime(
            self.end_date, DEFAULT_SERVER_DATE_FORMAT)

        if dte_to < dte_fr:
            raise ValidationError(
                'Start Date should be greater than End Date in Phases')


class PropertyPhoto(models.Model):
    _name = "property.photo"

    photos = fields.Binary(
        string='Photos')
    doc_name = fields.Char(
        string='Filename')
    photos_description = fields.Char(
        string='Description')
    photo_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class PropertyRoom(models.Model):
    _name = "property.room"

    note = fields.Text(
        string='Notes')
    width = fields.Float(
        string='Width')
    height = fields.Float(
        string='Height')
    length = fields.Float(
        string='Length')
    image = fields.Binary(
        string='Picture')
    name = fields.Char(
        string='Name',
        size=60)
    attach = fields.Boolean(
        string='Attach Bathroom')
    type_id = fields.Many2one(
        comodel_name='room.type',
        string='Room Type')
    assets_ids = fields.One2many(
        comodel_name='room.assets',
        inverse_name='room_id',
        string='Assets')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class NearbyProperty(models.Model):
    _name = 'nearby.property'

    distance = fields.Float(
        string='Distance (Km)')
    name = fields.Char(
        string='Name',
        size=100)
    type = fields.Many2one(
        comodel_name='place.type',
        string='Type')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class CostCost(models.Model):
    _name = "cost.cost"
    _order = 'date'

    @api.one
    @api.depends('move_id')
    def _get_move_check(self):
        self.move_check = bool(self.move_id)

    date = fields.Date(
        string='Date')
    amount = fields.Float(
        string='Amount')
    name = fields.Char(
        string='Description',
        size=100)
    payment_details = fields.Char(
        string='Payment Details',
        size=100)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Purchase Entry')
    purchase_property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    remaining_amount = fields.Float(
        string='Remaining Amount',
        help='Shows remaining amount in currency')
    move_check = fields.Boolean(
        compute='_get_move_check',
        method=True,
        string='Posted',
        store=True)
    rmn_amnt_per = fields.Float(
        string='Remaining Amount In %',
        help='Shows remaining amount in Percentage')
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')

    @api.multi
    def create_invoice(self):
        """
        This button Method is used to create account invoice.
        @param self: The object pointer
        """
        if not self.purchase_property_id.partner_id:
            raise Warning(_('Please Select Partner'))
        if not self.purchase_property_id.expense_account_id:
            raise Warning(_('Please Select Expense Account'))
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'purchase')])

        inv_line_values = {
            'origin': 'Cost.Cost',
            'name': 'Purchase Cost For' + '' + self.purchase_property_id.name,
            'price_unit': self.amount or 0.00,
            'quantity': 1,
            'account_id': self.purchase_property_id.expense_account_id.id,
        }

        inv_values = {
            'payment_term_id': self.purchase_property_id.payment_term.id or
            False,
            'partner_id': self.purchase_property_id.partner_id.id or False,
            'type': 'in_invoice',
            'property_id': self.purchase_property_id.id or False,
            'invoice_line_ids': [(0, 0, inv_line_values)],
            'date_invoice': datetime.now().strftime(
                DEFAULT_SERVER_DATE_FORMAT) or False,
            'journal_id': account_jrnl_obj and account_jrnl_obj.ids[0] or
            False,
        }
        acc_id = self.env['account.invoice'].create(inv_values)
        self.write({'invc_id': acc_id.id, 'move_check': True})
        context = dict(self._context or {})
        wiz_form_id = self.env['ir.model.data'].get_object_reference(
            'account', 'invoice_supplier_form')[1]
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

    @api.multi
    def open_invoice(self):
        """
        This Method is used to Open invoice
        @param self: The object pointer
        """
        context = dict(self._context or {})
        wiz_form_id = self.env['ir.model.data'].get_object_reference(
            'account', 'invoice_supplier_form')[1]
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


class RoomAssets(models.Model):
    _name = "room.assets"

    date = fields.Date(
        string='Date')
    name = fields.Char(
        string='Description',
        size=60)
    type = fields.Selection(
        [('fixed', 'Fixed Assets'),
         ('movable', 'Movable Assets'),
         ('other', 'Other Assets')],
        string='Type')
    qty = fields.Float(
        string='Quantity')
    room_id = fields.Many2one(
        comodel_name='property.room',
        string='Property')


class AccountCheckDetail(models.Model):
    _name = "account.check.detail"

    date = fields.Date(
        string='Date')
    name = fields.Char(
        string='Check No',
        size=60)
    amount = fields.Float(
        string='Amount')
    bank_name = fields.Char(
        string='Bank name')
    tenant_id = fields.Many2one(
        comodel_name="tenant.partner",
        string='Tenant')
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string='Tenancy')
    state = fields.Selection(
        [('posted', 'Posted'),
         ('paid', 'Paid'),
         ('bounced', 'Bounced')],
        string='State')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')

    _sql_constraints = [
        ('name', 'unique(name)', 'Check Number must be unique !')
    ]

    @api.onchange('analytic_account_id')
    def analytic_account_id_onchange(self):
        for data in self:
            if data.analytic_account_id:
                data.tenant_id = data.analytic_account_id.tenant_id.id or False
                data.company_id = data.analytic_account_id.company_id.id or False
                data.property_id = data.analytic_account_id.property_id.id or False


class PropertyInsurance(models.Model):
    _name = "property.insurance"

    premium = fields.Float(
        string='Premium')
    end_date = fields.Date(
        string='End Date')
    doc_name = fields.Char(
        string='Filename')
    contract = fields.Binary(
        string='Contract')
    start_date = fields.Date(
        string='Start Date')
    name = fields.Char(
        string='Description',
        size=60)
    policy_no = fields.Char(
        string='Policy Number',
        size=60)
    contact = fields.Many2one(
        comodel_name='res.partner',
        string='Insurance Comapny')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Related Company')
    property_insurance_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    payment_mode_type = fields.Selection(
        [('monthly', 'Monthly'),
         ('semi_annually', 'Semi Annually'),
         ('yearly', 'Annually')],
        string='Payment Term',
        size=40)

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller
        than the Expiration date.
        @param self : object pointer
        """
        dte_fr = datetime.strptime(
            self.start_date, DEFAULT_SERVER_DATE_FORMAT)
        dte_to = datetime.strptime(
            self.end_date, DEFAULT_SERVER_DATE_FORMAT)
        if dte_to < dte_fr:
            raise ValidationError(
                'Start Date should be less than End Date in Property \
                    Insurance')


class TenancyRentSchedule(models.Model):
    _name = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"
    _order = 'start_date'

    @api.multi
    @api.depends('invc_id.state')
    def _get_move_check(self):
        for data in self:
            data.move_check = bool(data.move_id)
            if data.invc_id:
                if data.invc_id.state == 'paid':
                    data.move_check = True

    @api.depends('invc_id', 'invc_id.state')
    def invoice_paid_true(self):
        for data in self:
            if data.invc_id:
                if data.invc_id.state == 'paid':
                    data.paid = True

    note = fields.Text(
        string='Notes',
        help='Additional Notes.')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env['res.company']._company_default_get(
            'tenancy.rent.schedule'))
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        required=True)
    amount = fields.Monetary(
        string='Amount',
        default=0.0,
        currency_field='currency_id',
        help="Rent Amount.")
    start_date = fields.Date(
        string='Date',
        help='Start Date.')
    end_date = fields.Date(
        string='End Date',
        help='End Date.')
    cheque_detail = fields.Many2one(
        comodel_name='account.check.detail',
        string='Check Details')
    cheque_date = fields.Date(
        related='cheque_detail.date',
        string='Cheque Date',
        help='Cheque Date.')
    move_check = fields.Boolean(
        compute='_get_move_check',
        method=True,
        string='Posted',
        store=True)
    rel_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string="Tenant")
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Depreciation Entry')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    paid = fields.Boolean(
        compute="invoice_paid_true",
        store=True,
        method=True,
        string='Paid',
        help="True if this rent is paid by tenant")
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    inv = fields.Boolean(
        string='Invoice')
    paid_amount = fields.Float(
        related='cheque_detail.amount',
        string='Paid Amount',
        help='Paid Amount.')
    pen_amt = fields.Float(
        string='Pending Amount',
        help='Pending Amount.')
    is_readonly = fields.Boolean(
        string='Readonly')
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Payment')

    @api.onchange('tenancy_id')
    def onchange_property_id(self):
        if self.tenancy_id:
            self.rel_tenant_id = self.tenancy_id.tenant_id and \
                self.tenancy_id.tenant_id.id or False
            self.currency_id = self.tenancy_id.currency_id and \
                self.tenancy_id.currency_id.id or False
            self.amount = self.tenancy_id.rent or 0.00
            self.company_id = self.tenancy_id.company_id

    @api.multi
    def create_invoice(self):
        """
        Create invoice for Rent Schedule.
        """

        aa = self.env['res.company']._company_default_get(
            'tenancy.rent.schedule')
        journal_ids = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.company_id.id)])
        inv_line_values = {
            'origin': 'tenancy.rent.schedule',
            'name': 'Tenancy(Rent) Cost',
            'price_unit': self.amount or 0.00,
            'quantity': 1,
            'account_id': self.tenancy_id.property_id.income_acc_id.sudo().id or
            False,
            'account_analytic_id': self.tenancy_id.id or False,
        }
        if self.tenancy_id.multi_prop:
            for data in self.tenancy_id.prop_id:
                for account in data.property_ids.income_acc_id:
                    inv_line_values.update({'account_id': account.id})

        inv_values = {
            'partner_id': self.tenancy_id.tenant_id.parent_id.id or False,
            'type': 'out_invoice',
            'schedule_id': self.id,
            'new_tenancy_id': self.tenancy_id.id,
            'property_id': self.tenancy_id.property_id.id or False,
            'date_invoice': self.start_date or False,
            'journal_id': journal_ids and journal_ids.ids[0] or False,
            'invoice_line_ids': [(0, 0, inv_line_values)],
            'company_id': self.company_id.sudo().id,
            'partner_bank_id': self.company_id.bank_id.sudo().id
        }
        acc_id = self.env['account.invoice'].create(inv_values)
        # print"open_id::::::::::", open_id
        self.write({'invc_id': acc_id.id, 'inv': True})
        # return acc_id
        # open_id = self.invc_id.action_invoice_open()
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

    @api.multi
    def open_invoice(self):
        if self.invc_id.id:
            self.invc_id.schedule_id = self.id
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
        else:
            raise Warning(
                _('Invoice in access that invoice is deleted !!.'))

    @api.model
    def rent_done_cron(self):
        """
        This cron create invoice for current date rent.
        """
        # print"------------------"
        date_start = '2017-09-01'
        # date_today = date.today()
        # print"date----------------", date_today
        curr_dt = datetime.now()
        bdate = curr_dt.strftime(DEFAULT_SERVER_DATE_FORMAT)

        for data in self.search([('inv', '=', False), ('paid', '=', False), ('start_date', '<=', bdate), ('start_date', '>=', date_start)]):
            if data.tenancy_id.state == 'open':
                print"<<------Invoice-Created------>>"
                data.create_invoice()
        return True


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        if self._context.get('asset') or self._context.get('openinvoice'):
            tenancy = self.env['account.analytic.account']
            for data in tenancy.rent_schedule_ids.browse(
                    self._context.get('active_id')):
                if data:
                    tenan_rent_obj = self.env['tenancy.rent.schedule'].search(
                        [('invc_id', '=', data.id)])
                    amt = 0.0
                    for data1 in tenan_rent_obj:
                        if data1.invc_id.state == 'paid':
                            data1.paid = True
                            data1.move_check = True
                        if data1.invc_id:
                            amt = data1.invc_id.residual
                        data1.write({'pen_amt': amt, 'payment_id': self.id})
        return res


class PropertyUtility(models.Model):
    _name = "property.utility"

    note = fields.Text(
        string='Remarks')
    ref = fields.Char(
        string='Reference',
        size=60)
    expiry_date = fields.Date(
        string='Expiry Date')
    issue_date = fields.Date(
        string='Issuance Date')
    utility_id = fields.Many2one(
        comodel_name='utility',
        string='Utility')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact',
        domain="[('tenant', '=', True)]")

    @api.constrains('issue_date', 'expiry_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller
        than the Expiration date.
        @param self : object pointer
        """
        if self.issue_date and self.expiry_date:
            dte_issu = datetime.strptime(
                self.issue_date, DEFAULT_SERVER_DATE_FORMAT)
            dte_exp = datetime.strptime(
                self.expiry_date, DEFAULT_SERVER_DATE_FORMAT)
            if dte_issu > dte_exp:
                raise ValidationError(
                    'Issue Date should be greater than Expiry Date in \
                    Utilities')


class PropertySafetyCertificate(models.Model):
    _name = "property.safety.certificate"

    ew = fields.Boolean(
        'EW')
    weeks = fields.Integer(
        'Weeks')
    ref = fields.Char(
        'Reference',
        size=60)
    expiry_date = fields.Date(
        string='Expiry Date')
    name = fields.Char(
        string='Certificate',
        size=60,
        required=True)
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact',
        domain="[('tenant', '=', True)]")

    @api.one
    @api.constrains('expiry_date')
    def _check_expiry_date(self):
        context = dict(self._context)
        if context is None:
            context = {}
        if self.expiry_date:
            expiry_date = datetime.strptime(
                self.expiry_date, DEFAULT_SERVER_DATE_FORMAT)
            today = datetime.today()
            if expiry_date < today:
                raise ValidationError(_(
                    "You cannot Add expired safety certificate for \
                    the property!"))


class PropertyAttachment(models.Model):
    _name = 'property.attachment'

    doc_name = fields.Char(
        string='Filename')
    expiry_date = fields.Date(
        string='Expiry Date')
    contract_attachment = fields.Binary(
        string='Attachment')
    name = fields.Char(
        string='Description',
        size=64,
        requiered=True)
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class SaleCost(models.Model):
    _name = "sale.cost"
    _order = 'date'

    @api.one
    @api.depends('move_id')
    def _get_move_check(self):
        self.move_check = bool(self.move_id)

    date = fields.Date(
        string='Date')
    amount = fields.Float(
        string='Amount')
    name = fields.Char(
        string='Description',
        size=100)
    payment_details = fields.Char(
        string='Payment Details',
        size=100)
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency')
    move_id = fields.Many2one(
        comodel_name='account.move',
        string='Purchase Entry')
    sale_property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    remaining_amount = fields.Float(
        string='Remaining Amount',
        help='Shows remaining amount in currency')
    move_check = fields.Boolean(
        string='Posted',
        compute='_get_move_check',
        method=True,
        store=True)
    rmn_amnt_per = fields.Float(
        string='Remaining Amount In %',
        help='Shows remaining amount in Percentage')
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')

    @api.multi
    def create_invoice(self):
        """
        This button Method is used to create account invoice.
        @param self: The object pointer
        """
        if not self.sale_property_id.customer_id:
            raise Warning(_('Please Select Customer'))
        if not self.sale_property_id.income_acc_id:
            raise Warning(_('Please Configure Income Account from Property'))
        account_jrnl_obj = self.env['account.journal'].search(
            [('type', '=', 'sale')])

        inv_line_values = {
            'origin': 'Sale.Cost',
            'name': 'Purchase Cost For' + '' + self.sale_property_id.name,
            'price_unit': self.amount or 0.00,
            'quantity': 1,
            'account_id': self.sale_property_id.income_acc_id.id,
        }

        inv_values = {
            'payment_term_id': self.sale_property_id.payment_term.id or False,
            'partner_id': self.sale_property_id.customer_id.id or False,
            'type': 'out_invoice',
            'property_id': self.sale_property_id.id or False,
            'invoice_line_ids': [(0, 0, inv_line_values)],
            'date_invoice': datetime.now().strftime(
                DEFAULT_SERVER_DATE_FORMAT) or False,
            'journal_id': account_jrnl_obj and account_jrnl_obj.id[0] or False,
        }
        acc_id = self.env['account.invoice'].create(inv_values)
        self.write({'invc_id': acc_id.id, 'move_check': True})
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

    @api.multi
    def open_invoice(self):
        """
        This Method is used to Open invoice
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
