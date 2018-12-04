# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from dateutil.relativedelta import relativedelta
from datetime import datetime

from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class RecurringMaintenanceType(models.Model):
    _name = 'recurring.maintenance.type'

    name = fields.Char(
        string='Maintenance Type',
        size=50,
        required=True,
        help='Name of Maintenance Type Example Maintain Garden, Maintain \
              Swimming pool')
    cost = fields.Float(
        string='Maintenance Cost',
        help='Cost of maintenance type',)
    maintenance_team_id = fields.Many2one(
        comodel_name='maintenance.team',
        string='Maintenance Team',
        help='Select team who manage this recurring maintenance.')


class RecurringMaintenanceLine(models.Model):
    _name = 'recurring.maintenance.line'

    date = fields.Date(
        string='Expiration Date',
        help="Tenancy contract end date.")
    r_maintenance = fields.Many2one(
        comodel_name='recurring.maintenance',
        string='Recurring Maintenance')
    maintenance_type_ids = fields.Many2many(
        comodel_name='recurring.maintenance.type',
        relation='recurring_maintenance_type_rel',
        column1='recurring_line_id',
        column2='maintenance_typ_id',
        string='Maintenance Types')


class RecurringMaintenance(models.Model):
    _name = 'recurring.maintenance'
    _rec_name = "tenancy"

    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy',
        help='Select tenancy name for recurring maintenance schedule \
            for that.')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        related='tenancy.property_id',
        string='Property',
        store=True,
        help='Property name related tenancy')
    start_date = fields.Date(
        string='Contract Start Date',
        related='tenancy.date_start',
        store=True,
        help='Tenancy contract start date')
    end_date = fields.Date(
        string='Contract End Date',
        related='tenancy.date',
        store=True,
        help='Tenancy contract end date')
    rmaintenance_line = fields.One2many(
        comodel_name='recurring.maintenance.line',
        inverse_name='r_maintenance',
        string='Line',
        help='its shows Scheduled Maintenance between contract duration')
    state = fields.Selection(
        [('draft', 'Open'),
         ('added', 'Scheduled')],
        string='Status',
        default='draft',
        help='In Open state show yet not create Scheduled Maintenance and \
        Scheduled state shows its created Scheduled Maintenance')
    maintenance_type = fields.Selection(
        [('monthly', 'monthly'),
         ('weekly', 'Weekly'),
         ('Daily', 'Daily')
         ],
        string='Recurring Type')
    kanban_state = fields.Selection(
        [('normal', 'In Progress'),
         ('blocked', 'Blocked'),
         ('done', 'Ready for next stage')],
        string='Kanban State',
        required=True,
        default='normal',
        track_visibility='onchange')
    priority = fields.Selection(
        [('0', 'Very Low'),
         ('1', 'Low'),
         ('2', 'Normal'),
         ('3', 'High')],
        string='Priority')
    color = fields.Integer('Color Index')
    close_date = fields.Date('Close Date')
    recuring = fields.Boolean(
        string='Recurring')

    @api.multi
    def schedule_recuring_maintenance(self):
        """
        This Method is used to schedule recurring maintenance,
        -----------------------------------------------------
        @param self: The object pointer
        """
        recurring_maintenance_line_obj = self.env['recurring.maintenance.line']
        tanency_recurring_obj = self.env['maintenance.cost']
        recurring_ids = []
        tanency_recurring_ids = tanency_recurring_obj.search(
                [('tenancy', '=', self.tenancy.id)])
        for i in tanency_recurring_ids:
                recurring_ids.append(i.maint_type.id)
        if self.start_date and self.end_date:
            d1 = datetime.strptime(
                self.start_date, DEFAULT_SERVER_DATE_FORMAT)
            d2 = datetime.strptime(
                self.end_date, DEFAULT_SERVER_DATE_FORMAT)

            diff = abs((d1.year - d2.year) * 12 + (d1.month - d2.month))
            interval = 1
            tot_rec = diff / interval
            tot_rec2 = diff % interval
            if abs(d1.month - d2.month) >= 0 and d1.day < d2.day:
                tot_rec2 += 1
            if diff == 0:
                tot_rec2 = 1
            if tot_rec > 0:
                for rec in range(tot_rec):
                    recurring_maintenance_vals = {
                        'date': d1.strftime(
                                    DEFAULT_SERVER_DATE_FORMAT),
                        'r_maintenance': self.id,
                        'maintenance_type_ids': [(6, 0, recurring_ids)],
                     }
                    recurring_maintenance_line_obj.create(
                        recurring_maintenance_vals)
                    d1 = d1 + relativedelta(months=interval)
            if tot_rec2 > 0:
                recurring_maintenance_vals = {
                    'date':  d1.strftime(
                                DEFAULT_SERVER_DATE_FORMAT),
                    'r_maintenance': self.id,
                    'maintenance_type_ids': [(6, 0, recurring_ids)],
                     }
                recurring_maintenance_line_obj.create(
                    recurring_maintenance_vals)
            self.write({'recuring': True, 'state': 'added'})
        return True


