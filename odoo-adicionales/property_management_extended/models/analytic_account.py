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
from odoo import models, fields, api, _
from odoo.exceptions import UserError, Warning, ValidationError
import time
from datetime import datetime


class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    wmeter_id = fields.Many2one(
        comodel_name='water.meter.reading',
        string='Water Meter')
    emeter_id = fields.Many2one(
        comodel_name='electricity.meter.reading',
        string='Electricity Meter')
    gate_pass_no = fields.One2many(
        comodel_name='gate.pass.no',
        inverse_name='tenancy_id',
        string="Gate Pass")
    furniture_ids = fields.One2many(
        comodel_name='furniture.allocation.tenancy',
        inverse_name='tenancy_id',
        string='Furniture')
    wacc = fields.Char(
        string="ACC#",)
    wmeter = fields.Char(
        string="Meter#",
        group_operator="max")
    wop_date = fields.Date(
        string="Opening Date")
    wop_reading = fields.Char(
        string="Opening Reading")
    wcl_date = fields.Date(
        string="Closing Date")
    wcl_reading = fields.Char(
        string="Closing Reading")
    wremarks = fields.Char(
        string="Remarks/Notes")
    eacc = fields.Char(
        string="ACC#",)
    emeter = fields.Char(
        string="Meter#",
        group_operator="max")
    eop_date = fields.Date(
        string="Opening Date")
    eop_reading = fields.Char(
        string="Opening Reading")
    ecl_date = fields.Date(
        string="Closing Date")
    ecl_reading = fields.Char(
        string="Closing Reading")
    eremarks = fields.Char(
        string="Remarks/Notes")
    get_whide = fields.Boolean(
        string='Water Hide')
    get_ehide = fields.Boolean(
        string='Electricity Hide')
    get_fhide = fields.Boolean(
        string='furniater Hide')
    status_we = fields.Selection(
        [('1', 'Move In'), ('2', 'Move Out')],
        string='Status')

    @api.multi
    def button_close(self):
        """
        This button method is used to Change Tenancy state to close.
        @param self: The object pointer
        """
        res = super(AccountAnalyticAccount, self).button_close()
        self.water_reading_create()
        self.electricity_reading_create()
        return res

    @api.multi
    def button_cancel_tenancy(self):
        """
        This button method is used to Change Tenancy state to Cancelled.
        @param self: The object pointer
        """
        res = super(AccountAnalyticAccount, self).button_cancel_tenancy()
        self.water_reading_create()
        self.electricity_reading_create()
        return res

    # @api.multi
    # def button_start(self):
    #     """
    #     This button method is used to Change Tenancy state to Open.
    #     @param self: The object pointer
    #     """
    #     res = super(AccountAnalyticAccount, self).button_start()
    #     self.get_water_reading()
    #     self.get_electricity_reading()
    #     return res

    def water_reading_create(self):
        water_obj = self.env['water.meter.reading']
        reading = []
        # if self.wcl_date < self.wop_date:
        #     raise ValidationError(
        #         'Closing date should be greater than opening date(water reading).')
        # if self.wcl_reading < self.wop_reading:
        #     raise ValidationError(
        #         'Closing reading should be greater than opening reading(water reading).')
        # if not self.wcl_reading and self.wcl_date:
        #     raise ValidationError(
        #         'Please enter water meter closing reading.')
        for record in self:
            vals = {
                'wacc': record.wacc,
                'wmeter': record.wmeter,
                'wop_date': record.wop_date,
                'wop_reading': record.wop_reading,
                'wcl_date': record.wcl_date,
                'wcl_reading': record.wcl_reading,
                'property_id': record.property_id.id,
                'tenancy_id': record.id,
                'remarks': record.wremarks,
            }
        water_obj.create(vals)

    @api.multi
    def get_water_reading(self):
        water_obj = self.env['water.meter.reading']
        water_id = water_obj.search([
            ('property_id', '=', self.property_id.id)], limit=1,
            order='wcl_reading desc')

        self.wacc = water_id.wacc
        self.wmeter = water_id.wmeter
        self.wop_date = datetime.now().date()
        self.wop_reading = water_id.wcl_reading
        self.wcl_date = False
        self.wcl_reading = False
        self.write({'get_whide': True})

    def electricity_reading_create(self):
        reading = []
        electricity_obj = self.env['electricity.meter.reading']
        # if self.ecl_date < self.eop_date:
        #     raise ValidationError(
        #         'Closing date should be greater than opening date(electricity date).')
        # if self.ecl_reading < self.eop_reading:
        #     raise ValidationError(
        #         'Closing reading should be greater than opening reading(electricity reading).')
        # if not self.ecl_reading and self.ecl_date:
        #     raise ValidationError(
        #         'Please enter electricity meter closing reading.')
        for record in self:
            vals = {
                'eacc': record.eacc,
                'emeter': record.emeter,
                'eop_date': record.eop_date,
                'eop_reading': record.eop_reading,
                'ecl_date': record.ecl_date,
                'ecl_reading': record.ecl_reading,
                'property_id': record.property_id.id,
                'tenancy_id': record.id,
                'remarks': record.eremarks,
            }
        electricity_obj.create(vals)

    @api.multi
    def get_electricity_reading(self):
        electricity_obj = self.env['electricity.meter.reading']
        electricity_id = electricity_obj.search([
            ('property_id', '=', self.property_id.id)], limit=1,
            order='ecl_reading desc')

        self.eacc = electricity_id.eacc
        self.emeter = electricity_id.emeter
        self.eop_date = datetime.now().date()
        self.eop_reading = electricity_id.ecl_reading
        self.ecl_date = False
        self.ecl_reading = False
        self.write({'get_ehide': True})

    @api.constrains('furniture_ids')
    def furniture_id_lines(self):
        furniture = []
        for f in self[0].furniture_ids:
            if f.furniture_id.id in furniture:
                raise ValidationError(
                    _('You cannot add same furniture multiple times.'))
            furniture.append(f.furniture_id.id)

    @api.multi
    def compute_furniture_details(self):
        furniture = self.env['furniture.allocation']
        furniture_ten_obj = self.env['furniture.allocation.tenancy']
        data = []
        for furni_line in self.furniture_ids:
            self.furniture_ids = [(2, furni_line.id)]
        if self.property_id:
            furniture_ids = furniture.search(
                [('property_id', '=', self.property_id.id)])
            for f in furniture_ids:
                data.append((0, False, {
                    'furniture_id': f.furniture_id.id,
                    'quantity': f.quantity,
                    'tenancy_id': self.id,
                    'property_id': self.property_id.id,
                    'remarks': f.remarks,
                    'uom_id': f.uom_id.id,
                }))
            self.furniture_ids = data
            self.write({'get_fhide': True})

    @api.multi
    def update_furniture_details(self, vals):
        lst = []
        for furni_line in self.property_id.furniture_ids:
            self.property_id.furniture_ids = [(2, furni_line.id)]

        furniture_ten_obj = self.env['furniture.allocation.tenancy']
        furniture_ids = furniture_ten_obj.search(
            [('tenancy_id', '=', self.id)])
        if furniture_ids:
            for f in furniture_ids:
                lst.append((0, False, {
                    'furniture_id': f.furniture_id.id,
                    'quantity': f.quantity,
                    'tenancy_id': self.id,
                    'property_id': self.property_id.id,
                    'remarks': f.remarks,
                    'uom_id': f.uom_id.id,
                }))
            self.property_id.furniture_ids = lst
