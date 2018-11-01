from datetime import datetime
from dateutil import relativedelta
from odoo import http, models, fields, api, _
import xlwt
from cStringIO import StringIO
import base64
from odoo import conf
import imp
from decimal import *
import copy
from collections import OrderedDict

TWOPLACES = Decimal(10) ** -2

def MultiplybyRate(rate, amountincur, curcomp, invcur):
    if curcomp != invcur:
        return rate * amountincur
    else:
        return amountincur

class sales_reports(models.TransientModel):
    _name = 'vitt_sales_reports.reportvatpl'

    vatcode_id = fields.Many2one('account.tax','Cod IVA',
                                 ondelete='cascade',
                                 domain="[('type_tax_use','=','sale')]")
    date_from = fields.Date(string='Date From', required=True,
        default=datetime.now().strftime('%Y-%m-01'))
    date_to = fields.Date(string='Date To', required=True,
        default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10])
    det_level = fields.Selection(
        [('detailed','Detallado'),
        ('overview','Resumido')],
        'Nivel de Detalle',
        default='detailed',
        translate=True,
    )
    journal_ids = fields.Many2many('account.journal',
                                 string="Journal",
                                 Translate=True,
                                 domain=[('type', '=', 'purchase'),('use_documents', '=', True)]
                                 )

    def gettotalsperVAT(self,invoices=None):

        arrayvat = OrderedDict()
        arrayvat['IVA 21%'] = 0.00
        arrayvat['IVA 10.50%'] = 0.00
        arrayvat['IVA 27%'] = 0.00
        arrayvat['IVA 5%'] = 0.00
        arrayvat['IVA 2.50%'] = 0.00
        for inv in invoices:
            if inv.journal_id.use_documents:
                totval4 = 0.00
                totval5 = 0.00
                totval6 = 0.00
                totval8 = 0.00
                totval9 = 0.00

                totval4 = sum(inv.tax_line_ids.filtered(lambda r: (
                    r.tax_id.tax_group_id.type == 'tax' and
                    r.tax_id.tax_group_id.tax == 'vat') and
                    r.tax_id.tax_group_id.afip_code == 4 and
                    r.tax_id.vatreport_included == True).mapped('amount'))
                if totval4 > 0:
                    total = float(MultiplybyRate(inv.currency_rate, totval4, inv.company_currency_id, inv.currency_id))
                    if inv.document_type_id.internal_type == 'credit_note':
                        total *= -1
                    arrayvat['IVA 10.50%'] += total

                totval5 = sum(inv.tax_line_ids.filtered(lambda r: (
                    r.tax_id.tax_group_id.type == 'tax' and
                    r.tax_id.tax_group_id.tax == 'vat') and
                    r.tax_id.tax_group_id.afip_code == 5 and
                    r.tax_id.vatreport_included == True).mapped('amount'))
                if totval5 > 0:
                    total = float(MultiplybyRate(inv.currency_rate, totval5, inv.company_currency_id, inv.currency_id))
                    if inv.document_type_id.internal_type == 'credit_note':
                        total *= -1
                    arrayvat['IVA 21%'] += total

                totval6 = sum(inv.tax_line_ids.filtered(lambda r: (
                    r.tax_id.tax_group_id.type == 'tax' and
                    r.tax_id.tax_group_id.tax == 'vat') and
                    r.tax_id.tax_group_id.afip_code == 6 and
                    r.tax_id.vatreport_included == True).mapped('amount'))
                if totval6 > 0:
                    total = float(MultiplybyRate(inv.currency_rate, totval6, inv.company_currency_id, inv.currency_id))
                    if inv.document_type_id.internal_type == 'credit_note':
                        total *= -1
                    arrayvat['IVA 27%'] += total

                totval8 = sum(inv.tax_line_ids.filtered(lambda r: (
                    r.tax_id.tax_group_id.type == 'tax' and
                    r.tax_id.tax_group_id.tax == 'vat') and
                    r.tax_id.tax_group_id.afip_code == 8 and
                    r.tax_id.vatreport_included == True).mapped('amount'))
                if totval8 > 0:
                    total = float(MultiplybyRate(inv.currency_rate, totval8, inv.company_currency_id, inv.currency_id))
                    if inv.document_type_id.internal_type == 'credit_note':
                        total *= -1
                    arrayvat['IVA 5%'] += total

                totval9 = sum(inv.tax_line_ids.filtered(lambda r: (
                    r.tax_id.tax_group_id.type == 'tax' and
                    r.tax_id.tax_group_id.tax == 'vat') and
                    r.tax_id.tax_group_id.afip_code == 9 and
                    r.tax_id.vatreport_included == True).mapped('amount'))
                if totval9 > 0:
                    total = float(MultiplybyRate(inv.currency_rate, totval9, inv.company_currency_id, inv.currency_id))
                    if inv.document_type_id.internal_type == 'credit_note':
                        total *= -1
                    arrayvat['IVA 2.50%'] += total
        return arrayvat

    def Print_to_excel(self):
        context = self._context
        filename= 'Libro_IVA_Compras.xls'
        workbook= xlwt.Workbook(encoding="UTF-8")
        worksheet= workbook.add_sheet('Detalle')
        #style = xlwt.easyxf('font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')
        #worksheet.write_merge(0,1,0,7,'REPORT IN EXCEL',style)
        
        #data
        vatcode_ids = list(self.vatcode_id)
        date_froms = self.date_from
        date_tos = self.date_to
        domain = [
            ('date', '>=', date_froms), ('date', '<=', date_tos),
            ('type', '!=', 'out_invoice'),('type', '!=', 'out_refund'),
            ('journal_id.use_documents', '=', True),('state', 'not in', ['draft','cancel'])
        ]
        if self.journal_ids:
            domain.append(('journal_id.id', 'in', list(self.journal_ids._ids)))

        invoiceModel = self.env['account.invoice']
        invoices = invoiceModel.search(domain,order="date_invoice")
        vatarray = self.gettotalsperVAT(invoices)
        vattot = {}

        # Titles
        worksheet.write(0, 0, _('Nombre del Informe: Libro IVA Compras'))
        worksheet.write(1, 0, _('Empresa: ') + self.env.user.company_id.name)
        cuit = self.env.user.company_id.partner_id.main_id_number
        worksheet.write(2, 0, _('CUIT: ') + cuit[0:2] + '-' + cuit[2:10] + '-' + cuit[10:11])
        worksheet.write(4, 0, _('Periodo ') +
                        date_froms[8:10] + '-' + date_froms[5:7] + '-' + date_froms[0:4]
                        + ':' + date_tos[8:10] + '-' + date_tos[5:7] + '-' + date_tos[0:4])


        #columns
        index = 5
        if self.det_level == 'detailed':
            subindex = 0
            worksheet.write(index,subindex,_('Fecha'))
            subindex += 1
            worksheet.write(index,subindex,_('Tipo Doc'))
            subindex += 1
            worksheet.write(index,subindex,_('Serie'))
            subindex += 1
            worksheet.write(index,subindex,_('Nro. Comp'))
            subindex += 1
            worksheet.write(index,subindex,_('Resp IVA'))
            subindex += 1
            worksheet.write(index,subindex,_('CUIT/CUIL'))
            subindex += 1
            worksheet.write(index,subindex,_('Nombre'))
            subindex += 1
            worksheet.write(index,subindex,_('Neto Gravado'))
            subindex += 1
            for key in vatarray:
                worksheet.write(index,subindex, key)
                subindex += 1
            worksheet.write(index,subindex,_('Exento'))
            subindex += 1
            worksheet.write(index,subindex,_('Percepcion IVA'))
            subindex += 1
            worksheet.write(index,subindex,_('Percepcion IIBB'))
            subindex += 1
            worksheet.write(index,subindex,_('Impuestos Internos'))
            subindex += 1
            worksheet.write(index,subindex,_('No Gravado'))
            subindex += 1
            #worksheet.write(0,11,'IVA')
            worksheet.write(index,subindex,_('Total'))
        else:
            subindex = 0
            worksheet.write(index,subindex,_('Fecha'))
            subindex += 1
            worksheet.write(index,subindex,_('Nombre'))
            subindex += 1
            worksheet.write(index,subindex,_('CUIT/CUIL'))
            subindex += 1
            worksheet.write(index,subindex,_('Resp IVA'))
            subindex += 1
            worksheet.write(index,subindex,_('Tipo Doc'))
            subindex += 1
            worksheet.write(index,subindex,_('Serie'))
            subindex += 1
            worksheet.write(index,subindex,_('Nro. Comp'))
            subindex += 1
            worksheet.write(index,subindex,_('Total'))
            subindex += 1
            worksheet.write(index,subindex,_('Neto Gravado'))
            subindex += 1
            worksheet.write(index,subindex,_('No Gravado'))
            subindex += 1
            worksheet.write(index,subindex,_('IVA'))
            subindex += 1
            worksheet.write(index,subindex,_('Percepciones'))
            subindex += 1
            worksheet.write(index,subindex,_('Impuestos Internos'))
            subindex += 1

        index = 7
        camount_untaxed = 0
        gettotpercep = 0
        gettotgrossincome  = 0
        gettotexempt = 0
        gettotnovat = 0
        camount_total = 0
        gettotinttaxes = 0
        tot1 = tot2 = tot3 = tot4 = tot5 = tot6 = 0

        vattot = OrderedDict()
        vattot['IVA 21%'] = 0.00
        vattot['IVA 10.50%'] = 0.00
        vattot['IVA 27%'] = 0.00
        vattot['IVA 5%'] = 0.00
        vattot['IVA 2.50%'] = 0.00

        matrix = {}
        matrixbase = {}
        vatcodes = {}
        vatcodesbase = {}
        tmp = 0.0
        for o in invoices:
            if o.journal_id.use_documents and o.validated_inv(self):
                subindex = 0
                if self.det_level == 'detailed':
                    worksheet.write(index, subindex, o.date_invoice)
                    subindex += 1

                    worksheet.write(index, subindex, o.journal_document_type_id.document_type_id.report_name)
                    subindex += 1

                    let = o.display_name[-16:]
                    let = let[1]
                    worksheet.write(index, subindex, str(let))  # letra
                    subindex += 1

                    worksheet.write(index, subindex, str(o.display_name[-13:]))  # nro comprob
                    subindex += 1

                    worksheet.write(index, subindex,  str(o.partner_id.afip_responsability_type_id.report_code_name))
                    subindex += 1

                    if str(o.partner_id.main_id_number) == 'False':
                        worksheet.write(index, subindex, ' ')
                    else:
                        cuit = o.partner_id.main_id_number
                        worksheet.write(index, subindex,cuit[0:2] + '-' + cuit[2:10] + '-' + cuit[10:11])
                    subindex += 1

                    worksheet.write(index, subindex,  o.partner_id.name)
                    subindex += 1

                    tot = o.camount_untaxed()
                    worksheet.write(index, subindex, tot)
                    camount_untaxed += tot
                    subindex += 1

                    #worksheet.write(index, 11, o.gettotvat())
                    vatarray = self.gettotalsperVAT(o)
                    for key in vatarray:
                        worksheet.write(index, subindex, vatarray[key])
                        vattot[key] += vatarray[key]
                        subindex += 1

                    tot = o.gettotexempt()
                    worksheet.write(index, subindex, tot)
                    gettotexempt += tot
                    subindex += 1

                    tot = o.gettotpercep()
                    worksheet.write(index, subindex, tot)
                    gettotpercep += tot
                    subindex += 1

                    tot = o.gettotgrossincome()
                    worksheet.write(index, subindex, tot)
                    gettotgrossincome += tot
                    subindex += 1

                    tot = o.gettotinttaxes()
                    worksheet.write(index, subindex, tot)
                    gettotinttaxes += tot
                    subindex += 1

                    tot = o.gettotnovat()
                    worksheet.write(index, subindex, tot)
                    gettotnovat += tot
                    subindex += 1

                    tot = o.camount_total()
                    worksheet.write(index, subindex, tot)
                    camount_total += tot
                    index += 1

                    #Matrix for vat totals grouped by document_type_id
                    for vat in o.tax_line_ids:
                        if vat.tax_id.vatreport_included:
                            amount = float(MultiplybyRate(o.currency_rate, vat.amount, o.company_currency_id, o.currency_id))
                            base = float(MultiplybyRate(o.currency_rate, vat.base, o.company_currency_id, o.currency_id))
                            if vat.name in vatcodes:
                                vatcodes[vat.name] += amount
                            else:
                                vatcodes.update({vat.name: amount})

                            if vat.name in vatcodesbase:
                                vatcodesbase[vat.name] += base
                            else:
                                vatcodesbase.update({vat.name: base})

                    for vat in o.tax_line_ids:
                        if vat.tax_id.vatreport_included:
                            amount = float(MultiplybyRate(o.currency_rate, vat.amount, o.company_currency_id, o.currency_id))
                            base = float(MultiplybyRate(o.currency_rate, vat.base, o.company_currency_id, o.currency_id))
                            if vat.amount > 0:
                                if o.document_type_id.internal_type == 'credit_note':
                                    monto = -amount
                                else:
                                    monto = amount
                            if vat.amount == 0:
                                if o.document_type_id.internal_type == 'credit_note':
                                    monto = -base
                                else:
                                    monto = base

                            if not o.partner_id.afip_responsability_type_id.name in matrix.keys():
                                matrix[o.partner_id.afip_responsability_type_id.name] = {vat.name:monto}
                            else:
                                if not vat.name in matrix[o.partner_id.afip_responsability_type_id.name].keys():
                                    matrix[o.partner_id.afip_responsability_type_id.name].update({vat.name:monto})
                                else:
                                    matrix[o.partner_id.afip_responsability_type_id.name][vat.name] += monto

                    for vat in o.tax_line_ids:
                        if vat.tax_id.vatreport_included:
                            amount = float(MultiplybyRate(o.currency_rate, vat.amount, o.company_currency_id, o.currency_id))
                            base = float(MultiplybyRate(o.currency_rate, vat.base, o.company_currency_id, o.currency_id))
                            if vat.amount > 0:
                                if o.document_type_id.internal_type == 'credit_note':
                                    monto = -base
                                else:
                                    monto = base
                            if vat.amount == 0:
                                if o.document_type_id.internal_type == 'credit_note':
                                    monto = -amount
                                else:
                                    monto = amount

                            if not o.partner_id.afip_responsability_type_id.name in matrixbase.keys():
                                matrixbase[o.partner_id.afip_responsability_type_id.name] = {vat.name:monto}
                            else:
                                if not vat.name in matrixbase[o.partner_id.afip_responsability_type_id.name].keys():
                                    matrixbase[o.partner_id.afip_responsability_type_id.name].update({vat.name:monto})
                                else:
                                    matrixbase[o.partner_id.afip_responsability_type_id.name][vat.name] += monto

                else:
                    worksheet.write(index, subindex, o.date_invoice)
                    subindex += 1

                    worksheet.write(index, subindex, o.partner_id.name)
                    subindex += 1

                    if str(o.partner_id.main_id_number) == 'False':
                        worksheet.write(index, subindex, ' ')
                    else:
                        worksheet.write(index, subindex, o.partner_id.main_id_number)
                    subindex += 1

                    worksheet.write(index, subindex, str(o.partner_id.afip_responsability_type_id.report_code_name))
                    subindex += 1

                    worksheet.write(index, subindex, o.journal_document_type_id.document_type_id.report_name)
                    subindex += 1

                    let = o.display_name[-16:]
                    let = let[1]
                    worksheet.write(index, subindex, str(let))  # letra
                    subindex += 1

                    worksheet.write(index, subindex, str(o.display_name[-13:]))  # nro comprob
                    subindex += 1

                    tot = 0.0
                    if o.document_type_id.internal_type == 'credit_note':
                        tot = -o.camount_total()
                    else:
                        tot = o.camount_total()
                    tot1 += tot
                    worksheet.write(index, subindex, str(tot))
                    subindex += 1

                    worksheet.write(index, subindex, str(o.camount_untaxed()))
                    tot2 += o.camount_untaxed()
                    subindex += 1

                    worksheet.write(index, subindex, str(o.gettotexempt() + o.gettotnovat()))
                    tot3 += o.gettotexempt() + o.gettotnovat()
                    subindex += 1

                    tot = 0.0
                    vatarray = self.gettotalsperVAT(o)
                    for key in vatarray:
                        tot += vatarray[key]
                    tot4 += tot
                    worksheet.write(index, subindex, str(tot))
                    subindex += 1

                    tot = o.gettotpercep() + o.gettotgrossincome()
                    tot5 += tot
                    worksheet.write(index, subindex, tot)
                    subindex += 1

                    tot = o.gettotinttaxes()
                    tot6 += tot
                    worksheet.write(index, subindex, tot)
                    subindex += 1
                    index += 1

        if self.det_level == 'detailed':
            worksheet.write(index, 0, _("Totales"))
            subindex = 7
            worksheet.write(index, subindex, camount_untaxed)
            subindex += 1
            for key in vattot:
                worksheet.write(index, subindex, vattot[key])
                subindex += 1
            worksheet.write(index, subindex, gettotexempt)
            subindex += 1
            worksheet.write(index, subindex, gettotpercep)
            subindex += 1
            worksheet.write(index, subindex, gettotgrossincome)
            subindex += 1
            worksheet.write(index, subindex, gettotinttaxes)
            subindex += 1
            worksheet.write(index, subindex, gettotnovat)
            subindex += 1
            worksheet.write(index, subindex, camount_total)

            index += 2
            subindex = 0
            worksheet.write(index, subindex, _("Totales Agrupados"))
            subindex += 1
            for code in vatcodes:
                worksheet.write(index, subindex, _("Base"))
                subindex += 1
                worksheet.write(index, subindex, code)
                subindex += 1
            worksheet.write(index, subindex, _("Totales"))
            subindex += 1

            totgrp = 0
            for type in matrix:
                index += 1
                subindex = 0
                worksheet.write(index, subindex, type)
                subindex += 1
                for code in vatcodes:
                    foundf = False
                    for key, value in matrix[type].iteritems():
                        if key == code:
                            foundf = True
                            worksheet.write(index, subindex, matrixbase[type][key])
                            subindex += 1
                            worksheet.write(index, subindex, value)
                            subindex += 1
                            totgrp +=  (matrixbase[type][key] + value)
                    if not foundf:
                        subindex += 2
                worksheet.write(index, subindex, totgrp)
                subindex += 1
                totgrp = 0

            #print matrix

        else:
            subindex = 7
            worksheet.write(index, subindex, tot1)
            subindex += 1
            worksheet.write(index, subindex, tot2)
            subindex += 1
            worksheet.write(index, subindex, tot3)
            subindex += 1
            worksheet.write(index, subindex, tot4)
            subindex += 1
            worksheet.write(index, subindex, tot5)
            subindex += 1
            worksheet.write(index, subindex, tot6)
            subindex += 1


        fp = StringIO()
        workbook.save(fp)
        export_id = self.env['excel.extended'].create({'excel_file': base64.encodestring(fp.getvalue()), 'file_name': filename }).id
        fp.close()
        return{
            'view_mode': 'form',
            'res_id': export_id,
            'res_model': 'excel.extended',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'context': context,
            'target': 'new',
        }


    @api.multi
    def ex_salesvatreport(self):
        datas = {
          'filter': self.vatcode_id.id,
          'date_froms': self.date_from,
          'date_tos': self.date_to,
          'journal_ids': list(self.journal_ids._ids),
        }
        return self.env['report'].with_context(landscape=True).get_action(self, 'vitt_sales_reports.reportvatpl', data=datas)


class report_vitt_sales_reports_reportvatpl(models.Model):
    _name = "report.vitt_sales_reports.reportvatpl"

    def render_html(self,docids, data=None):
        domain = [
            ('date', '>=', data['date_froms']), ('date', '<=', data['date_tos']),
            ('type', '!=', 'out_invoice'),('type', '!=', 'out_refund'),
            ('journal_id.use_documents', '=', True),('state', 'not in', ['draft','cancel']),
            ('journal_id.id', 'in', data['journal_ids'])
        ]
        invoiceModel = self.env['account.invoice']
        invoices = invoiceModel.search(domain,order="date_invoice")
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('vitt_sales_reports.reportvatpl')
        docargs = {
            'doc_ids': invoices._ids,
            'doc_model': report.model,
            'docs': invoices,
        }
        return self.env['report'].render('vitt_sales_reports.reportvatpl', docargs)