class MaintenanaceCost(models.Model):
    _name = 'maintenance.cost'

    maint_type = fields.Many2one(
        comodel_name='recurring.maintenance.type',
        string='Maintenance Type',
        help='Recurring maintenance type')
    cost = fields.Float(
        string='Maintenance Cost',
        help='recurring maintenance cost')
    tenancy = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Tenancy')

    @api.onchange('maint_type')
    def onchange_property_id(self):
        """
        This Method is used to set maintenance type related fields value,
        on change of property.
        --------------------------------------------------------------------
        @param self: The object pointer
        """
        for data in self:
            if data.maint_type:
                data.cost = data.maint_type.cost or 0.00


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"
    _order = 'ref'

    cost_id = fields.One2many(
        comodel_name='maintenance.cost',
        inverse_name='tenancy',
        string='cost',
        help='it shows all recurring maintenance assigned to this tenancy')

    main_cost = fields.Float(
        string='Maintenance Cost',
        default=0.0,
        store=True,
        compute='_total_cost_maint',
        help="Its shows overall cost of recurring maintenance")

    @api.multi
    @api.depends('cost_id.cost')
    def _total_cost_maint(self):
        """
        This method is used to calculate total maintenance
        boolean field accordingly to current Tenancy.
        -------------------------------------------------------------
        @param self: The object pointer
        """
        total = 0
        for data in self:
            for data_1 in data.cost_id:
                total += data_1.cost
            data.main_cost = total


class TenancyRentSchedule(models.Model):
    _inherit = "tenancy.rent.schedule"
    _rec_name = "tenancy_id"
    _order = 'start_date'

    @api.multi
    def create_invoice(self):
        """
        This Method is used to create invoice
        ---------------------------------------------------------------
        @param self: The object pointer
        """
        res = super(TenancyRentSchedule, self).create_invoice()
        print res
        journal_ids = self.env['account.journal'].search(
            [('type', '=', 'sale'), ('company_id', '=', self.company_id.id)])
        if self.tenancy_id.main_cost:
            inv_line_main = {
                'origin': 'tenancy.rent.schedule',
                'name': 'Maintenance cost',
                'price_unit': self.tenancy_id.main_cost or 0.00,
                'quantity': 1,
                'account_id': self.tenancy_id.property_id.
                income_acc_id.id or False,
                'account_analytic_id': self.tenancy_id.id or False,
            }
            if self.tenancy_id.rent_type_id.renttype == 'Monthly':
                m = self.tenancy_id.main_cost * \
                    float(self.tenancy_id.rent_type_id.name)
                inv_line_main.update({'price_unit': m})
            if self.tenancy_id.rent_type_id.renttype == 'Yearly':
                y = self.tenancy_id.main_cost * \
                    float(self.tenancy_id.rent_type_id.name) * 12
                inv_line_main.update({'price_unit': y})
            inv_line_values = {
                'origin': 'tenancy.rent.schedule',
                'name': 'Tenancy(Rent) Cost',
                'quantity': 1,
                'account_id': self.tenancy_id.property_id.
                income_acc_id.id or False,
                'account_analytic_id': self.tenancy_id.id or False,
                'price_unit': self.amount or 0.00,
            }

            inv_values = {
                'partner_id': self.tenancy_id.tenant_id.parent_id.id or False,
                'type': 'out_invoice',
                'property_id': self.tenancy_id.property_id.id or False,
                'date_invoice': datetime.now().strftime(
                    DEFAULT_SERVER_DATE_FORMAT) or False,
                'schedule_id': self.id,
                'new_tenancy_id': self.tenancy_id.id,
                'journal_id': journal_ids and journal_ids.ids[0] or False,
                'company_id': self.company_id.sudo().id,
                'partner_bank_id': self.company_id.bank_id.sudo().id
            }

            if self.tenancy_id.main_cost:
                inv_values.update(
                                {'invoice_line_ids': [(0, 0, inv_line_values),
                                                      (0, 0, inv_line_main)]})
            else:
                inv_values.update(
                    {'invoice_line_ids': [(0, 0, inv_line_values)]})

            acc_id = self.env['account.invoice'].create(inv_values)
            self.write({'invc_id': acc_id.id, 'inv': True})
            context = dict(self._context or {})
            wiz_form_id = self.env['ir.model.data'].get_object_reference(
                'account', 'invoice_form')[1]
            return {
                'view_type': 'form',
                'view_id': wiz_form_id,
                'view_mode': 'form',
                'res_model': 'account.invoice',
                'res_id': self.invc_id.id,
                'type': 'ir.actions.act_window',
                'target': 'current',
                'context': context,
            }
        return res
