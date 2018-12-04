# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo.exceptions import except_orm
from odoo import models, fields, api, _
from odoo import SUPERUSER_ID


class CrmLead(models.Model):
    _inherit = "crm.lead"

    facing = fields.Char(
        string='Facing')
    demand = fields.Boolean(
        string='Is Demand')
    max_price = fields.Float(
        string='Max Price')
    min_price = fields.Float(
        string='Min. Price')
    is_buy = fields.Boolean(
        string='Is Buy',
        default=False)
    is_rent = fields.Boolean(
        string='Is Rent',
        default=False)
    max_bedroom = fields.Integer(
        string='Max Bedroom Require')
    min_bedroom = fields.Integer(
        string='Min. Bedroom Require')
    max_bathroom = fields.Integer(
        string='Max Bathroom Require')
    min_bathroom = fields.Integer(
        string='Min. Bathroom Require')
    furnished = fields.Char(
        string='Furnishing',
        help='Furnishing')
    type_id = fields.Many2one(
        comodel_name='property.type',
        string='Property Type',
        help='Property Type')
    email_send = fields.Boolean(
        string='Email Send',
        help="it is checked when email is send")
    property_id = fields.Many2one(
        comodel_name='account.asset.asset',
        string='Property')

    @api.model
    def cron_property_demand(self):
        """
        This is scheduler function which send mails to customers,
        who are demanded properties.
        @param self: The object pointer
        """
        lead_ids = self.search([('demand', '=', True)])
        property_obj = self.env['account.asset.asset']
        template_id = self.env['ir.model.data'].get_object_reference(
            'property_management', 'email_template_demand_property')[1]
        if lead_ids and lead_ids.ids:
            for lead_rec in lead_ids:
                req_args = [('bedroom', '<=', lead_rec.max_bedroom),
                            ('bedroom', '>=', lead_rec.min_bedroom),
                            ('bathroom', '<=', lead_rec.max_bathroom),
                            ('bathroom', '>=', lead_rec.min_bathroom),
                            ('sale_price', '<=', lead_rec.max_price),
                            ('sale_price', '>=', lead_rec.min_price),
                            ('type_id', '=', lead_rec.type_id.id)]
                if lead_rec.furnished == "all" and lead_rec.facing == "all":
                    required_prop = property_obj.search(req_args)
                elif lead_rec.furnished == "all":
                    req_args += [('facing', '=', lead_rec.facing)]
                    required_prop = property_obj.search(req_args)
                elif lead_rec.facing == "all":
                    req_args += [('furnished', '=', lead_rec.furnished)]
                    required_prop = property_obj.search(req_args)
                else:
                    req_args += [('furnished', '=', lead_rec.furnished),
                                 ('facing', '=', lead_rec.facing)]
                    required_prop = property_obj.search(req_args)
                if template_id and required_prop.ids and \
                        lead_rec.user_id.login and \
                        lead_rec.email_send is False:
                    self.env['mail.template'].send_mail(
                        template_id, lead_rec.id, force_send=True)
                    lead_rec.write({'email_send': True})
        return True

    @api.model
    def _lead_create_contact(self, lead, is_company, parent_id=False):
        """
        This method is used to create customer when lead convert to
        opportunity.
        @param self: The object pointer
        @param lead: The current user’s ID for security checks,
        @param name: Contact name from current Lead,
        @param is_company: Boolean field, checked if company's lead,
        @param parent_id: Linked partner from current Lead,
        @return: Newly created Partner id,
        """
        vals = {
            # 'name': name,
            'name': lead.contact_name,
            'user_id': lead.user_id.id,
            'comment': lead.description,
            'team_id': lead.team_id.id or False,
            'parent_id': parent_id,
            'phone': lead.phone,
            'mobile': lead.mobile,
            'email': lead.email_from,
            'fax': lead.fax,
            'title': lead.title and lead.title.id or False,
            'function': lead.function,
            'street': lead.street,
            'street2': lead.street2,
            'zip': lead.zip,
            'city': lead.city,
            'country_id': lead.country_id and lead.country_id.id or False,
            'state_id': lead.state_id and lead.state_id.id or False,
            'is_company': is_company,
            'type': 'contact',
        }
        if not lead.email_from:
            raise except_orm(
                _('Warning!'), _(' Contact Name or Email is Missing'))

        company_id = self.env['res.users'].browse(SUPERUSER_ID).company_id.id
        paypal_ids = self.env['payment.acquirer'].search(
            [('name', 'ilike', 'paypal'),
             ('company_id', '=', company_id), ], limit=1)
        if paypal_ids:
            if not lead.country_id:
                raise except_orm(_('Warning!'), _(' Please select country'))
        if lead.is_rent:
            vals.update({'tenant': True})
            tenant_id = self.env['tenant.partner'].create(vals)
            tenant_id.parent_id.write({'tenant': True})
            return tenant_id.parent_id.id
        else:
            return self.env['res.partner'].create(vals).id

    @api.multi
    def action_set_lost(self):
        """ Lost semantic: probability = 0, active = False """
        res = super(CrmLead, self).action_set_lost()
        for data in self:
            if data.property_id:
                tenancy_data = self.env['account.analytic.account'].search([
                                     ('property_id', '=', data.property_id.id),
                                     ('name', '=', data.name),
                                     ('state', '=', 'draft')
                        ])
                for tenancy in tenancy_data:
                    tenancy.write({'active': False})
                data.property_id.write({'state': 'draft'})
        return res


