# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import odoo.addons.decimal_precision as dp
import re
import time
from datetime import datetime
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.tools import misc, DEFAULT_SERVER_DATE_FORMAT
from odoo.exceptions import ValidationError, Warning
    

class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    asset_id = fields.Many2one(
        'account.asset.asset',
        string='Property')

    @api.one
    @api.constrains('date_from', 'date_to')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Expiration date.
        @param self : object pointer
        """
        dte_fr = datetime.strptime(
            self.date_from, DEFAULT_SERVER_DATE_FORMAT)
        dte_to = datetime.strptime(
            self.date_to, DEFAULT_SERVER_DATE_FORMAT)
        if dte_to < dte_fr:
            raise ValidationError(
                'Start Date should be greater than End Date in Property \
                        Budget')


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    _description = 'Asset'

    @api.multi
    @api.depends('image')
    def _has_image(self):
        """
        This method is used to set Property image.
        @param self: The object pointer
        @return: True or False
        """
        result = False
        for p in self:
            if p.image:
                result = bool(p.image)
            p.has_image = result

    @api.multi
    @api.depends('date', 'tenancy_property_ids', 'tenancy_property_ids.date',
                 'tenancy_property_ids.date_start')
    def occupancy_calculation(self):
        """
        This Method is used to calculate occupancy rate.
        @param self: The object pointer
        @return: Calculated Occupancy Rate.
        """
        occ_rate = 0
        diffrnc = 0
        for prop_rec in self:
            if prop_rec.date:
                prop_date = datetime.strptime(
                    prop_rec.date, DEFAULT_SERVER_DATE_FORMAT).date()
                pur_diff = datetime.now().date() - prop_date
                purchase_diff = pur_diff.days
                if prop_rec.tenancy_property_ids and \
                        prop_rec.tenancy_property_ids.ids:
                    for tency_rec in prop_rec.tenancy_property_ids:
                        if tency_rec.date and tency_rec.date_start:
                            date_diff = datetime.strptime(
                                tency_rec.date, DEFAULT_SERVER_DATE_FORMAT) - \
                                datetime.strptime(tency_rec.date_start,
                                                  DEFAULT_SERVER_DATE_FORMAT)
                            diffrnc += date_diff.days
                if purchase_diff != 0 and diffrnc != 0:
                    occ_rate = (purchase_diff * 100) / diffrnc
                prop_rec.occupancy_rates = occ_rate

    @api.multi
    @api.depends('property_phase_ids', 'property_phase_ids.lease_price')
    def sales_rate_calculation(self):
        """
        This Method is used to calculate total sales rates.
        @param self: The object pointer
        @return: Calculated Sales Rate.
        """
        sal_rate = 0
        counter = 0
        les_price = 0
        for prop_rec in self:
            if prop_rec.property_phase_ids and prop_rec.property_phase_ids.ids:
                for phase in prop_rec.property_phase_ids:
                    counter = counter + 1
                    les_price += phase.lease_price
                if counter != 0 and les_price != 0:
                    sal_rate = les_price / counter
            prop_rec.sales_rates = sal_rate

    @api.multi
    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent')
    def roi_calculation(self):
        """
        This Method is used to Calculate ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        cost_of_investment = 0
        gain_from_investment = 0
        total = 0
        for prop_rec in self:
            if prop_rec.tenancy_property_ids and \
                    prop_rec.tenancy_property_ids.ids:
                for gain in prop_rec.tenancy_property_ids:
                    gain_from_investment += gain.rent
            if (cost_of_investment != 0 and gain_from_investment != 0 and
                    cost_of_investment != gain_from_investment):
                total = (gain_from_investment - cost_of_investment) / \
                    cost_of_investment
            prop_rec.roi = total

    @api.one
    @api.depends('roi')
    def ten_year_roi_calculation(self):
        """
        This Method is used to Calculate ten years ROI(Return On Investment).
        @param self: The object pointer
        @return: Calculated Return On Investment.
        """
        self.ten_year_roi = 10 * self.roi

    @api.multi
    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'property_phase_ids', 'property_phase_ids.operational_budget')
    def operation_cost(self):
        """
        This Method is used to Calculate Operation Cost.
        @param self: The object pointer
        @return: Calculated Operational Cost.
        """
        operational_cost = 0
        opr_cst = 0
        gain_from_investment = 0
        for prop_rec in self:
            if prop_rec.tenancy_property_ids and \
                    prop_rec.tenancy_property_ids.ids:
                for gain in prop_rec.tenancy_property_ids:
                    gain_from_investment += gain.rent
            if prop_rec.property_phase_ids and prop_rec.property_phase_ids.ids:
                for phase in prop_rec.property_phase_ids:
                    operational_cost += ((phase.operational_budget *
                                          phase.lease_price) / 100)
            if gain_from_investment != 0 and operational_cost != 0:
                opr_cst = operational_cost / gain_from_investment
            prop_rec.operational_costs = opr_cst

    @api.multi
    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids')
    def cal_simulation(self):
        """
        This Method is used to calculate simulation
        which is used in Financial Performance Report.
        @param self: The object pointer
        @return: Calculated Simulation Amount.
        """
        amt = 0.0
        for property_data in self:
            if property_data.tenancy_property_ids and \
                    property_data.tenancy_property_ids.ids:
                for tncy in property_data.tenancy_property_ids:
                    if tncy.rent_schedule_ids and tncy.rent_schedule_ids.ids:
                        for prty_tncy_data in tncy.rent_schedule_ids:
                            amt += prty_tncy_data.amount
            property_data.simulation = amt

    @api.multi
    @api.depends('tenancy_property_ids',
                 'tenancy_property_ids.rent_schedule_ids',
                 'tenancy_property_ids.rent_schedule_ids.move_check')
    def cal_revenue(self):
        """
        This Method is used to calculate revenue
        which is used in Financial Performance Report.
        @param self: The object pointer
        @return: Calculated Revenue Amount.
        """
        amt = 0.0
        for property_data in self:
            if property_data.tenancy_property_ids and \
                    property_data.tenancy_property_ids.ids:
                for tncy in property_data.tenancy_property_ids:
                    if tncy.rent_schedule_ids and tncy.rent_schedule_ids.ids:
                        for prty_tncy_data in tncy.rent_schedule_ids:
                            if prty_tncy_data.move_check:
                                amt += prty_tncy_data.amount
            property_data.revenue = amt

    @api.one
    @api.depends('value', 'salvage_value', 'depreciation_line_ids')
    def _amount_residual(self):
        """
        @param self: The object pointer
        @return: Calculated Residual Amount.
        """
        total_amount = 0.0
        total_residual = 0.0
        if self.value > 0:
            for line in self.depreciation_line_ids:
                if line.move_check:
                    total_amount += line.amount
            total_residual = self.value - total_amount - self.salvage_value
        self.value_residual = total_residual

    @api.one
    @api.depends('gfa_feet', 'unit_price')
    def cal_total_price(self):
        """
        This Method is used to Calculate Total Price.
        @param self: The object pointer
        @return: Calculated Total Price.
        """
        self.total_price = self.gfa_feet * self.unit_price

    image = fields.Binary(
        string='Image',
        help='Image of this property.')
    simulation_date = fields.Date(
        string='Simulation Date',
        help='Simulation Date.')
    age_of_property = fields.Date(
        string='Date',
        default=lambda *a: time.strftime(DEFAULT_SERVER_DATE_FORMAT),
        help='Property Build Date.')
    city = fields.Char(
        string='City',
        help='Address this property.')
    street = fields.Char(
        string='Street')
    street2 = fields.Char(
        string='Street2')
    township = fields.Char(
        string='Township')
    simulation_name = fields.Char(
        string='Simulation Name')
    construction_cost = fields.Char(
        string='Construction Cost')
    zip = fields.Char(
        string='Zip',
        size=24,
        change_default=True)
    # city = fields.Many2one(
    #     comodel_name='city.city',
    #     string='City')
    video_url = fields.Char(
        string='Video URL',
        help="//www.youtube.com/embed/mwuPTI8AT7M?rel=0")
    unit_price = fields.Float(
        string='Unit Price',
        help='Unit Price Per Sqft.')
    ground_rent = fields.Float(
        string='Ground Rent',
        help='Ground rent of Property.')
    gfa_meter = fields.Float(
        string='GFA(m)',
        help='Gross floor area in Meter.')
    sale_price = fields.Float(
        string='Sale Price',
        help='Sale price of the Property.')
    gfa_feet = fields.Float(
        string='GFA(Sqft)',
        help='Gross floor area in Square feet.')
    sales_rates = fields.Float(
        string="Sales Rate",
        compute='sales_rate_calculation',
        help='Average Sale/Lease price from property phase per Month.')
    ten_year_roi = fields.Float(
        string="10year ROI",
        compute='ten_year_roi_calculation',
        help="10year Return of Investment.")
    roi = fields.Float(
        string="ROI",
        compute='roi_calculation',
        store=True,
        help='ROI ( Return On Investment ) = ( Total Tenancy rent - Total \
        maintenance cost ) / Total maintenance cost.',)
    operational_costs = fields.Float(
        string="Operational Costs(%)",
        store=True,
        compute='operation_cost',
        help='Average of total operational budget and total rent.')
    occupancy_rates = fields.Float(
        string="Occupancy Rate",
        store=True,
        compute='occupancy_calculation',
        help='Total Occupancy rate of Property.')
    value_residual = fields.Float(
        string='Residual Value',
        method=True,
        compute='_amount_residual',
        digits=dp.get_precision('Account'),)
    tax_ids = fields.Many2many(
        comodel_name='account.tax',
        string="Municipality Taxes",
        help='Select the municipality and all taxes included in this property')
    simulation = fields.Float(
        string='Total Amount',
        compute='cal_simulation',
        store=True)
    revenue = fields.Float(
        string='Revenue',
        compute='cal_revenue',
        store=True)
    total_price = fields.Float(
        string='Total Price',
        compute='cal_total_price',
        help='Total Price of Property, \nTotal Price = Unit Price * \
        GFA (Sqft).')
    has_image = fields.Boolean(
        compute='_has_image')
    pur_instl_chck = fields.Boolean(
        string='Purchase Installment Check',
        default=False)
    sale_instl_chck = fields.Boolean(
        string='Sale Installment Check',
        default=False)
    color = fields.Integer(
        string='Color',
        default=4)
    floor = fields.Integer(
        string='Floor',
        help='Number of Floors.')
    no_of_towers = fields.Integer(
        string='No of Towers',
        help='Number of Towers.')
    no_of_property = fields.Integer(
        string='Property Per Floors.',
        help='Number of Properties Per Floor.')
    income_acc_id = fields.Many2one(
        comodel_name='account.account',
        string='Income Account',
        help='Income Account of Property.')
    expense_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Expense Account',
        help='Expense Account of Property.')
    parent_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Parent Property',
        help='If this property contains any parent property you can choose \
        here,if not then leave it as blank.')
    current_tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Current Tenant')
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country')
    state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='State',
        ondelete='restrict')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        index=True)
    analytic_acc_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Analytic Account')
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type',
        help='Type of Rent.')
    contact_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Contact Name',
        domain="[('tenant', '=', True)]")
    property_manager = fields.Many2one(
        comodel_name='res.partner',
        string='Property Manager')
    room_ids = fields.One2many(
        comodel_name='property.room',
        inverse_name='property_id',
        string='Rooms')
    property_phase_ids = fields.One2many(
        comodel_name='property.phase',
        inverse_name='phase_id',
        string='Phase')
    property_photo_ids = fields.One2many(
        comodel_name='property.photo',
        inverse_name='photo_id',
        string='Photos')
    utility_ids = fields.One2many(
        comodel_name='property.utility',
        inverse_name='property_id',
        string='Utilities')
    nearby_ids = fields.One2many(
        comodel_name='nearby.property',
        inverse_name='property_id',
        string='Nearest Property')
    contract_attachment_ids = fields.One2many(
        comodel_name='property.attachment',
        inverse_name='property_id',
        string='Document')
    child_ids = fields.One2many(
        comodel_name='account.asset.asset',
        inverse_name='parent_id',
        string='Children Assets')
    property_insurance_ids = fields.One2many(
        comodel_name='property.insurance',
        inverse_name='property_insurance_id',
        string='Insurance')
    tenancy_property_ids = fields.One2many(
        comodel_name='account.analytic.account',
        inverse_name='property_id',
        string='Tenancy Property')
    crossovered_budget_line_property_ids = fields.One2many(
        comodel_name='crossovered.budget.lines',
        inverse_name='asset_id',
        string='Budget Lines')
    safety_certificate_ids = fields.One2many(
        comodel_name='property.safety.certificate',
        inverse_name='property_id',
        string='Safety Certificate')
    account_move_ids = fields.One2many(
        comodel_name='account.move',
        inverse_name='asset_id',
        string='Entries',
        readonly=True,
        states={'draft': [('readonly', False)]})
    depreciation_line_ids = fields.One2many(
        comodel_name='account.asset.depreciation.line',
        inverse_name='asset_id',
        string='Depreciation Lines',
        readonly=True,
        states={'draft': [('readonly', False)]})
    bedroom = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Bedrooms',
        default='1')
    bathroom = fields.Selection(
        [('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4'),
         ('5', '5+')],
        string='Bathrooms',
        default='1')
    facing = fields.Selection(
        [('north', 'North'), ('south', 'South'),
         ('east', 'East'), ('west', 'West')],
        string='Facing',
        help='The property is been faced in which direction')
    furnished = fields.Selection(
        [('none', 'None'),
         ('semi_furnished', 'Semi Furnished'),
         ('full_furnished', 'Full Furnished')],
        string='Furnishing',
        default='none',
        help='Furnishing.')
    state = fields.Selection(
        [('new_draft', 'Booking Open'),
         ('draft', 'Available'),
         ('book', 'Booked'),
         ('normal', 'On Lease'),
         ('close', 'Sale'),
         ('sold', 'Sold'),
         ('cancel', 'Cancel')],
        string='State',
        required=True,
        default='draft',
        help="When an asset is created, the status is 'Available'.")
    rent_type_id = fields.Many2one(
        comodel_name='rent.type',
        string='Rent Type')

    @api.multi
    @api.onchange('state_id')
    def state_details_change(self):
        if self.state_id:
            self.country_id = self.state_id.country_id.id

    @api.model
    def create(self, vals):
        """
        This Method is used to overrides orm create method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if not vals:
            vals = {}
        if 'message_follower_ids' in vals:
            del vals['message_follower_ids']
        vals['code'] = self.env['ir.sequence'].next_by_code('property')
        if vals.get('parent_id'):
            parent_periods = self.browse(vals.get('parent_id'))
            if parent_periods.rent_type_id and parent_periods.rent_type_id.id:
                vals.update({'rent_type_id': parent_periods.rent_type_id.id})
#         asset_id = super(AccountAssetAsset, self).create(vals)
        acc_analytic_id = self.env['account.analytic.account'].sudo()
        acc_analytic_id.create({'name': vals['name']})
        return super(AccountAssetAsset, self).create(vals)

    @api.multi
    def write(self, vals):
        """
        This Method is used to overrides orm write method.
        @param self: The object pointer
        @param vals: dictionary of fields value.
        """
        if 'state' in vals and vals['state'] == 'new_draft':
            vals.update({'color': 0})
        if 'state' in vals and vals['state'] == 'draft':
            vals.update({'color': 4})
        if 'state' in vals and vals['state'] == 'book':
            vals.update({'color': 2})
        if 'state' in vals and vals['state'] == 'normal':
            vals.update({'color': 7})
        if 'state' in vals and vals['state'] == 'close':
            vals.update({'color': 9})
        if 'state' in vals and vals['state'] == 'sold':
            vals.update({'color': 9})
        if 'state' in vals and vals['state'] == 'cancel':
            vals.update({'color': 1})
        return super(AccountAssetAsset, self).write(vals)

    @api.multi
    def unlink(self):
        """Allows to delete property in available,sold states"""
        for property_rec in self:
            if property_rec.state != 'draft' and 'sold':
                raise Warning(_("Property in Available and Sold State can \
                only be deleted"))
        return super(AccountAssetAsset, self).unlink()

    @api.onchange('parent_id')
    def parent_property_onchange(self):
        """
        when you change Parent Property, this method will change
        address fields values accordingly.
        @param self: The object pointer
        """
        if self.parent_id:
            self.street = self.parent_id.street or ''
            self.street2 = self.parent_id.street2 or ''
            self.township = self.parent_id.township or ''
            self.city = self.parent_id.city or ''
            self.state_id = self.parent_id.state_id.id or False
            self.zip = self.parent_id.zip or ''
            self.country_id = self.parent_id.country_id.id or False

    @api.onchange('gfa_feet')
    def sqft_to_meter(self):
        """
        when you change GFA Feet, this method will change
        GFA Meter field value accordingly.
        @param self: The object pointer
        @return: Calculated GFA Feet.
        """
        meter_val = 0.0
        if self.gfa_feet:
            meter_val = float(self.gfa_feet / 10.7639104)
        self.gfa_meter = meter_val

    @api.onchange('unit_price', 'gfa_feet')
    def unit_price_calc(self):
        """
        when you change Unit Price and GFA Feet fields value,
        this method will change Total Price and Purchase Value
        accordingly.
        @param self: The object pointer
        """
        if self.unit_price and self.gfa_feet:
            self.total_price = float(self.unit_price * self.gfa_feet)
            self.value = float(self.unit_price * self.gfa_feet)
        if self.unit_price and not self.gfa_feet:
            raise ValidationError(_('Please Insert GFA(Sqft) Please'))

    @api.multi
    def edit_status(self):
        """
        This method is used to change property state to book.
        @param self: The object pointer
        """
        for rec in self:
            if not rec.property_manager:
                raise ValidationError(_('Please Insert Owner Name'))

        return self.write({'state': 'book'})

    @api.multi
    def edit_status_book(self):
        """
        This method will open a wizard.
        @param self: The object pointer
        """
        cr, uid, context = self.env.args
        context = dict(context)
        for rec in self:
            context.update({'edit_result': rec.id})
            self.env.args = cr, uid, misc.frozendict(context)
        return {
            'name': ('wizard'),
            'res_model': 'book.available',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
            'context': {'default_current_ids': context.get('edit_result')},
        }

    @api.multi
    def open_url(self):
        """
        This Button method is used to open a URL
        according fields values.
        @param self: The object pointer
        """
        for line in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if line.name:
                street_s = re.sub(r'[^\w]', ' ', line.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street:
                street_s = re.sub(r'[^\w]', ' ', line.street)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.street2:
                street_s = re.sub(r'[^\w]', ' ', line.street2)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.township:
                street_s = re.sub(r'[^\w]', ' ', line.township)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.city:
                street_s = re.sub(r'[^\w]', ' ', line.city)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.state_id:
                street_s = re.sub(r'[^\w]', ' ', line.state_id.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.country_id:
                street_s = re.sub(r'[^\w]', ' ', line.country_id.name)
                street_s = re.sub(' +', '+', street_s)
                url += street_s + '+'
            if line.zip:
                url += line.zip
            return {
                'name': 'Go to website',
                'res_model': 'ir.actions.act_url',
                'type': 'ir.actions.act_url',
                'target': 'current',
                'url': url
            }

    @api.multi
    def button_normal(self):
        """
        This Button method is used to change property state to On Lease.
        @param self: The object pointer
        """
        return self.write({'state': 'normal'})

    @api.multi
    def button_sold(self):
        """
        This Button method is used to change property state to Sold.
        @param self: The object pointer
        """
        for data in self:
            if not data.expense_account_id:
                raise Warning(_('Please Configure Income Account from \
                Property'))
            inv_line_values = {
                'name': data.name or "",
                'origin': 'account.asset.asset',
                'quantity': 1,
                'account_id': data.income_acc_id.id or False,
                'price_unit': data.sale_price or 0.00,
            }

            inv_values = {
                'origin': data.name or "",
                'type': 'out_invoice',
                'property_id': data.id,
                'partner_id': data.customer_id.id or False,
                'payment_term_id': data.payment_term.id,
                'invoice_line_ids': [(0, 0, inv_line_values)],
                'date_invoice': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'number': data.code or '',
            }
            self.env['account.invoice'].create(inv_values)
            data.write({'state': 'sold'})
        return True

    @api.multi
    def button_close(self):
        """
        This Button method is used to change property state to Sale.
        @param self: The object pointer
        """
        return self.write({'state': 'close'})

    @api.multi
    def button_cancel(self):
        """
        This Button method is used to change property state to Cancel.
        @param self: The object pointer
        """
        return self.write({'state': 'cancel'})

    @api.multi
    def button_draft(self):
        """
        This Button method is used to change property state to Available.
        @param self: The object pointer
        """
        return self.write({'state': 'draft'})

    @api.multi
    def date_addition(self, starting_date, end_date, period):
        date_list = []
        if period == 'monthly':
            while starting_date < end_date:
                date_list.append(starting_date)
                res = ((datetime.strptime(
                    starting_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(
                    months=1)).strftime(
                        DEFAULT_SERVER_DATE_FORMAT))
                starting_date = res
            return date_list
        else:
            while starting_date < end_date:
                date_list.append(starting_date)
                res = ((datetime.strptime(
                    starting_date, DEFAULT_SERVER_DATE_FORMAT) + relativedelta(
                    years=1)).strftime(DEFAULT_SERVER_DATE_FORMAT))
                starting_date = res
            return date_list

    @api.multi
    def inactive_record(self):
        return self.write({'active': False})

    @api.multi
    def active_record(self):
        return self.write({'active': True})

    @api.one
    @api.constrains('age_of_property')
    def _check_age_of_property(self):
        context = dict(self._context)
        if context is None:
            context = {}
        if self.age_of_property:
            age_of_property = datetime.strptime(
                self.age_of_property, DEFAULT_SERVER_DATE_FORMAT)
            today = datetime.today()
            if age_of_property > today:
                raise ValidationError(
                    _("You cannot create the property with future Date!"))
