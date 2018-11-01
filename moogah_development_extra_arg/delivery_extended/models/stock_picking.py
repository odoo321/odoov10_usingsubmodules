# -*- coding: utf-8 -*-

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transport_company_id = fields.Many2one('res.partner', "Transport Company")
    freight_id = fields.Many2one('freight.freight', "Freight", readonly=True,
                                 states={'draft': [('readonly', False)],
                                         'sent': [('readonly', False)]})
    transport_note = fields.Text('Transport note')
    volume_done = fields.Float(string='Volume', digits=(16, 4),
                               compute='_compute_vol_wght',
                               help="Sum qty done * product volume in all operations")
    weight_done = fields.Float(string='Weight', digits=(16, 4),
                               compute='_compute_vol_wght',
                               help="Sum of qty done * product weight in all operations")

    @api.depends('pack_operation_product_ids',
                 'pack_operation_product_ids.qty_done')
    def _compute_vol_wght(self):
        for picking in self:
            picking.volume_done = sum(
                x.product_id.uom_id._compute_quantity(x.qty_done,
                                                      x.product_uom_id) * x.product_id.volume
                for x in picking.pack_operation_product_ids)
            picking.weight_done = sum(
                x.product_id.uom_id._compute_quantity(x.qty_done,
                                                      x.product_uom_id) * x.product_id.weight
                for x in picking.pack_operation_product_ids)

    @api.onchange('transport_company_id')
    def onchange_transport_company_id(self):
        self.transport_note = self.transport_company_id.comment
