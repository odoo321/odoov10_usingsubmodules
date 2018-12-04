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


class GatePassNo(models.Model):
    _name = 'gate.pass.no'

    pass_no = fields.Char(
        string="Gate Pass#")
    date = fields.Date(
        string='Issued Date')
    remarks = fields.Text(
        string='Remarks')
    tenancy_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string='Tenancy')


class WaterMeterReading(models.Model):
    _name = 'water.meter.reading'
    _description = 'Asset'

    date = fields.Datetime(
        string='Date')
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
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string="Property")
    tenancy_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string='Tenancy')
    remarks = fields.Char(
        string="Remarks/Notes")

    @api.onchange('tenancy_id')
    def onchange_tenancy_id(self):
        for data in self:
            if data.tenancy_id:
                data.property_id = data.tenancy_id.property_id.id or False


class ElectricityMeterReading(models.Model):
    _name = 'electricity.meter.reading'

    date = fields.Datetime(
        string='Date')
    eacc = fields.Char(
        string="ACC#",)
    emeter = fields.Char(
        string="Meter#",
        # compute='_get_reading',
        # inverse='_set_reading',
        group_operator="max")
    eop_date = fields.Date(
        string="Opening Date")
    eop_reading = fields.Char(
        string="Opening Reading")
    ecl_date = fields.Date(
        string="Closing Date")
    ecl_reading = fields.Char(
        string="Closing Reading")
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string="Property")
    tenancy_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string='Tenancy')
    remarks = fields.Char(
        string="Remarks/Notes")

    @api.onchange('tenancy_id')
    def onchange_tenancy_id(self):
        for data in self:
            if data.tenancy_id:
                data.property_id = data.tenancy_id.property_id.id or False

    # @api.onchange('emeter')
    # def onchange_eid(self):
    #     e_meter = self.env['electricity.meter.reading']
    #     for record in self:
    #         meter = e_meter.search(
    #             [('property_id', '=', record.property_id.id)],
    #             limit=1, order='emeter desc')
    #         if record.emeter < meter.emeter:
    #             raise Warning(('User Error!\nYou can\'t enter reading less \
    #             than previous reading %s !') % (meter.emeter))


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    _description = 'Asset'

    water_reading_id = fields.One2many(
        comodel_name='water.meter.reading',
        inverse_name='property_id',
        string="Water Reading")
    # last_reading = fields.Float(
    #     compute='_get_reading',
    #     inverse='_set_reading',
    #     string="Last Electricity Reading")
    ldate = fields.Datetime(
        string='Date')
    electricity_reading_id = fields.One2many(
        comodel_name='electricity.meter.reading',
        inverse_name='property_id',
        string="Electricity Reading")
    # elast_reading = fields.Float(
    #     compute='_get_electric_reading',
    #     inverse='_set_electric_reading',
    #     string="Last Electricity Reading")
    eldate = fields.Datetime(
        string='Date')
    furniture_ids = fields.One2many(
        comodel_name='furniture.allocation',
        inverse_name='property_id',
        string='Furniture Details')
#     furniture_ids = fields.Many2many(
#         comodel_name='furniture.allocation',
#         inverse_name='property_id',
#         string='Furniture')
    # def _get_reading(self):
    #     water_id = self.env['water.meter.reading']
    #     for record in self:
    #         water_reading = water_id.search(
    #             [('property_id', '=', record.id)], limit=1, order='wmeter desc')
    #         if water_reading:
    #             record.last_reading = water_reading.wmeter
    #         else:
    #             record.last_reading = 0

    # def _set_reading(self):
    #     analytic = self.env['account.analytic.account']
    #     w_meter = self.env['water.meter.reading']
    #     for record in self:
    #         meter = w_meter.search(
    #             [('property_id', '=', record.id)],
    #             limit=1, order='wmeter desc')
    #         if record.last_reading < meter.wmeter:
    #             raise Warning(('User Error!\nYou can\'t enter reading less \
    #             than previous reading %s !') % (meter.wmeter))
    #         if record.last_reading:
    #             analytic_id = analytic.search(
    #                 [('property_id', '=', record.id),
    #                  ('is_property', '=', True),
    #                  ('state', '!=', 'close'),
    #                  ('state', '!=', 'cancelled')])
    #             date = fields.Date.context_today(record)
    #             data = {
    #                 'wmeter': record.last_reading,
    #                 'date': date,
    #                 'property_id': record.id,
    #                 'tenancy_id': analytic_id.id
    #                 }
    #             self.env['water.meter.reading'].create(data)

    # def _get_electric_reading(self):
    #     elec_id = self.env['electricity.meter.reading']
    #     for record in self:
    #         elec_reading = elec_id.search(
    #             [('property_id', '=', record.id)], limit=1, order='emeter desc')
    #         if elec_reading:
    #             record.elast_reading = elec_reading.emeter
    #         else:
    #             record.elast_reading = 0

    # def _set_electric_reading(self):
    #     analytic = self.env['account.analytic.account']
    #     e_meter = self.env['electricity.meter.reading']
    #     for record in self:
    #         meter = e_meter.search(
    #             [('property_id', '=', record.id)],
    #             limit=1, order='emeter desc')
    #         if record.elast_reading < meter.emeter:
    #             raise Warning(('User Error!\nYou can\'t enter reading less \
    #             than previous reading %s !') % (meter.emeter))
    #         if record.elast_reading:
    #             analytic_id = analytic.search(
    #                 [('property_id', '=', record.id),
    #                  ('is_property', '=', True),
    #                  ('state', '!=', 'close'),
    #                  ('state', '!=', 'cancelled')])
    #             date = fields.Date.context_today(record)
    #             data = {
    #                 'emeter': record.elast_reading,
    #                 'date': date,
    #                 'property_id': record.id,
    #                 'tenancy_id': analytic_id.id
    #                 }
    #             e_meter.create(data)

    @api.constrains('furniture_ids')
    def furniture_id_lines(self):
        furniture = []
        for f in self[0].furniture_ids:
            if f.furniture_id.id in furniture:
                raise ValidationError(
                    _('You cannot add same furniture multiple times.'))
            furniture.append(f.furniture_id.id)
