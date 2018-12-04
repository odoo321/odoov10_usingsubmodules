# -*- coding: utf-8 -*-
###############################################################################
#
#   OpenERP, Open Source Management Solution
#   Copyright (C) 2011-Today Serpent Consulting Services PVT LTD
#    (<http://www.serpentcs.com>)
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import models, fields, api, _, osv
import xlsxwriter
from odoo.exceptions import Warning
from datetime import timedelta, datetime
import babel
import calendar
import json
import StringIO
from odoo.tools import config, posix_to_ldml


class AccountReportContextCommon(models.TransientModel):
    _inherit = "account.report.context.common"

    def get_pdf(self):
        # As the assets are generated during the same transaction as the rendering of the
        # templates calling them, there is a scenario where the assets are unreachable: when
        # you make a request to read the assets while the transaction creating them is not done.
        # Indeed, when you make an asset request, the controller has to read the `ir.attachment`
        # table.
        # This scenario happens when you want to print a PDF report for the first time, as the
        # assets are not in cache and must be generated. To workaround this issue, we manually
        # commit the writes in the `ir.attachment` table. It is done thanks to
        # a key in the context.
        if not config['test_enable']:
            self = self.with_context(commit_assetsbundle=True)

        report_obj = self.get_report_obj()
        lines = report_obj.with_context(print_mode=True).get_lines(self)
        footnotes = self.get_footnotes_from_lines(lines)
        base_url = self.env['ir.config_parameter'].sudo().get_param(
            'report.url') or self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        rcontext = {
            'mode': 'print',
            'base_url': base_url,
            'company': self.env.user.company_id,
        }

        body = self.env['ir.ui.view'].render_template(
            "account_reports.report_financial_letter",
            values=dict(rcontext, lines=lines, footnotes=footnotes,
                        report=report_obj, context=self),
        )

        header = self.env['report'].render(
            "report.internal_layout",
            values=rcontext,
        )

        header = self.env['report'].render(
            "property_management_extended.property_external_layout_ar",
            values=dict(rcontext, subst=True, body=header),
        )

        landscape = False
        if len(self.get_columns_names()) > 4:
            landscape = True

        return self.env['report']._run_wkhtmltopdf([header], [''], [(0, body)], landscape, self.env.user.company_id.paperformat_id, spec_paperformat_args={'data-report-margin-top': 10, 'data-report-header-spacing': 10})
