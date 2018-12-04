# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _

class ResCompany(models.Model):
    _inherit = "res.company"

    restriction_days = fields.Integer(
            string='Restriction Days',
            help='No of days to block back entries')

    _sql_constraints = [
        ('restriction_days','CHECK (restriction_days >= 0)', 'Restriction Days should\
         be grater than or equal to zero !')
    ]