class CrmMakeContract(models.TransientModel):
    """ Make contract  order for crm """
    _name = "crm.make.contract"
    _description = "Make sales"

    @api.model
    def _selectPartner(self):
        """
        This function gets default value for partner_id field.
        @param self: The object pointer
        @return: default value of partner_id field.
        """
        if self._context is None:
            self._context = {}
        active_id = self._context and self._context.get(
            'active_id', False) or False
        if not active_id:
            return False
        lead_brw = self.env['crm.lead'].browse(active_id)
        lead = lead_brw.read(['partner_id'])[0]
        return lead['partner_id'][0] if lead['partner_id'] else False

    date = fields.Date(
        string='End Date')
    date_start = fields.Date(
        string='Start Date',
        default=fields.Date.context_today)
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        default=_selectPartner,
        required=True,
        domain=[('customer', '=', True)])
    close = fields.Boolean(
        string='Mark Won',
        default=False,
        help='Check this to close the opportunity after having created the \
        sales order.')

    @api.multi
    def makecontract(self):
        """
        This function create Quotation on given case.
        @param self: The object pointer
        @return: Dictionary value of created sales order.
        """
        context = dict(self._context or {})
        context.pop('default_state', False)
        data = context and context.get('active_ids', []) or []
        for make in self:
            partner = make.partner_id
            new_ids = []
            for case in self.env['crm.lead'].browse(data):
                if not partner and case.partner_id:
                    partner = case.partner_id
                if not case.property_id.id:
                    raise except_orm(('Warning!'), _("There is no property\
                     chosen to create contract"))
                vals = {
                    'name': case.name,
                    'partner_id': partner.id,
                    'property_id': case.property_id.id or False,
                    'tenant_id': self.env['res.users'].search([
                        ('partner_id', '=', case.partner_id.id)]).tenant_id.id,
                    'company_id': partner.company_id.id,
                    'date_start': make.date_start or False,
                    'date': make.date or False,
                    'type': 'contract',
                    'is_property': True,
                    'rent': case.property_id.ground_rent,
                }
                new_id = self.env['account.analytic.account'].create(vals)
                case.write({'ref': 'account.analytic.account,%s' % new_id})
                new_ids.append(new_id.id)
                message = _(
                    "Opportunity has been <b>converted</b> to \
                    the Contract <em>%s</em>.") % (new_id.name)
                case.message_post(body=message)
            if make.close:
                case.action_set_won()
            if not new_ids:
                return {'type': 'ir.actions.act_window_close'}
            value = {
                'domain': str([('id', 'in', new_ids)]),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'account.analytic.account',
                # 'view_id': False,
                'view_id': self.env.ref(
                    'property_management.property_analytic_view_form').id,
                'type': 'ir.actions.act_window',
                'name': _('Contract'),
                'res_id': new_ids
            }
            if len(new_ids) <= 1:
                value.update(
                    {'view_mode': 'form', 'res_id': new_ids and new_ids[0]})
            return value
