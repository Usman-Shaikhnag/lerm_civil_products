from odoo import models, fields, api
from datetime import datetime

class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.model
    def _interpolation_dict(self):
        res = super(IrSequence, self)._interpolation_dict()
        # Add custom logic to extract the year from a date range and add 1 to it
        import wdb;wdb.set_trace()
        date_range = self._context.get('date_range_id')

        if date_range:
            date_range_record = self.env['date.range'].browse(date_range)
            if date_range_record.date_start:
                year = datetime.strptime(date_range_record.date_start, '%Y-%m-%d').year
                res['next_year'] = str(year + 1)
            else:
                res['next_year'] = '00'
        else:
            res['next_year'] = '00'
        return res