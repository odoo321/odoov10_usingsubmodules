# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api


class WizardBookToAvailable(models.TransientModel):
    _name = 'book.available'

    current_ids = fields.Char(
        string='My ids')

    @api.multi
    def print_yes(self):
        """
        @param self: The object pointer
        """
        for curr_rec in self:
            curr_id = int(curr_rec.current_ids)
            for rec in self.env['account.asset.asset'].browse(curr_id):
                if rec.state in ('book', 'normal', 'close', 'sold'):
                    status = {'state': 'draft', 'property_manager': False}
                    rec.write(status)
        return True
