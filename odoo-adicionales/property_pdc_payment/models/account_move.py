# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields
class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    cheque_reference = fields.Char(copy=False,
        string='Cheque')