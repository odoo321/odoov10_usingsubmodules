# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo.exceptions import Warning, ValidationError
from odoo import models, fields, api, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset.asset'
    _description = 'Asset'

    commission_acc_id = fields.Many2one(
        comodel_name='account.account',
        string='Commission Account',
        help='Commission Account of Property.')
