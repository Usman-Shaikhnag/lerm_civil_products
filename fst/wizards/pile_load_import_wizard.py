from odoo import models, fields, api
from odoo.exceptions import ValidationError
from openpyxl import load_workbook
import base64
import io
from datetime import datetime, time
from pytz import timezone
import pytz

india_tz = timezone('Asia/Kolkata')

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
            'Date',
            'Time',
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
            # if not any(row):
            #     continue

            row_data = dict(zip(headers, row))
            if (
                row_data['Load'] in (None, '')
                and row_data['Dial A'] in (None, '')
                and row_data['Dial B'] in (None, '')
                and row_data['Dial C'] in (None, '')
                and row_data['Dial D'] in (None, '')
            ):
                continue

            for field_name, value in row_data.items():

                if value in (None, ''):
                    raise ValidationError(
                        f"{field_name} is empty in "
                        f"{sheet.title} sheet row {index}"
                    )

            excel_date = row_data['Date']
            excel_time = row_data['Time']

            
            if not isinstance(excel_date, datetime):
                raise ValidationError(
                    f"Invalid Date in "
                    f"{sheet.title} sheet row {index}"
                )

            if isinstance(excel_time, datetime):
                time_part = excel_time.time()

            elif isinstance(excel_time, time):
                time_part = excel_time

            else:
                raise ValidationError(
                    f"Invalid Time in "
                    f"{sheet.title} sheet row {index}"
                )

            excel_dt = datetime.combine(
                excel_date.date(),
                time_part
            )

            # Excel times are local India times
            localized_dt = india_tz.localize(excel_dt)

            # Convert to UTC for Odoo storage
            normalized_dt = localized_dt.astimezone(
                pytz.UTC
            ).replace(
                tzinfo=None,
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

