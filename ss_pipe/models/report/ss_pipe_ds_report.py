from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import base64
import qrcode
from io import BytesIO
from lxml import etree
import re

_UNIT_SUFFIX_RE = re.compile(
    r'[ \t]*[,;:]?[ \t]*(?:N/mm\s*\^?\s*[2²]|kN|KN|mm|%)\s*$',
    re.IGNORECASE,
)



class SsPipeReport(models.AbstractModel):
    _name = 'report.ss_pipe.ss_pipe_report'
    _description = 'SS Pipe Report'

    @api.model
    def _ss_pipe_param_label(self, param):
        name = (param.parameter_name or '').strip()
        if not name:
            return name
        unit = (param.unit.name or '').strip() if param.unit else ''
        if unit:
            u1 = unit
            u2 = unit.replace('²', '2')
            u3 = unit.replace('2', '²')
            u4 = unit.replace('2', '²')
            for u in (u1, u2, u3, u4):
                if u and name.endswith(u):
                    name = name[:-len(u)]
                    break
        else:
            name = _UNIT_SUFFIX_RE.sub('', name)
        name = re.sub(r'[ \t]*[,;:]?[ \t]*$', '', name)
        return name.strip()

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        nabl = data.get("nabl", False)

        # ✅ ELN Fetch
        if data.get("report_wizard"):
            eln = (
                self.env["lerm.eln"]
                .sudo()
                .search([("sample_id", "=", data.get("sample"))], limit=1)
            )
        elif data.get("context", {}).get("active_id"):
            eln = (
                self.env["lerm.eln"]
                .sudo()
                .search([("sample_id", "=", data["context"]["active_id"])], limit=1)
            )
        else:
            eln = self.env["lerm.eln"].sudo().browse(docids)

        if not eln or not eln.exists():
            raise ValueError("ELN record not found")

        # ✅ LAB FETCH
        lab = eln.sample_id.lab_location if eln.sample_id else False

        # ✅ QR LINK (थेट NABL ची मूळ लिंक QR मध्ये टाकणे)
        qr_link = lab.nabl_scope_link or ""

        qrcode_static = False  # <--- हे नाव खाली return मध्ये वापरले आहे
        if qr_link:
            # 🔳 QR Generate (NABL च्या लिंकचा QR)
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(qr_link)
            qr.make(fit=True)

            buffer = BytesIO()
            qr.make_image(fill_color="black", back_color="white").save(
                buffer, format="PNG"
            )
            qrcode_static = base64.b64encode(buffer.getvalue()).decode()

        # 🧩 QR Code तयार करा
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        report_url = f"{base_url}/download_report/sspipe/{'nabl' if nabl else 'nonnabl'}/{eln.id}"

        qr.add_data(report_url)
        qr.make(fit=True)
        qr_image = qr.make_image()
        buffered = BytesIO()
        qr_image.save(buffered, format="PNG")
        qr_code = base64.b64encode(buffered.getvalue()).decode()

         # ✅ General Data मिळवा
        model_id = eln.model_id
        model_name = (
            eln.material.product_based_calculation[0].ir_model.name
            if eln.material.product_based_calculation else False
        )
        if model_name:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = self.env['lerm.eln'].sudo().browse(docids)
        
        return {
            'eln': eln,
            'data' : general_data,
            'qrcode': qr_code,
            'fromEln' : data.get('fromEln', False),
            'qrcode_static': qr_static_b64,
            # 'nabl' is what the shared lerm_civil layout reads for the
            # letterhead. ss_report_type is what picks the rows; the NABL /
            # Non-NABL report templates set it themselves, so this is only a
            # fallback for direct rendering of this base template.
            'nabl' : nabl,
            'ss_report_type': data.get('ss_report_type') or ('nabl' if nabl else 'non_nabl')
        }


def _resolve_ss_pipe_records(env, docids, data=None):
    data = data or {}
    records = env['ss.pipe'].sudo().browse(docids or [])
    if records:
        return records
    if data.get('eln_id'):
        eln = env['lerm.eln'].sudo().browse(data['eln_id'])
    elif data.get('eln'):
        eln = env['lerm.eln'].sudo().browse(data.get('eln'))
    else:
        return records
    if not eln or not eln.exists():
        return records
    if eln.model_id:
        return env['ss.pipe'].sudo().browse(eln.model_id[:1].id)
    return env['ss.pipe'].sudo().search([('eln_ref', '=', eln.id)], limit=1)


