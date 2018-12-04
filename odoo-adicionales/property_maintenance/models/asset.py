# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    _description = 'Asset'

    maint_request = fields.Integer(
        string='Request',
        compute='request_count',
        help='Only shows new request maintenance for this property')
    maintenance_ids = fields.One2many(
        comodel_name='maintenance.request',
        inverse_name='property_id',
        string='Maintenance',
        help='Its shows over all maintenance for this property')

    @api.multi
    def request_count(self):
        for asset in self:
            res = self.env['maintenance.request'].search_count(
                [('property_id', '=', asset.id), ('done', '=', False)])
            asset.maint_request = res or 0

    @api.multi
    def open_maintenance(self):
        for asset in self:
            res = self.env['maintenance.request'].search(
                [('property_id', '=', asset.id), ('done', '=', False)])
        return {
            'name': _('Maintenance Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'maintenance.request',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', res.ids)],
        }

    @api.multi
    @api.depends('tenancy_property_ids', 'tenancy_property_ids.rent',
                 'maintenance_ids', 'maintenance_ids.cost')
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
            if prop_rec.maintenance_ids and prop_rec.maintenance_ids.ids:
                for maintenance in prop_rec.maintenance_ids:
                    cost_of_investment += maintenance.cost
            if prop_rec.tenancy_property_ids and \
                    prop_rec.tenancy_property_ids.ids:
                for gain in prop_rec.tenancy_property_ids:
                    gain_from_investment += gain.rent
            if (cost_of_investment != 0 and gain_from_investment != 0 and
                    cost_of_investment != gain_from_investment):
                total = (gain_from_investment - cost_of_investment) / \
                    cost_of_investment
            prop_rec.roi = total
