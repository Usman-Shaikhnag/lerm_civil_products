from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime
import pytz
import logging

_logger = logging.getLogger(__name__)


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    # ─── Backdated Sequence Fields ───
    is_backdated = fields.Boolean(
        string="Use Backdated Date",
        default=False,
        help="If checked, the sequence will use a date from the source record "
             "instead of today's date when generating numbers."
    )
    source_model_id = fields.Many2one(
        'ir.model',
        string="Source Model",
        ondelete='set null',
        help="The model from which the date will be read (e.g., SRF, Invoice)."
    )
    date_field_id = fields.Many2one(
        'ir.model.fields',
        string="Date Field",
        ondelete='set null',
        domain="[('model_id', '=', source_model_id), ('ttype', 'in', ['date', 'datetime'])]",
        help="The date field on the source model to use for sequence generation."
    )

    # ─── Override next_by_code to support backdating ───
    @api.model
    def next_by_code(self, sequence_code, sequence_date=None):
        """Override to automatically resolve the effective date from the
        calling record when the sequence is configured for backdating.

        The calling code must pass 'backdated_record_id' in the context
        for this to work:
            self.env['ir.sequence'].with_context(
                backdated_record_id=rec.id
            ).next_by_code('your.sequence.code')
        """
        if not sequence_date:
            seq = self.search([
                ('code', '=', sequence_code),
                ('company_id', 'in', [self.env.company.id, False])
            ], order='company_id', limit=1)

            if seq.is_backdated and seq.source_model_id and seq.date_field_id:
                record_id = self._context.get('backdated_record_id')
                if record_id:
                    try:
                        record = self.env[seq.source_model_id.model].browse(record_id)
                        if record.exists():
                            date_value = record[seq.date_field_id.name]
                            if date_value:
                                sequence_date = date_value
                                _logger.info(
                                    "Backdated sequence '%s': using date %s from %s.%s (record #%s)",
                                    sequence_code, sequence_date,
                                    seq.source_model_id.model,
                                    seq.date_field_id.name,
                                    record_id
                                )
                    except Exception as e:
                        _logger.warning(
                            "Backdated sequence '%s': failed to resolve date — %s",
                            sequence_code, str(e)
                        )

        return super().next_by_code(sequence_code, sequence_date=sequence_date)

    # ─── Existing: prefix/suffix interpolation with %(next_y)s support ───
    def _get_prefix_suffix(self, date=None, date_range=None):
        def _interpolate(s, d):
            return (s % d) if s else ''

        def _interpolation_dict():
            # Set dates
            now = range_date = effective_date = datetime.now(pytz.timezone(self._context.get('tz') or 'UTC'))
            if date or self._context.get('ir_sequence_date'):
                effective_date = fields.Datetime.from_string(date or self._context.get('ir_sequence_date'))
            if date_range or self._context.get('ir_sequence_date_range'):
                range_date = fields.Datetime.from_string(date_range or self._context.get('ir_sequence_date_range'))

            # Predefined placeholders
            sequences = {
                'year': '%Y', 'month': '%m', 'day': '%d', 'y': '%y', 'doy': '%j', 'woy': '%W',
                'weekday': '%w', 'h24': '%H', 'h12': '%I', 'min': '%M', 'sec': '%S'
            }

            res = {}
            for key, fmt in sequences.items():
                res[key] = effective_date.strftime(fmt)
                res['range_' + key] = range_date.strftime(fmt)
                res['current_' + key] = now.strftime(fmt)

            # Custom next year logic (last 2 digits)
            next_year = (range_date.year + 1) % 100
            res['next_y'] = f'{next_year:02d}'  # always 2 digits like 26

            return res

        self.ensure_one()
        d = _interpolation_dict()
        try:
            interpolated_prefix = _interpolate(self.prefix, d)
            interpolated_suffix = _interpolate(self.suffix, d)
        except ValueError:
            raise UserError(_('Invalid prefix or suffix for sequence \'%s\'') % self.name)
        return interpolated_prefix, interpolated_suffix