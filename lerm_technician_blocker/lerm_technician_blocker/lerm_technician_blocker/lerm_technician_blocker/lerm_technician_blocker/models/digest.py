from odoo import fields, models

NOTIFICATION_TYPES = [
    ('1-new_work', 'New Work'),
    ('2-due_tomorrow', 'Due Tomorrow'),
    ('2-due_today', 'Due Today'),
    ('2-overdue', 'Overdue'),
]


class TechnicianDigest(models.Model):
    _name = 'lerm.tech.digest'
    _description = 'Technician Work Digest'
    _order = 'create_date asc'

    technician_id = fields.Many2one(
        'res.users', string='Technician', required=True, index=True)
    state = fields.Selection([
        ('1-pending', 'Pending'),
        ('2-seen', 'Seen'),
    ], string='State', default='1-pending')
    notification_type = fields.Selection(
        NOTIFICATION_TYPES, string='Notification Type', default='1-new_work')
    digest_date = fields.Datetime(
        string='Digest Date', default=fields.Datetime.now, readonly=True)
    line_ids = fields.One2many(
        'lerm.technician.notification', 'digest_id', string='Jobs')


class TechnicianNotification(models.Model):
    _name = 'lerm.technician.notification'
    _description = 'Technician Notified Job'

    technician_id = fields.Many2one(
        'res.users', string='Technician', required=True, index=True)
    sample_id = fields.Many2one(
        'lerm.srf.sample', string='Sample', required=True, ondelete='cascade')
    digest_id = fields.Many2one(
        'lerm.tech.digest', string='Digest', ondelete='cascade')
    notification_type = fields.Selection(
        NOTIFICATION_TYPES, string='Notification Type', default='1-new_work',
        index=True)

    _sql_constraints = [
        ('technician_sample_type_uniq',
         'unique (technician_id, sample_id, notification_type)',
         'This job has already been notified to this technician for this '
         'notification type.'),
    ]
