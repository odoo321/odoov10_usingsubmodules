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
from datetime import datetime, date


class FurnitureAllocationDetails(models.Model):
    _name = 'furniture.allocation.details'

    name = fields.Char(
        string='Furniture Name')


class FurnitureAllocation(models.Model):
    _name = 'furniture.allocation'
    _rec_name = 'furniture_id'

    furniture_id = fields.Many2one(
        comodel_name='furniture.allocation.details',
        string='Furniture Name')
    quantity = fields.Float(
        string='Quantity')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Unit Of Measure.')
    remarks = fields.Char(
        string='Remarks')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')


class FurnitureAllocationTenancy(models.Model):
    _name = 'furniture.allocation.tenancy'
    _rec_name = 'furniture_id'

    furniture_id = fields.Many2one(
        comodel_name='furniture.allocation.details',
        string='Furniture Name')
    quantity = fields.Float(
        string='Quantity')
    remarks = fields.Char(
        string='Remarks')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account')
    allocation_id = fields.Many2one(
        comodel_name='furniture.allocation',
        string='Allocation')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        string='Unit Of Measure.')


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def validate_invoice_corn(self):
        date_start = '2017-09-01'
        date_today = date.today()
        for data in self.search([('state', '=', 'draft'), ('type', '=', 'out_invoice'), ('date_invoice', '<=', date_today), ('date_invoice', '>=', date_start)]):
            if data.schedule_id:
                data.action_invoice_open()
        return True
