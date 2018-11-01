# -*- coding: utf-8 -*-
{
    'name': 'Configuracion en Provincias para Percepciones y Retenciones',
    'summary': 'Configuracion en Provincias para Percepciones y Retenciones',
    'description': """Configuracion en Provincias para Percepciones y Retenciones""",
    'version': '10.0.1.0',
    'author': 'Moogah',
    'website': 'http://www.moogah.com',
    'depends': [
        'l10n_ar_account_withholding',
        'vitt_sales_reports',
    ],
    'data': [
        'views/res_config.xml',
        'views/res_country_state.xml',
    ],
    'installable': True,
}
