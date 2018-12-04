# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

import re
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"


    tenant = fields.Boolean(
        string='Tenant',
        help="Check this box if this contact is a tenant.")
    occupation = fields.Char(
        string='Occupation')
    agent = fields.Boolean(
        string='Agent',
        help="Check this box if this contact is a Agent.")
    is_worker = fields.Boolean(
        string='Worker',
        help="Check this box if this contact is a worker.")
    is_insurance = fields.Boolean(
        string='Insurance',
        help="Check this box if this contact is a Insurance Company/Partner.")
    mobile = fields.Char(
        string='Mobile')

class ResUsers(models.Model):
    _inherit = "res.users"

    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Related Tenant')
    tenant_ids = fields.Many2many(
        comodel_name='tenant.partner',
        relation='rel_ten_user',
        column1='user_id',
        column2='tenant_id',
        string='All Tenants')
