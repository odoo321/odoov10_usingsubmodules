# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details

from odoo import models, fields, api
from email.utils import formataddr
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class InvoiceToOwner(models.TransientModel):
    _name = 'invoice.to.owner'

    end_date = fields.Date(
        string='End Date',
        help='End date')
    start_date = fields.Date(
        string='Beginning Date',
        help='End date')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        help='Company name')

    @api.constrains('start_date', 'end_date')
    def check_date_overlap(self):
        """
        This is a constraint method used to check the from date smaller than
        the Expiration date.
        @param self : object pointer
        """
        for ver in self:
            if ver.start_date and ver.end_date:
                dt_from = datetime.strptime(
                    ver.start_date, DEFAULT_SERVER_DATE_FORMAT)
                dt_to = datetime.strptime(
                    ver.end_date, DEFAULT_SERVER_DATE_FORMAT)
                if dt_to < dt_from:
                    raise ValidationError(
                        'End date should be greater than Start date.')

    @api.multi
    def print_yes(self):
        if self._context is None:
            self._context = {}
        datas = {
            'ids': self.ids,
            'model': 'invoice.to.owner',
            'form': self.read(['start_date', 'end_date', 'company_id'])[0]
        }
        return self.env['report'].get_action(
            self, 'property_maintenance.invoice_to_owner_report_template',
            data=datas)

    @api.multi
    def action_invoice_sent(self):
        """
        Open a window to compose an email, with the edi invoice template
        message loaded by default
        """
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            template_id = ir_model_data.get_object_reference(
                'property_maintenance', 'email_template_invoice_id')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference(
                'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        datas = {
            'ids': self.ids,
            'model': 'invoice.to.owner',
            'form': self.read(['start_date', 'end_date', 'company_id'])[0]
        }
        ctx = dict()
        ctx.update({
            'default_model': 'invoice.to.owner',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'data': datas
        })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
            'data': datas
        }

    @api.model
    def message_get_reply_to(self, res_ids, default=None):
        model_name = self.env.context.get('thread_model') or self._name
        alias_domain = self.env['ir.config_parameter'].get_param(
            "mail.catchall.domain")
        res = dict.fromkeys(res_ids, False)
        aliases = {}
        doc_names = {}
        if alias_domain:
            if model_name and model_name != 'mail.thread' and res_ids:
                mail_aliases = self.env['mail.alias'].sudo().search([
                    ('alias_parent_model_id.model', '=', model_name),
                    ('alias_parent_thread_id', 'in', res_ids),
                    ('alias_name', '!=', False)])
                for alias in mail_aliases:
                    if alias.alias_parent_thread_id not in aliases:
                        aliases[alias.alias_parent_thread_id] = '%s@%s' % (
                            alias.alias_name, alias_domain)
                doc_names.update(
                    dict((ng_res[0], ng_res[1])
                         for ng_res in self.env[model_name].sudo().browse(
                             aliases.keys()).name_get()))
            left_ids = set(res_ids).difference(set(aliases.keys()))
            if left_ids:
                catchall_alias = self.env[
                    'ir.config_parameter'].get_param("mail.catchall.alias")
                if catchall_alias:
                    aliases.update(
                        dict((res_id, '%s@%s' % (
                            catchall_alias, alias_domain)) for res_id in
                            left_ids))
            company_name = self.env.user.company_id.name
            for res_id in aliases.keys():
                email_name = '%s%s' % (company_name, doc_names.get(
                    res_id) and (' ' + doc_names[res_id]) or '')
                email_addr = aliases[res_id]
                res[res_id] = formataddr((email_name, email_addr))
        left_ids = set(res_ids).difference(set(aliases.keys()))
        if left_ids:
            res.update(dict((res_id, default) for res_id in res_ids))
        return res
