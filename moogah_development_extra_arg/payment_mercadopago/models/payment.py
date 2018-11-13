# coding=utf-8
from odoo import _, api, fields, models
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.exceptions import UserError
from odoo.tools import float_compare
import logging
import mercadopago
from datetime import datetime
import json

from werkzeug import urls, utils
from odoo.http import request
from .mercadopago_request import MecradoPagoPayment


_logger = logging.getLogger(__name__)

class MercadoPagoPaymentMethods(models.Model):
    _name = "mercadopago.payment.methods"

    name = fields.Char(string="Name")
    uni_id = fields.Char(string="Id")
    payment_type = fields.Selection([('credit_card','Credit Card'),
                                     ('debit_card', 'Debit Card'),
                                     ('ticket', 'Ticket'),
                                     ('atm', 'ATM'),
                                     ],string="Payment Type Ids")
    type = fields.Selection([('credit_card','Credit Card'),
                                     ('debit_card', 'Debit Card'),
                                     ('other', 'Others'),
                                     ],string="Type")

class PaymentMercadoPago(models.Model):
    _inherit = 'payment.acquirer'

    global _mercadopago_sandbox_url, _mercadopago_production_url
    _mercadopago_sandbox_url = ""
    _mercadopago_production_url = ""
    # _card_token_dict = {}

    @api.model
    def _get_credit_card_payment(self):
        return self.env['mercadopago.payment.methods'].sudo().search([('type', '=', 'credit_card')]).ids

    @api.model
    def _get_debit_card_payment(self):
        return self.env['mercadopago.payment.methods'].sudo().search([('type', '=', 'debit_card')]).ids

    @api.model
    def _get_other_payment(self):
        return self.env['mercadopago.payment.methods'].sudo().search([('type', '=', 'other')]).ids


    provider = fields.Selection(selection_add=[('mercadopago', 'MercadoPago')])
    mercadopago_client_id = fields.Char(string='Client Id', required_if_provider='mercadopago', groups='base.group_user')
    mercadopago_client_secret = fields.Char(string='Client Secret', required_if_provider='mercadopago', groups='base.group_user')
    mercadopago_use_ipn = fields.Boolean(string='Use IPN', groups='base.group_user')
    mercadopago_ipn_url = fields.Char(string='IPN URL', groups='base.group_user', compute='_get_ipn_url')
    mercadopago_enable_MercadoEnvio = fields.Boolean(string='Enable MercadoEnvio', groups='base.group_user')
    auto_confirm = fields.Selection(selection_add=[('confirm_order_draft_acquirer', 'Authorize & capture the amount, confirm the SO, create	the	payment	and	save the invoice in	draft state on acquirer confirmation'),("confirm_order_confirm_inv","Authorize & capture the amount, confirm the SO and auto-validate the invoice on acquirer confirmation")],
                                    domain=[('provider', '=', 'mercadopago')],)
    available_payment_method = fields.Selection([('all', 'All Available Payment Methods Available'),
                                                 ('custom', 'Customized Available Payment Methods')],
                                                default="all",
                                                string="Available Payment Methods")
    credit_card_payment_methods_ids = fields.Many2many('mercadopago.payment.methods', 'credit_card_mercadopago_payment_rel',  'mercadopago_payment_id', 'credit_card_payment_id', domain=[('type', '=', 'credit_card')], string="Credit Cards", default=_get_credit_card_payment)
    debit_card_payment_methods_ids = fields.Many2many('mercadopago.payment.methods', 'debit_card_mercadopago_payment_rel', 'mercadopago_payment_id', 'debit_card_payment_id', domain=[('type', '=', 'debit_card')], string="Debit Cards", default=_get_debit_card_payment)
    other_payment_methods_ids = fields.Many2many('mercadopago.payment.methods', 'other_mercadopago_payment_rel', 'mercadopago_payment_id', 'other_payment_id', domain=[('type', '=', 'other')], string="Cash/Bank Transfer", default=_get_other_payment)
    mercadopago_test_public_key = fields.Char(string='Test Public Key')
    mercadopago_test_access_token = fields.Char(string="Test Access Token")
    mercadopago_prod_public_key = fields.Char(string="Public Key")

    @api.depends('mercadopago_use_ipn')
    def _get_ipn_url(self):
        for rec in self:
            if rec.mercadopago_use_ipn:
                base_url = self.env['ir.config_parameter'].get_param('web.base.url')
                rec.mercadopago_ipn_url = base_url + '/ipn/notification'
            else:
                rec.mercadopago_ipn_url = False


    def _set_excluded_payment_methods(self, acquirer):
        excluded_type = []
        excluded_method = []
        incl_methods = []
        incl_methods.extend(self.credit_card_payment_methods_ids.ids)
        incl_methods.extend(self.debit_card_payment_methods_ids.ids)
        incl_methods.extend(self.other_payment_methods_ids.ids)
        excl_methods = self.env['mercadopago.payment.methods'].search([('id', 'not in', incl_methods)])
        for method in excl_methods:
            excluded_method.append({'id' : method.uni_id})
        print("----------method------",excluded_method)
        atm = self.other_payment_methods_ids.search([('payment_type', '=', 'atm')])
        ticket = self.other_payment_methods_ids.search([('payment_type', '=', 'ticket')])
        if not self.credit_card_payment_methods_ids:
            excluded_type.append({'id' : 'credit_card'})
        if not self.debit_card_payment_methods_ids:
            excluded_type.append({'id' : 'debit_card'})
        if not atm:
            excluded_type.append({'id' : 'atm'})
        if not ticket:
            excluded_type.append({'id' : 'ticket'})
        print("-------type-------",excluded_type)
        return {'excluded_type' : excluded_type, 'excluded_method' : excluded_method}

    def _get_mercadopago_pref(self, values, order, base_url, excluded_payment_methods):
        # Initializing mercadoPago Payment
        mp = mercadopago.MP(self.mercadopago_client_id, self.mercadopago_client_secret)

        accessToken = mp.get_access_token()
        # print("---------accessToken-----------",accessToken)
        # print("-------values--------",values)
        # print("-------order--------",order)
        if excluded_payment_methods.get('excluded_method'):
            excluded_payment_method = excluded_payment_methods.get('excluded_method')
        else:
            excluded_payment_method = []
        if excluded_payment_methods.get('excluded_type'):
            excluded_payment_type = excluded_payment_methods.get('excluded_type')
        else:
            excluded_payment_type = []
        r_url = '/mercadopago'+values.get('return_url')
        return_url = urls.url_join(base_url, r_url)
        preference_data = {"items": [{'id' : order.name,
                                      'title' : order.name,
                                      'quantity' : 1,
                                      'currency_id' : values.get('currency').name,
                                      'unit_price' : values.get('amount'),
                                      }],
                           "payer" : {'name' : values.get('partner_name'),
                                       'email' : values.get('partner_email'),
                                       'date_created' : order.create_date,
                                       'phone' : {'area_code' : "",
                                                  'number' : values.get('partner_phone')},
                                       'address' : {'zip_code' : values.get('billing_partner_zip'),
                                                    'street_name' : values.get('billing_partner_address'),}
                                       },
                           "back_urls" : {'pending' : return_url,
                                          'success' : return_url,
                                          'failure' : return_url},
                                          'auto_return' : 'approved',
                           "external_reference" : order.name,
                               "payment_methods" : {'excluded_payment_methods' :excluded_payment_method,
                                                    'excluded_payment_types' : excluded_payment_type,
                                                   },
                           }
        preference_result = mp.create_preference(preference_data)
        print("-----preference_result-----", preference_result)
        if preference_result.get('response').get('status') == 400:
            raise UserError(_('There seems to be some problem while creating MercadoPago Preference'))
        request.session['pref_id'] = preference_result.get('response').get("id")

        # 2/0
        return preference_result

    def _get_feature_support(self):
        """Get advanced feature support by provider.

        Each provider should add its technical in the corresponding
        key for the following features:
            * fees: support payment fees computations
            * authorize: support authorizing payment (separates
                         authorization and capture)
            * tokenize: support saving payment data in a payment.tokenize
                        object
        """
        res = super(PaymentMercadoPago, self)._get_feature_support()
        res['authorize'].append('mercadopago')
        res['tokenize'].append('mercadopago')
        return res


    def _get_fu_urls(self, environment):
        """ MercadoPago URLs """
        if environment == 'prod':
            return {'mercadopago_form_url': _mercadopago_production_url}
        else:
            return {'mercadopago_form_url':_mercadopago_sandbox_url}

    @api.multi
    def mercadopago_form_generate_values(self, values):
        self.ensure_one()
        global _mercadopago_sandbox_url, _mercadopago_production_url
        print("--------mercadopago_form_generate_values----------", values)
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        order = request.website.sale_get_order()
        excluded_payment_methods = self._set_excluded_payment_methods(self)
        print("------excluded_payment_methods----",excluded_payment_methods)
        if order:

            mercadopago_pref = self._get_mercadopago_pref(values, order, base_url, excluded_payment_methods)
            _mercadopago_sandbox_url = mercadopago_pref.get('response').get('sandbox_init_point')
            _mercadopago_production_url = mercadopago_pref.get('response').get('init_point')
            print "--------_mercadopago_sandbox_url",_mercadopago_sandbox_url

            temp_mercadopago_tx_values = {'tx_return_url' : mercadopago_pref.get('response').get("back_urls").get('success'),}
            print "temp_mercadopago_tx_values", temp_mercadopago_tx_values
        return temp_mercadopago_tx_values


    @api.model
    def mercadopago_s2s_form_process(self, data):
        # print("----------data---------",data, self)
        # print("----_card_token_dict------",_card_token_dict)
        self = self.env['payment.acquirer'].sudo().search([('provider', '=', 'mercadopago')])
        print ('-------self------',self)
        print("-----data------",data)

        mercado_obj = MecradoPagoPayment(self)
        values = {'cc_number': data.get('cc_number'),
                  'cc_holder_name': data.get('cc_holder_name'),
                  'cc_expiry': data.get('cc_expiry'),
                  'cc_cvc': data.get('cc_cvc'),
                  'cc_brand': data.get('cc_brand'),
                  'acquirer_id': self.id,
                  # 'acquirer_id': int(data.get('acquirer_id')),
                  'partner_id': int(data.get('partner_id')),
                  'docNumber' : data.get('docNumber'),
                  'docType' : data.get('docType'),
                  'customer_email' : data.get('customer_email')}
        # 2/0
        PaymentMethod = self.env['payment.token'].sudo().create(values)
        return PaymentMethod

    @api.multi
    def mercadopago_s2s_form_validate(self, data):
        error = dict()
        # print("--mercadopago_s2s_form_validate-----",data)
        mandatory_fields = ["cc_number", "cc_cvc", "cc_holder_name", "cc_expiry", "cc_brand"]
        # Validation
        for field_name in mandatory_fields:
            if not data.get(field_name):
                error[field_name] = 'missing'
        # if data['cc_expiry'] and datetime.now().strftime('%y%M') > datetime.strptime(data['cc_expiry'],
        #                                                                              '%M / %y').strftime('%y%M'):
        #     return False
        print("------error-----",error)
        return False if error else True

    @api.multi
    def mercadopago_get_form_action_url(self):
        self.ensure_one()
        print "It has been called for getting urls"
        return self._get_fu_urls(self.environment)['mercadopago_form_url']


