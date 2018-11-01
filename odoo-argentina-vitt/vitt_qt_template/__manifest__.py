# -*- coding: utf-8 -*-
{
    'name': "Nueva impresion de cotizaciones ARG",

    'summary': """Nueva impresion de cotizaciones ARG""",

    'description': """
        Nueva impresion de cotizaciones ARG
    """,

    'author': "Moogah",
    'website': "http://www.Moogah.com",

    'category': 'Uncategorized',
    'version': '10.0.1.0',

    # any module necessary for this one to work correctly
    'depends': [
        'sale',
     ],

    # always loaded
    'data': [
        'views/template.xml',
        'views/layout_templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'application': True,
}