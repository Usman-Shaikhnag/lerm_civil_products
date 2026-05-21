from odoo import models, fields, api
from odoo.exceptions import ValidationError
from openpyxl import load_workbook
import base64
import io
from datetime import datetime

class PileLoadImportWizard(models.TransientModel):
    _name = 'pile.load.import.wizard'
    _description = 'Pile Load Excel Import Wizard'

    file = fields.Binary(required=True)
    filename = fields.Char()

    parent_id = fields.Many2one(
        'pile.load.test.parent',
        required=True
    )

    def action_import_excel(self):

        self.ensure_one()

        if not self.file:
            raise ValidationError("Please upload an Excel file.")

        file_data = base64.b64decode(self.file)

        workbook = load_workbook(
            filename=io.BytesIO(file_data),
            data_only=True
        )

        required_sheets = ['Loading', 'Unloading']

        for sheet_name in required_sheets:
            if sheet_name not in workbook.sheetnames:
                raise ValidationError(
                    f"Sheet '{sheet_name}' not found in Excel."
                )

        self._process_sheet(
            workbook['Loading'],
            'pile.load.reading.loading'
        )

        self._process_sheet(
            workbook['Unloading'],
            'pile.load.reading.unloading'
        )

        self.parent_id.action_recompute_all()
        self.parent_id.action_generate_graph()

    def _process_sheet(self, sheet, model_name):

        Model = self.env[model_name]

        headers = [
            'Date Time',
            'Load',
            'Dial A',
            'Dial B',
            'Dial C',
            'Dial D',
        ]

        for index, row in enumerate(
            sheet.iter_rows(min_row=2, values_only=True),
            start=2
        ):

            # Skip fully empty rows
            if not any(row):
                continue

            row_data = dict(zip(headers, row))

            for field_name, value in row_data.items():

                if value in (None, ''):
                    raise ValidationError(
                        f"{field_name} is empty in "
                        f"{sheet.title} sheet row {index}"
                    )

            excel_dt = row_data['Date Time']

            if not isinstance(excel_dt, datetime):
                raise ValidationError(
                    f"Invalid Date Time in "
                    f"{sheet.title} sheet row {index}"
                )

            # Round to minute
            normalized_dt = excel_dt.replace(
                second=0,
                microsecond=0
            )

            existing = Model.search([
                ('parent_id', '=', self.parent_id.id)
            ])

            matched_record = existing.filtered(
                lambda r:
                    r.reading_datetime and
                    r.reading_datetime.replace(
                        second=0,
                        microsecond=0
                    ) == normalized_dt
            )

            vals = {
                'parent_id': self.parent_id.id,
                'reading_datetime': normalized_dt,
                'load_tonne': row_data['Load'],
                'dial_a': row_data['Dial A'],
                'dial_b': row_data['Dial B'],
                'dial_c': row_data['Dial C'],
                'dial_d': row_data['Dial D'],
            }

            if matched_record:
                matched_record[0].write(vals)
            else:
                Model.create(vals)

