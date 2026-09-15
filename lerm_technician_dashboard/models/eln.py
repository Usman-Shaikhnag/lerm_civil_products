from odoo import fields, models


class ELN(models.Model):
    _inherit = 'lerm.eln'

    stage_updated_at = fields.Datetime(
        string='Last Stage Update',
        default=lambda self: fields.Datetime.now(),
        help='Timestamp of the last workflow stage (state) change. Used by the '
             'technician dashboard to compute how long a worksheet has been '
             'waiting on verification / approval.',
    )

    def write(self, vals):
        if 'state' in vals:
            vals = dict(vals)
            vals['stage_updated_at'] = fields.Datetime.now()
        return super(ELN, self).write(vals)
