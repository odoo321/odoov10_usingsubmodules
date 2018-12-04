# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import tools
from odoo import api, fields, models


class propertyAnalysisReport(models.Model):
    _name = "property.analysis.report"
    _description = "Sales Orders Statistics"
    _auto = False
    _rec_name = 'expir_date'
    _order = 'expir_date desc'

    name = fields.Char('Tenancy Reference', readonly=True)
    expir_date = fields.Date('Expire Date', readonly=True)
    property_id = fields.Many2one('account.asset.asset', 'Property', readonly=True)
    company = fields.Many2one('res.company', 'Company')
    tenancy_id = fields.Many2one('account.analytic.account', 'Tenancy', readonly=True)
    price_total = fields.Float('Total', readonly=True)
    balance_amount = fields.Float('Balance', readonly=True)
    advance_amount = fields.Float('Advance Amount', readonly=True)
    advance_receiv = fields.Float('Advance Received', readonly=True)
    advance_return = fields.Float('Advance Returned', readonly=True)

    @api.model_cr
    def init(self):
        tools.sql.drop_view_if_exists(self.env.cr, 'property_analysis_report')
        self.env.cr.execute("""
        CREATE or REPLACE view property_analysis_report
        as (SELECT
                a.id as id,
                a.property_id as property_id,
                a.tenant_id as tenancy_id,
                a.company_id as company,
                a.date as expir_date,
                ( select sum(amount) from tenancy_rent_schedule
                where tenancy_id = a.tenant_id) as
                price_total,
                ( select sum(pen_amt) from tenancy_rent_schedule
                where tenancy_id = a.tenant_id) as
                balance_amount,
                a.deposit as advance_amount,
                ( select amount from account_payment
                where state = 'posted' and payment_type = 'inbound' and
                tenancy_id = a.id) as advance_receiv,
                a.amount_return as advance_return
            FROM
                account_analytic_account a
            WHERE
                a.is_property = True AND a.active=True
            GROUP BY
                a.id,a.property_id,a.tenant_id,a.company_id
                )""")
