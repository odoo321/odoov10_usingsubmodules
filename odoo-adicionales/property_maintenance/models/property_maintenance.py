# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api, _
from odoo.exceptions import Warning
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import re


class MaintenanceRequest(models.Model):
    _inherit = 'maintenance.request'
    # _order = 'invc_id asc'

    renters_fault = fields.Boolean(
        string='Renters Fault',
        default=False,
        copy=True,
        help='If this maintenance are fault by tenant than its true')
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property',
        help='Property name for need to maintenance')
    done = fields.Boolean(
        string='Stage Done',
        default=False)
    cost = fields.Float(
        string='Cost',
        help='Cost for over all maintenance')
    invc_id = fields.Many2one(
        comodel_name='account.invoice',
        string='Invoice')
    date_invoice = fields.Date(
        related="invc_id.date_invoice",
        store=True,
        string='Invoice Date')
    invc_check = fields.Boolean(
        string='Already Created',
        default=False)
    city = fields.Char(
        string='City',
        help='Enter the City')
    street = fields.Char(
        related='property_id.street',
        string='Street',
        help='Property street name')
    street2 = fields.Char(
        related='property_id.street2',
        string='Street2',
        help='Property street2 name')
    township = fields.Char(
        related='property_id.township',
        string='Township',
        help='Property Township name')
    zip = fields.Char(
        related='property_id.zip',
        string='Zip',
        size=24,
        change_default=True,
        help='Property zip code')
    state_id = fields.Many2one(
        related='property_id.state_id',
        comodel_name='res.country.state',
        string='State',
        ondelete='restrict',
        help='Property state name')
    country_id = fields.Many2one(
        comodel_name='res.country',
        string='Country',
        ondelete='restrict',
        help='Property country name',
        default=lambda self: self.env['res.country'].search(
            [('code', '=', 'OM')]))
    request_from = fields.Selection(
        [('telephone', 'Telephone'),
         ('email', 'Email'),
         ('office', 'Office'),
         ('other', 'Other')],
        string='Request From',
        help='Which medium maintenance requested')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        help='Company Name',
        default=lambda self: self.env['res.company']._company_default_get(
            'maintenance.request'))
    active = fields.Boolean(
        string='Active',
        default=True)
    equipment = fields.Boolean(
        string='If Add Other Equipment?',
        help='If you used(ADD) any products in maintenance.')
    add_equipment_id = fields.One2many(
        comodel_name='add.equipment',
        inverse_name='maintenance_id',
        string='Added Equipment',
        help='Add equipment name and cost which you add in during maintenance')
    tenant_id = fields.Many2one(
        comodel_name='tenant.partner',
        string='Tenant')
    phone = fields.Char(
        related='tenant_id.phone',
        string='Phone')
    mobile = fields.Char(
        related='tenant_id.mobile',
        string='Mobile')
    email = fields.Char(
        related='tenant_id.email',
        string='E-mail')
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Maintenance Account')
    payment_id = fields.Many2one(
        comodel_name='account.payment',
        string='Paymanet')

    @api.model
    def create(self, vals):
        # context: no_log, because subtype already handle this
        self = self.with_context(mail_create_nolog=True)
        if vals.get('property_id'):
            tenant_id = self.env['account.analytic.account'].search(
                 [('property_id', '=', vals.get('property_id')),
                 ('is_property', '=', True),
                 ('state', '!=', 'close'),
                 ('state', '!=', 'cancelled')]).tenant_id
            if tenant_id:
                vals.update({'tenant_id': tenant_id.id})
        request = super(MaintenanceRequest, self).create(vals)
        if request.owner_user_id:
            request.message_subscribe_users(
                user_ids=[request.owner_user_id.id])
        if request.technician_user_id:
            request.message_subscribe_users(
                user_ids=[request.technician_user_id.id])
        if request.maintenance_team_id and \
                request.maintenance_team_id.partner_id.user_id:
            request.message_subscribe_users(
                user_ids=[request.maintenance_team_id.partner_id.user_id.id])
        if request.equipment_id and not request.maintenance_team_id:
            request.maintenance_team_id = request.equipment_id. \
                maintenance_team_id
        if request.maintenance_team_id:
            for line in request.maintenance_team_id.member_ids:
                if line.user_id:
                    request.message_subscribe_users(user_ids=[line.user_id.id])
        return request

    @api.multi
    @api.onchange('property_id')
    def state_details_change(self):
        for line in self:
            if line.property_id:
                line.tenant_id = self.env['account.analytic.account'].search(
                    [('property_id', '=', line.property_id.id),
                     ('is_property', '=', True),
                     ('state', '!=', 'close'),
                     ('state', '!=', 'cancelled')]).tenant_id

    @api.multi
    def write(self, vals):
        res = super(MaintenanceRequest, self).write(vals)
        if self.stage_id.done and 'stage_id' in vals:
            self.write({'done': True})
        return res

    @api.multi
    def create_invoice(self):
        """
        This Method is used to create invoice from maintenance record.
        --------------------------------------------------------------
        @param self: The object pointer
        """
        inv_line_values = []
        for data in self:
            if not data.property_id.id:
                raise Warning(_("Please Select Property"))
            tncy_ids = self.env['account.analytic.account'].search(
                [('property_id', '=', data.property_id.id), (
                    'state', '!=', 'close')])
            if len(tncy_ids.ids) == 0:
                inv_line_values.append((0, 0, {
                        'name': 'Maintenance For ' + data.name or "",
                        'origin': 'maintenance.request',
                        'quantity': 1,
                        'account_id': data.account_id.id or
                        False,
                        'price_unit': data.cost or 0.00,
                    }))
                inv_values = {
                        'origin': 'maintenance.request' or "",
                        'type': 'out_invoice',
                        'partner_id':
                            data.property_id.company_id.partner_id.id or
                            False,
                        'property_id': data.property_id.id,
                        'invoice_line_ids': inv_line_values,
                        'amount_total': data.cost or 0.0,
                        'date_invoice': datetime.now().strftime(
                            DEFAULT_SERVER_DATE_FORMAT) or False,
                    }
                if self.equipment:
                    for e in self.add_equipment_id:
                        inv_line_values.append((0, 0, {
                            'product_id': e.name.id or "",
                            'name': e.name.name or "",
                            'origin': ' ',
                            'quantity': e.quantity,
                            'account_id':
                                data.account_id.id or False,
                            'uom_id': e.uom_id.id,
                            'price_unit': e.cost or 0.00,
                        }))
                        inv_values.update({
                            'invoice_line_ids': inv_line_values
                        })
                acc_id = self.env['account.invoice'].create(inv_values)
                data.write({
                    'invc_check': True,
                    'invc_id': acc_id.id,
                })
            else:
                inv_line_values.append((0, 0, {
                        'name': 'Maintenance For ' + data.name or "",
                        'origin': 'maintenance.request',
                        'quantity': 1,
                        'account_id': data.account_id.id or
                        False,
                        'price_unit': data.cost or 0.00,
                    }))
                for tenancy_data in tncy_ids:
                    inv_values = {
                        'origin': 'maintenance.request' or "",
                        'type': 'out_invoice',
                        'property_id': data.property_id.id,
                        'invoice_line_ids': inv_line_values,
                        'amount_total': data.cost or 0.0,
                        'date_invoice': datetime.now().strftime(
                            DEFAULT_SERVER_DATE_FORMAT) or False,
                        'number': tenancy_data.name or '',
                    }
                if self.equipment:
                    for eq in self.add_equipment_id:
                        inv_line_values.append((0, 0, {
                            'product_id': eq.name.id or "",
                            'name': eq.name.name or "",
                            'origin': ' ',
                            'quantity': eq.quantity,
                            'account_id':
                                data.account_id.id or False,
                            'uom_id': eq.uom_id.id,
                            'price_unit': eq.cost or 0.00,
                        }))
                        inv_values.update({
                            'invoice_line_ids': inv_line_values
                        })
                if data.renters_fault:
                    inv_values.update(
                        {'partner_id': tenancy_data.tenant_id.parent_id.id or
                         False})
                else:
                    inv_values.update(
                        {'partner_id':
                            tenancy_data.property_id.property_manager.id or
                            False})

                acc_id = self.env['account.invoice'].create(inv_values)
                data.write({
                    'invc_check': True,
                    'invc_id': acc_id.id,
                })

    @api.multi
    def open_invoice(self):
        """
        This Method is used to Open invoice from maintenance record.
        ------------------------------------------------------------
        @param self: The object pointer
        """
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

    @api.multi
    def open_google_map(self):
        """
        This Button method is used to open a URL
        according fields values.
        @param self: The object pointer
        """
        if self.property_id:
            for line in self.property_id:
                url = "http://maps.google.com/maps?oi=map&q="
                if line.name:
                    street_s = re.sub(r'[^\w]', ' ', line.name)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.street:
                    street_s = re.sub(r'[^\w]', ' ', line.street)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.street2:
                    street_s = re.sub(r'[^\w]', ' ', line.street2)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.township:
                    street_s = re.sub(r'[^\w]', ' ', line.township)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.city:
                    street_s = re.sub(r'[^\w]', ' ', line.city)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.state_id:
                    street_s = re.sub(r'[^\w]', ' ', line.state_id.name)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.country_id:
                    street_s = re.sub(r'[^\w]', ' ', line.country_id.name)
                    street_s = re.sub(' +', '+', street_s)
                    url += street_s + '+'
                if line.zip:
                    url += line.zip
                return {
                    'name': 'Go to website',
                    'res_model': 'ir.actions.act_url',
                    'type': 'ir.actions.act_url',
                    'target': 'current',
                    'url': url
                }