def _record_scope(record):
    if record.eln_ref and record.eln_ref.sample_id:
        return record.eln_ref.sample_id.scope
    return False

class SsPipeDataSheet(models.AbstractModel):
    _name = 'report.ss_pipe.ss_pipe_datasheet'
    _description = 'SS Pipe DataSheet'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = data or {}
        if data.get('fromsample') == True:
            if 'active_id' in data.get('context', {}):
                eln = self.env['lerm.eln'].sudo().search([('sample_id', '=', data['context']['active_id'])], limit=1)
            else:
                eln = self.env['lerm.eln'].sudo().browse(docids or [])
        else:
            if data.get('report_wizard') == True:
                eln = self.env['lerm.eln'].sudo().search([('id', '=', data.get('eln'))], limit=1)
            else:
                eln = self.env['lerm.eln'].sudo().browse(data.get('eln_id') or docids or [])

        if not eln:
            raise UserError("ELN record not found for the SS Pipe datasheet.")

        model_id = eln.model_id
        pbc = eln.material.product_based_calculation
        model_record = pbc.filtered(lambda record: record.grade.id == eln.grade_id.id)[:1] or pbc[:1]
        model_name = model_record.ir_model.name if model_record else False
        if model_name and model_id:
            general_data = self.env[model_name].sudo().browse(model_id)
        else:
            general_data = (self.env['ss.pipe'].sudo().browse(eln.model_id[:1].id)
                            or self.env['ss.pipe'].sudo().search([('eln_ref', '=', eln.id)], limit=1))
        return {
            'eln': eln,
            'data': general_data,
            'fromEln': data.get('fromEln', False)
        }


class SsPipePrintReport(models.AbstractModel):
    _name = 'report.ss_pipe.ss_pipe_print_report'
    _inherit = 'report.ss_pipe.ss_pipe_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        records = _resolve_ss_pipe_records(self.env, docids, data)
        if not records:
            raise UserError("SS Pipe record not found for printing the report.")
        data['nabl'] = _record_scope(records[0]) == 'nabl'
        # Generic Print Report has no explicit button, so it follows the sample
        # scope. 'nabl' above is what the shared layout letterhead reads.
        data['ss_report_type'] = 'nabl' if data['nabl'] else 'non_nabl'
        if not data.get('eln_id'):
            data['eln_id'] = records[0].eln_ref.id
        return super(SsPipePrintReport, self)._get_report_values(docids, data)


class SsPipeNablReport(models.AbstractModel):
    _name = 'report.ss_pipe.ss_pipe_nabl_report'
    _inherit = 'report.ss_pipe.ss_pipe_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        records = _resolve_ss_pipe_records(self.env, docids, data)
        # No sample-scope guard: the user explicitly asked for the NABL
        # certificate, so the NABL report is always produced and row selection
        # is driven by each parameter's own NABL result.
        data['nabl'] = True
        data['ss_report_type'] = 'nabl'
        if not data.get('eln_id'):
            pipes = records or self.env['ss.pipe'].sudo().browse(docids or [])
            if not pipes or not pipes[0].eln_ref:
                raise UserError("SS Pipe record not linked to an ELN.")
            data['eln_id'] = pipes[0].eln_ref.id
        return super(SsPipeNablReport, self)._get_report_values(docids, data)


class SsPipeNonNablReport(models.AbstractModel):
    _name = 'report.ss_pipe.ss_pipe_non_nabl_report'
    _inherit = 'report.ss_pipe.ss_pipe_report'

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        records = _resolve_ss_pipe_records(self.env, docids, data)
        # No sample-scope guard: clicking "Print Non-NABL Report" on a NABL
        # scoped sample must still print the parameters that failed NABL.
        data['nabl'] = False
        data['ss_report_type'] = 'non_nabl'
        if not data.get('eln_id'):
            pipes = records or self.env['ss.pipe'].sudo().browse(docids or [])
            if not pipes or not pipes[0].eln_ref:
                raise UserError("SS Pipe record not linked to an ELN.")
            data['eln_id'] = pipes[0].eln_ref.id
        return super(SsPipeNonNablReport, self)._get_report_values(docids, data)
