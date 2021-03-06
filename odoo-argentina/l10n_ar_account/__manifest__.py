# -*- coding: utf-8 -*-
{
    "name": "Módulo base de Contabilidad Argentina",
    'version': '10.0.1.0.3',
    'category': 'Localization/Argentina',
    'sequence': 14,
    'author': 'Moogah,ADHOC SA,Moldeo Interactive',
    'license': 'AGPL-3',
    'summary': '',
    'depends': [
        'account_document',
        'l10n_ar_partner',
        'sale'
        # no es una dependencia en si (salvo para datos demo) pero si es
        # necesario por como implemenamos la localizacion
        # 'account_invoice_tax_wizard',
    ],
    'external_dependencies': {
    },
    'data': [
        'data/base_validator_data.xml',
        'data/account_document_letter.xml',
        'data/afip_responsability_type.xml',
        'data/account.document.type.csv',
        'data/afip_incoterm.xml',
        'data/res_country_afip_code.xml',
        'data/res_country_cuit.xml',
        'data/product_uom.xml',
        'data/res_currency.xml',
        'data/account_tax_group.xml',
        'data/res_country_group_data.xml',
        'data/account.document.letter.csv',
        'data/recbook_seq_data.xml',
        'data/recbook_records_data.xml',
        # TODO analizar y migrar
        # data_account_type
        # 'data/account_financial_report_data.xml',
        # 'data/account_payment_term.xml',
        'wizard/account_invoice_refund_view.xml',
        'view/res_partner_view.xml',
        'view/res_company_view.xml',
        'view/afip_menuitem.xml',
        'view/afip_incoterm_view.xml',
        'view/res_country_view.xml',
        'view/res_currency_view.xml',
        'view/account_fiscal_position_view.xml',
        'view/product_uom_view.xml',
        'view/account_journal_view.xml',
        'view/account_invoice_view.xml',
        'view/afip_responsability_type_view.xml',
        'view/account_document_letter_view.xml',
        'view/account_document_type_view.xml',
        'res_config_view.xml',
        # TODO migrar
        # 'report/invoice_analysis.xml',
        'security/ir.model.access.csv',
    ],
    'test': [
    ],
    'images': [
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'post_init_hook': 'post_init_hook',
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