class PaymentTransactionMercadoPago(models.Model):
    _inherit = "payment.transaction"

    @api.model
    def create(self, vals):
        # The reference is used in the Authorize form to fill a field (invoiceNumber) which is
        # limited to 20 characters. We truncate the reference now, since it will be reused at
        # payment validation to find back the transaction.
        if 'reference' in vals and 'acquirer_id' in vals:
            acquier = self.env['payment.acquirer'].browse(vals['acquirer_id'])
            if acquier.provider == 'mercadopago':
                vals['reference'] = vals.get('reference', '')[:20]
        return super(PaymentTransactionMercadoPago, self).create(vals)

    def _generate_and_pay_invoice(self, tx, acquirer_name):
        tx.sale_order_id._force_lines_to_invoice_policy_order()

        # force company to ensure journals/accounts etc. are correct
        # company_id needed for default_get on account.journal
        # force_company needed for company_dependent fields
        ctx_company = {'company_id': tx.sale_order_id.company_id.id,
                       'force_company': tx.sale_order_id.company_id.id}
        created_invoice = tx.sale_order_id.with_context(**ctx_company).action_invoice_create()
        created_invoice = self.env['account.invoice'].browse(created_invoice).with_context(**ctx_company)

        if created_invoice:
            _logger.info('<%s> transaction completed, auto-generated invoice %s (ID %s) for %s (ID %s)',
                         acquirer_name, created_invoice.name, created_invoice.id, tx.sale_order_id.name, tx.sale_order_id.id)

            created_invoice.action_invoice_open()
            if tx.acquirer_id.journal_id:
                created_invoice.with_context(tx_currency_id=tx.currency_id.id).pay_and_reconcile(tx.acquirer_id.journal_id, pay_amount=created_invoice.amount_total)
                if created_invoice.payment_ids:
                    created_invoice.payment_ids[0].payment_transaction_id = tx
            else:
                _logger.warning('<%s> transaction completed, could not auto-generate payment for %s (ID %s) (no journal set on acquirer)',
                                acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
        else:
            _logger.warning('<%s> transaction completed, could not auto-generate invoice for %s (ID %s)',
                            acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)


    def _confirm_so(self, acquirer_name=False):
        for tx in self:
            if tx.acquirer_id.provider == "mercadopago":
                # print "inside _confirm_so method with record : ", tx
                # check tx state, confirm the potential SO
                if tx.sale_order_id and tx.sale_order_id.state in ['draft', 'sent']:
                    # verify SO/TX match, excluding tx.fees which are currently not included in SO
                    amount_matches = float_compare(tx.amount, tx.sale_order_id.amount_total, 2) == 0
                    if amount_matches:
                        # print "condition is true and going to confirm so"
                        # print "acquirer ref is : ", acquirer_name
                        if not acquirer_name:
                            acquirer_name = tx.acquirer_id.provider or 'unknown'
                        # print "tx.acquirer_id.auto_confirm : ", tx.acquirer_id.provider,tx.acquirer_id.auto_confirm
                        if tx.state == 'authorized' and tx.acquirer_id.auto_confirm == 'authorize':
                            _logger.info('<%s> transaction authorized, auto-confirming order %s (ID %s)', acquirer_name,
                                         tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.with_context(send_email=True).action_confirm()
                        if tx.state == 'done' and tx.acquirer_id.auto_confirm in ['confirm_so',
                                                                                  'generate_and_pay_invoice',
                                                                                  'confirm_order_draft_acquirer',
                                                                                  'confirm_order_confirm_inv']:
                            _logger.info('<%s> transaction completed, auto-confirming order %s (ID %s)', acquirer_name,
                                         tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.with_context(send_email=True).action_confirm()
                            print "tx.sale_order_id : ",tx.sale_order_id.state
                            if tx.acquirer_id.auto_confirm in ['generate_and_pay_invoice','confirm_order_confirm_inv'] :
                                self._generate_and_pay_invoice(tx, acquirer_name)
                        elif tx.state not in ['cancel', 'error'] and tx.sale_order_id.state == 'draft':
                            _logger.info(
                                '<%s> transaction pending/to confirm manually, sending quote email for order %s (ID %s)',
                                acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.force_quotation_send()
                    else:
                        _logger.warning('<%s> transaction AMOUNT MISMATCH for order %s (ID %s): expected %r, got %r',
                            acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id, tx.sale_order_id.amount_total,
                            tx.amount, )
                        tx.sale_order_id.message_post(subject=_("Amount Mismatch (%s)") % acquirer_name, body=_(
                            "The sale order was not confirmed despite response from the acquirer (%s): SO amount is %r but acquirer replied with %r.") % (
                                                                                                                  acquirer_name,
                                                                                                                  tx.sale_order_id.amount_total,
                                                                                                                  tx.amount,))

            else:
                # check tx state, confirm the potential SO
                if tx.sale_order_id and tx.sale_order_id.state in ['draft', 'sent']:
                    # verify SO/TX match, excluding tx.fees which are currently not included in SO
                    amount_matches = float_compare(tx.amount, tx.sale_order_id.amount_total, 2) == 0
                    if amount_matches:
                        if not acquirer_name:
                            acquirer_name = tx.acquirer_id.provider or 'unknown'
                        if tx.state == 'authorized' and tx.acquirer_id.auto_confirm == 'authorize':
                            _logger.info('<%s> transaction authorized, auto-confirming order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.with_context(send_email=True).action_confirm()
                        if tx.state == 'done' and tx.acquirer_id.auto_confirm in ['confirm_so', 'generate_and_pay_invoice']:
                            _logger.info('<%s> transaction completed, auto-confirming order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.with_context(send_email=True).action_confirm()

                            if tx.acquirer_id.auto_confirm == 'generate_and_pay_invoice':
                                self._generate_and_pay_invoice(tx, acquirer_name)
                        elif tx.state not in ['cancel', 'error'] and tx.sale_order_id.state == 'draft':
                            _logger.info('<%s> transaction pending/to confirm manually, sending quote email for order %s (ID %s)', acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id)
                            tx.sale_order_id.force_quotation_send()
                    else:
                        _logger.warning(
                            '<%s> transaction AMOUNT MISMATCH for order %s (ID %s): expected %r, got %r',
                            acquirer_name, tx.sale_order_id.name, tx.sale_order_id.id,
                            tx.sale_order_id.amount_total, tx.amount,
                        )
                        tx.sale_order_id.message_post(
                            subject=_("Amount Mismatch (%s)") % acquirer_name,
                            body=_("The sale order was not confirmed despite response from the acquirer (%s): SO amount is %r but acquirer replied with %r.") % (
                                acquirer_name,
                                tx.sale_order_id.amount_total,
                                tx.amount,
                            )
                        )


    @api.multi
    def mercadopago_s2s_do_transaction(self, **data):
        self.ensure_one()
        print("-------mercadopago_s2s_do_transaction-------",self.payment_token_id.acquirer_ref)
        transaction = MecradoPagoPayment(self.acquirer_id)
        res = transaction.mercadopago_payment(self)
        print("-------res---------",res)
        return self._mercadopago_s2s_validate_tree(res)

    @api.multi
    def _mercadopago_s2s_validate_tree(self, tree):
        print("-------_mercadopago_s2s_validate_tree--------",tree)
        self.ensure_one()
        if self.state not in ('draft', 'pending', 'refunding'):
            _logger.info('MercadoPago: trying to validate an already validated tx (ref %s)', self.reference)
            return True
        status = ""
        collection_id = ""
        status_detail = ""
        if tree and tree.get('collection_status'):
            status = tree.get('collection_status')
            collection_id = tree.get('collection_id')
        if tree and tree.get('status'):
            status = tree.get('status')
            collection_id = tree.get('id')
        # status = tree.get('collection_status')
        if tree and tree.get('status') and tree.get('status_detail'):
            collection_id = tree.get('id')
            status = tree.get('status')
            status_detail = tree.get('status_detail')

        print("---------Status--------",status)
        if status == 'approved':
            print("it has been approved and rest is being done")
            new_state = 'refunded' if self.state == 'refunding' else 'done'
            self.write({'state': new_state,
                        'date_validate': fields.datetime.now(),
                        'acquirer_reference': collection_id, })
            # self.execute_callback()
            # if self.payment_token_id:
            #     self.payment_token_id.verified = True
            return True

        elif status == 'pending':
            self.write({'state' : 'pending',
                        'acquirer_reference': collection_id,})
            # self.execute_callback()
            # if self.payment_token_id:
            #     self.payment_token_id.verified = True

            return True

        elif status == "in_process":
            self.write({'state': 'pending',
                        'acquirer_reference': collection_id, })
            return True

        elif status == "rejected":
            state_message = ""
            status_detail = tree.get('status_detail')
            print("--------status_detail--------",tree.get('status_detail'))
            if status_detail == "cc_rejected_call_for_authorize":
                state_message = "Aww Snap! There seems to be some problem with Payment. Please call authorize person."
            elif status_detail == "cc_rejected_insufficient_amount":
                state_message = "Insufficient Funds."
            elif status_detail == "cc_rejected_bad_filled_security_code":
                state_message = "Security Code entered is incorrect for this Card."
            elif status_detail == "cc_rejected_bad_filled_date":
                state_message = "Card has been Expired, Please provide Valid Card."
            elif status_detail == "cc_rejected_bad_filled_other":
                state_message = "It seems some information in Payment form has been provided incorrectly.\n\t Please check it and try again."
            else:
                state_message = "Aww Snap! We are sorry that your payment has been rejected. Please try again after sometimes."
            self.write({'state': 'cancel', 'acquirer_reference': collection_id,
                'state_message': state_message, })

            # r =  request.redirect("/mercadopago/reject_payment", state_message)
            # response = request.render("payment_mercadopago.reject_payment_template", state_message)
            # print("----------response---------", response)

            return True

        else:
            error = tree['error']['message']
            _logger.warn(error)
            self.sudo().write({'state': 'error', 'state_message': error, 'acquirer_reference': tree.get('id'),
                'date_validate': fields.datetime.now(), })

            return False

    # def confirm_sale_token(self):
    #     """ Confirm a transaction token and call SO confirmation if it is a success.
    #
    #     :return: True if success; error string otherwise """
    #     self.ensure_one()
    #     print("------------inside confirm_sale_token---------",self, self.payment_token_id)
    #     print("------------context inside confirm_sale_token---------",self._context)
    #     if self.payment_token_id and self.partner_id == self.sale_order_id.partner_id:
    #         if self._context and self._context.get('cc_cvc'):
    #             print("----payment token inside confirm_sale_token------", self.payment_token_id, self.payment_token_id.mercadopago_profile)
    #             acquirer = self.payment_token_id.acquirer_id
    #             cc_details = str(self.payment_token_id.mercadopago_profile).split(':')
    #             values = {'cc_number' : cc_details[0] if cc_details[0] else "",
    #                       'cc_expiry' : cc_details[1] if cc_details[1] else "",
    #                       'cc_holder_name' : cc_details[2] if cc_details[2] else "",
    #                       'docNumber' : cc_details[3] if cc_details[3] else "",
    #                       'docType' : cc_details[4] if cc_details[4] else "",
    #                       'cc_cvc' : self._context.get('cc_cvc'),
    #                       'acquirer_id' : acquirer.id,
    #                       'partner_id' : self.payment_token_id.partner_id.id,
    #                       'customer_email' : cc_details[5] if cc_details[5] else ""}
    #             mercado_obj = MecradoPagoPayment(acquirer)
    #             card_token = mercado_obj._get_card_token(acquirer, values)
    #             if card_token and card_token.get('id'):
    #                 token = self.payment_token_id
    #                 token.write({'acquirer_ref' : card_token.get('id')})
    #
    #         try:
    #             s2s_result = self.s2s_do_transaction()
    #             print("--------s2s_result-------",s2s_result)
    #         except Exception as e:
    #             _logger.warning(
    #                 _("<%s> transaction (%s) failed: <%s>") %
    #                 (self.acquirer_id.provider, self.id, str(e)))
    #             return 'pay_sale_tx_fail'
    #
    #         valid_state = 'authorized' if self.acquirer_id.capture_manually else 'done'
    #         print("------valid_state------",valid_state, self.state)
    #         if not s2s_result or self.state != valid_state:
    #             _logger.warning(
    #                 _("<%s> transaction (%s) invalid state: %s") %
    #                 (self.acquirer_id.provider, self.id, self.state_message))
    #             request.session['state_message'] = self.state_message
    #             return 'pay_sale_tx_state'
    #
    #         try:
    #             return self._confirm_so()
    #         except Exception as e:
    #             _logger.warning(
    #                 _("<%s> transaction (%s) order confirmation failed: <%s>") %
    #                 (self.acquirer_id.provider, self.id, str(e)))
    #             return 'pay_sale_tx_confirm'
    #     return 'pay_sale_tx_token'


    @api.model
    def _mercadopago_form_get_tx_from_data(self, data):
        print("----------data-----------",data)
        reference = data.get('sale_transaction_id')
        if not reference:
            error_msg = _(
                'MercadoPago: invalid reply received from provider, missing reference. Additional message: %s' % data.get(
                    'error', {}).get('message', ''))
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        tx = self.search([('id', '=', reference)])
        if not tx:
            error_msg = (_('MercadoPago: no order found for reference %s') % reference)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        elif len(tx) > 1:
            error_msg = (_('MercadoPago: %s orders found for reference %s') % (len(tx), reference))
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx[0]

    @api.multi
    def _mercadopago_form_validate(self, data):
        # res = self._mercadopago_s2s_validate_tree(data)
        # return res
        print "--------_mercadopago_form_validate-------",data
        if self.state == 'done':
            _logger.warning('MercadoPago: trying to validate an already validated tx (ref %s)' % self.reference)
            return True
        return self._mercadopago_s2s_validate_tree(data)


class MercadoPagoPaymentToken(models.Model):
    _inherit = "payment.token"

    mercadopago_profile = fields.Char(string='MercadoPago Profile ID', help='This contains the unique reference '
                                                                            'for this partner/payment token combination in the Authorize.net backend')
    provider = fields.Selection(string='Provider', related='acquirer_id.provider')
    save_token = fields.Selection(string='Save Cards', related='acquirer_id.save_token')

    @api.model
    def mercadopago_create(self, values):
        print("-----values-from mercadopago_create------- ",values)
        if values.get('cc_number'):
            values['cc_number'] = values['cc_number'].replace(' ', '')
            acquirer = self.env['payment.acquirer'].browse(values['acquirer_id'])
            expiry = str(values['cc_expiry'][:2]) + str(values['cc_expiry'][-2:])
            partner = self.env['res.partner'].browse(values['partner_id'])
            mercado_obj = MecradoPagoPayment(acquirer)
            mercadopago_profile_id = ""
            if acquirer.save_token:
                print("-------values----",values)
                # 2/0
                pass
            card_token = mercado_obj._get_card_token(acquirer, values)
            print("----card_token----", card_token)

            # if partner.mercadopago_customer:
            #     print("There it exists as : ",partner.mercadopago_customer)
            #     mercadopago_profile_id = partner.mercadopago_customer
            # else:
            #     new_customer = mercado_obj._create_mercadopago_customer(partner, acquirer)
            #     if new_customer:
            #         partner.sudo().write({
            #             'mercadopago_customer': new_customer.get('id'),
            #         })
            #         if new_customer.get('id'):
            #             mercadopago_profile_id = new_customer.get('id')
            #     # print("---else mercadopago_customer-------",partner.mercadopago_customer)
            # print("--mercadopago_profile_id----",mercadopago_profile_id)
            # print("--mercadopago_profile_id----",card_token)
            # print("--mercadopago_profile_id----",card_token.get("id"))
            # if mercadopago_profile_id and card_token.get('id'):
            #     if acquirer.save_token == 'always':
            #         customer_card = mercado_obj._set_customer_card(mercadopago_profile_id, acquirer, card_token)
            # 2/0
            doctype = ""
            if not values['docType']:
                doctype = "Otro"
            else:
                doctype = values['docType']

            card_info = values['cc_number'] + ":" + values["cc_expiry"] + ":" + values['cc_holder_name'] + ":" + values['docNumber'] + ":" + doctype + ":" + values['customer_email'] + ":" + values['cc_brand']
            if card_token and card_token.get("id"):
                print("Inside if----------------")
                return {'mercadopago_profile' : card_info,
                        'name': 'XXXXXXXXXXXX%s - %s' % (values['cc_number'][-4:], values['cc_holder_name']),
                        'acquirer_ref': card_token.get("id"),
                        }
            else:
                raise ValidationError(_('The Customer Profile creation in MercadoPago failed.'))

        else:
            return values

        #     transaction = AuthorizeAPI(acquirer)
        #     res = transaction.create_customer_profile(partner, values['cc_number'], expiry, values['cc_cvc'])
        #     if res.get('profile_id') and res.get('payment_profile_id'):
        #         return {'authorize_profile': res.get('profile_id'),
        #             'name': 'XXXXXXXXXXXX%s - %s' % (values['cc_number'][-4:], values['cc_holder_name']),
        #             'acquirer_ref': res.get('payment_profile_id'), }
        #     else:
        #         raise ValidationError(_('The Customer Profile creation in Authorize.NET failed.'))
        # else:
        #     return values



