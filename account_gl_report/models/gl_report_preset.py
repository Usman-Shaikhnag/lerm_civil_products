from odoo import api, fields, models


class AccountGLReportPreset(models.Model):
    _name = 'account.gl.report.preset'
    _description = 'General Ledger Report Preset'
    _order = 'is_default DESC, write_date DESC'
    _rec_name = 'name'

    name = fields.Char(string='Preset Name', required=True, translate=True)
    user_id = fields.Many2one(
        'res.users', string='User',
        default=lambda self: self.env.user,
        required=True, index=True)
    params_json = fields.Text(string='Filter Parameters (JSON)', required=True)
    is_default = fields.Boolean(string='Default Preset', default=False)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_name_per_user',
         'UNIQUE(name, user_id, company_id)',
         'Preset name must be unique per user and company.'),
    ]

    @api.model
    def get_user_presets(self):
        presets = self.search([
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
        ])
        return [{
            'id': p.id,
            'name': p.name,
            'params': p.params_json,
            'is_default': p.is_default,
        } for p in presets]

    def save_preset(self, name, params_json):
        existing = self.search([
            ('name', '=', name),
            ('user_id', '=', self.env.user.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if existing:
            existing.write({'params_json': params_json})
            return existing.id
        return self.create({
            'name': name,
            'user_id': self.env.user.id,
            'params_json': params_json,
            'company_id': self.env.company.id,
        }).id
