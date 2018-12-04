# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.exceptions import except_orm
from datetime import datetime
from dateutil import relativedelta


class AccountMove(models.Model):
    _inherit = "account.move"
    _description = "Account Entry"

    asset_id = fields.Many2one(
        comodel_name='account.asset.asset',
        help='Asset')
    schedule_date = fields.Date(
        string='Schedule Date',
        help='Rent Schedule Date.')
    source = fields.Char(
        string='Source',
        help='Source from where account move created.')

    @api.multi
    def assert_balanced(self):
        if not self.ids:
            return True
        prec = self.env['decimal.precision'].precision_get('Account')
        self._cr.execute("""\
        SELECT	  move_id
        FROM		account_move_line
        WHERE	   move_id in %s
        GROUP BY	move_id
        HAVING	  abs(sum(debit) - sum(credit)) > %s
        """, (tuple(self.ids), 10 ** (-max(5, prec))))
        self._cr.fetchall()
        if len(self._cr.fetchall()) != 0:
            raise UserError(_("Cannot create unbalanced journal entry."))
        return True

    @api.model
    def create(self, vals):
        company = self.env.user.company_id
        restriction_days = company.restriction_days
        if self.env.user.has_group('property_management.groups_back_entry_block'):
            entry_block_group = self.env.ref('property_management.groups_back_entry_block')
            if entry_block_group:
                today = datetime.today()
                invoice_date = vals.get('date')
                date = datetime.strptime(invoice_date, '%Y-%m-%d')
                diff = (today - date).days
                if restriction_days > 0:
                    if restriction_days < diff:
                        raise except_orm(('Warning!'), _("You can't create\
                     back dated entries. Please contact system Administrator"))
        return super(AccountMove, self).create(vals)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    deposite = fields.Boolean(
        string='Deposit',
    )


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Tenancy Name.')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    amount_due = fields.Monetary(
        comodel_name='res.partner',
        related='partner_id.credit',
        readonly=True,
        default=0.0,
        help='Display Due amount of Customer')
    payment_move_id = fields.Many2one(
        comodel_name='account.move',
        string='Move')
    deposite_rec = fields.Boolean(
        string='Deposit')

    @api.model
    def default_get(self, fields):
        rec = super(AccountPayment, self).default_get(fields)
        company = self.env['res.company']._company_default_get(
            'account.payment')
        jonral_type = self.env['account.journal'].search(
            [('type', '=', 'cash'), ('company_id', '=', company.id)])
        for a in jonral_type:
            rec['journal_id'] = a.id
        return rec

    @api.multi
    def post(self):
        res = super(AccountPayment, self).post()
        print"res:::::::::::::::::::", res
        for data in self.invoice_ids:
            data.write({'journal_name_p': self.move_name})
        if self._context.get('return'):
            invoice_obj = self.env['account.invoice']
            invoice_browse = invoice_obj.browse(
                self._context['active_id']).new_tenancy_id
            invoice_browse.write({'amount_return': self.amount})
        if self.tenancy_id and self.deposite_rec:
            # print"::::::::::::::::::::::::::"
            self.tenancy_id.write({'deposit_received' : True})

        return res

    @api.model
    def create(self, vals):
        res = super(AccountPayment, self).create(vals)
        if res and res.id and res.tenancy_id and res.tenancy_id.id:
            if res.deposite_rec == True:
                res.tenancy_id.write({'acc_pay_dep_rec_id': res.id})
            if res.payment_type == 'outbound':
                res.tenancy_id.write({'acc_pay_dep_ret_id': res.id})
        return res

    @api.multi
    def back_to_tenancy(self):
        """
        This method will open a Tenancy form view.
        @param self: The object pointer
        @param context: A standard dictionary for contextual values
        """
        for vou_brw in self:
            open_move_id = self.env['ir.model.data'].get_object_reference(
                'property_management', 'property_analytic_view_form')[1]
            tenancy_id = vou_brw.tenancy_id and vou_brw.tenancy_id.id
            if tenancy_id:
                return {
                    'view_type': 'form',
                    'view_id': open_move_id,
                    'view_mode': 'form',
                    'res_model': 'account.analytic.account',
                    'res_id': tenancy_id,
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'context': self._context,
                }
            else:
                return True

# 	Gives Credit amount line
    def _get_counterpart_move_line_vals(self, invoice=False):
        vals = super(AccountPayment, self)._get_counterpart_move_line_vals(
            invoice=invoice)
        if vals and self.tenancy_id and self.tenancy_id.id:
            vals.update({'tenancy_id': self.tenancy_id.id})
            if self.payment_type in ('inbound', 'outbound'):
                vals.update({'analytic_account_id': False})
            if self.deposite_rec == True:
                vals.update({'deposite': True})
        return vals

# 	Gives Debit amount line
    def _get_liquidity_move_line_vals(self, amount):
        vals = super(
            AccountPayment, self)._get_liquidity_move_line_vals(amount)
        if vals and self.tenancy_id and self.tenancy_id.id:
            vals.update({'tenancy_id': self.tenancy_id.id})
            if self.payment_type in ('inbound', 'outbound'):
                vals.update({'analytic_account_id': self.tenancy_id.id})
            if self.deposite_rec == True:
                vals.update({'deposite': True})

        return vals

    def _create_payment_entry(self, amount):
        move = super(AccountPayment, self)._create_payment_entry(amount)
        if move and move.id and self.property_id and self.property_id.id:
            move.write({
                'asset_id': self.property_id.id or False,
                'source': self.tenancy_id.name or False
                })
        self.write({'payment_move_id': move.id})
        return move


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property Name.')
    new_tenancy_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')
    schedule_id = fields.Many2one(
        comodel_name="tenancy.rent.schedule",
        string="Schedule")
    journal_name_p = fields.Char(
        'Journal Name')

    @api.multi
    def action_move_create(self):
        res = super(AccountInvoice, self).action_move_create()
        # print"res:::::::::::", res.line
        for inv_rec in self:
            if inv_rec.move_id and inv_rec.move_id.id:
                inv_rec.move_id.write({'asset_id': inv_rec.property_id.id
                                       or False,
                                       'ref': 'Invoice',
                                       'source': inv_rec.property_id.name
                                       or False})
                line = inv_rec.move_id.line_ids
                for data in line:
                    data.write({'tenancy_id': inv_rec.new_tenancy_id.id})
        return res
