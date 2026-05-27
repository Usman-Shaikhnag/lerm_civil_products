from odoo import models, fields, api

class LermOverview(models.Model):
    _name = 'lerm.overview'
    _description = 'Overview'

    discipline = fields.Many2one('lerm_civil.discipline',string="Discipline")
    sample = fields.Many2one("lerm.srf.sample",string="Sample")
    technician_id = fields.Many2one('res.users', string='Technician')
    total_samples = fields.Integer(string='Total Samples')
    assignment_pending = fields.Integer(string='Assignment Pending')
    alloted = fields.Integer(string='Alloted')
    pending_verification = fields.Integer(string='Pending Verification')
    in_report = fields.Integer(string='In Report')
    pending_approval = fields.Integer(string='Pending Approval')
    cancelled = fields.Integer(string='Cancelled')

    @api.model
    def _generate_overview_records(self):
        """Recreate dynamic overview records for all users in Technician group"""
        Sample = self.env['lerm.srf.sample']
        self.search([]).unlink()  # clear old transient data

        # Get the Technician Group
        tech_group = self.env.ref('lerm_civil.kes_technician_access_group', raise_if_not_found=False)
        if not tech_group:
            return  # safety check

        # Get only users that belong to the Technician group
        users = self.env['res.users'].search([('groups_id', 'in', tech_group.id)])

        records = []
        for user in users:
            samples = Sample.search([('technicians', '=', user.id)])
            records.append({
                'technician_id': user.id,
                'total_samples': len(samples),
                'assignment_pending': len(samples.filtered(lambda s: s.state == '1-allotment_pending')),
                'alloted': len(samples.filtered(lambda s: s.state == '2-alloted')),
                'pending_verification': len(samples.filtered(lambda s: s.state == '3-pending_verification')),
                'in_report': len(samples.filtered(lambda s: s.state == '4-in_report')),
                'pending_approval': len(samples.filtered(lambda s: s.state == '5-pending_approval')),
                'cancelled': len(samples.filtered(lambda s: s.state == '6-cancelled')),
            })
        self.create(records)
        return self.search([])