# class EquipmentProduct(models.Model):
#     _name = 'equipment.product'

#     name = fields.Char(
#         string='Equipment Name',
#         help='Equipment Name')


class AddEquipment(models.Model):
    _name = 'add.equipment'

    @api.multi
    @api.depends('cost', 'quantity')
    def _price_subtotal(self):
        for rec in self:
            if rec.cost and rec.quantity:
                rec.price_subtotal = rec.cost * rec.quantity
    
    name = fields.Many2one(
        comodel_name='product.product',
        string='Equipment Name',
        help='Equipment Name')
    cost = fields.Float(
        string='Unit Price',
        help='Cost of equipment name')
    quantity = fields.Float(
        string="Quantity",
        help='Number of equipment quantity used')
    price_subtotal = fields.Float(
        string='Subtotal',
        compute='_price_subtotal',
        readonly=True,
        store=True)
    maintenance_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='Maintenance')
    uom_id = fields.Many2one(
        comodel_name='product.uom',
        related='name.uom_id',
        store=True,
        string='Unit Of Measure.')



    @api.onchange('name')
    def _onchange_field_name(self):
        for data in self:
            if data.name:
                data.cost = data.name.lst_price or 0.0


            

class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'
    _description = 'Maintenance Teams'

    name = fields.Many2one(
        comodel_name='hr.department',
        string='Category Name',
        help='Choose Category name')

    member_ids = fields.Many2many(
        comodel_name='hr.employee',
        relation='hr_employee_maintenance_team_rel',
        column1='maintenance_team_id',
        column2='hr_employee_id',
        string='Team Members',
        help='List of employee related to selected category')
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Manager',
        help='Select manager for particular category')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        help='Company Name',
        default=lambda self: self.env['res.company']._company_default_get(
            'maintenance.team'))

    @api.multi
    @api.onchange('name')
    def onchange_partnerid(self):
        """
        Automatic address only if there is one address; otherwise, it
        must be selected
        """
        hr_emp = self.env['hr.employee']
        if self.name:
            self.member_ids = [(6, 0, [rec.id for rec in hr_emp.search(
                [('department_id', '=', self.name.id)])])]
            self.employee_id = self.name.manager_id and \
                self.name.manager_id.id or False

    @api.model
    def create(self, vals):
        res = super(MaintenanceTeam, self).create(vals)
        if not res.member_ids and vals.get('member_ids'):
            line = [rec[1] for rec in vals.get('member_ids') if rec[1]]
            res.member_ids = [(6, 0, line)]
        return res

    @api.multi
    def write(self, vals):
        res = super(MaintenanceTeam, self).write(vals)
        if res:
            for rec in self:
                if not rec.member_ids and vals.get('member_ids'):
                    line = [mbr[1] for mbr in vals.get('member_ids') if mbr[1]]
                    for usr in line:
                        self._cr.execute(
                            "insert into hr_employee_maintenance_team_rel \
                            (maintenance_team_id,hr_employee_id) \
                         values(%s,%s)", (rec.id, usr))
        return res
