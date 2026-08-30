from datetime import date

from odoo import api, fields, models


class LermHodBlock(models.Model):
    _name = 'lerm.hod.block'
    _description = 'HOD Sample Allotment Block'

    PENDING_STATES = ['1-allotment_pending', '7-partially-alloted']

    @api.model
    def _is_hod_user(self):
        hod_group = self.env.ref(
            'lerm_civil.kes_hod_access_group', raise_if_not_found=False)
        return bool(hod_group and self.env.user in hod_group.users)

    @api.model
    def _get_interval_minutes(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'hod_blocker.check_interval_minutes', '120')
        try:
            return max(1, int(float(value)))
        except (TypeError, ValueError):
            return 120

    @api.model
    def _is_enabled(self):
        value = self.env['ir.config_parameter'].sudo().get_param(
            'hod_blocker.enabled', 'False')
        return str(value).lower() in ('1', 'true', 'yes', 'on')

    @api.model
    def _get_pending_samples(self):
        """Pending samples belonging to the current HOD's department(s),
        i.e. samples whose discipline's HOD is the current user."""
        if not self._is_hod_user():
            return self.env['lerm.srf.sample']
        return self.env['lerm.srf.sample'].sudo().search([
            ('status', '=', '2-confirmed'),
            ('state', 'in', self.PENDING_STATES),
            ('discipline_id.hod', '=', self.env.user.id),
        ])

    @api.model
    def check_hod_block(self):
        enabled = self._is_hod_user() and self._is_enabled()
        samples = self._get_pending_samples()
        if not samples:
            return {
                'enabled': enabled,
                'interval_minutes': self._get_interval_minutes(),
                'blocked': False,
                'pending_count': 0,
                'samples': [],
            }
        today = date.today()
        blocked = any(
            sample.create_date and sample.create_date.date() < today
            for sample in samples)
        return {
            'enabled': enabled,
            'interval_minutes': self._get_interval_minutes(),
            'blocked': blocked,
            'pending_count': len(samples),
            'samples': [{
                'id': sample.id,
                'kes_no': sample.kes_no,
                'client': sample.srf_id.client if sample.srf_id else False,
                'material_name': sample.material_id.name if sample.material_id else False,
                'discipline': sample.discipline_id.discipline if sample.discipline_id else False,
                'received_date': fields.Date.to_string(sample.sample_received_date)
                    if sample.sample_received_date else False,
            } for sample in samples],
        }

    @api.model
    def get_pending_allotment_action(self):
        samples = self._get_pending_samples()
        return self.get_sample_allotment_action(samples.ids)

    @api.model
    def get_sample_allotment_action(self, sample_ids):
        if isinstance(sample_ids, int):
            sample_ids = [sample_ids]
        view = self.env.ref('lerm_civil.srf_sample_allotment_wizard')
        return {
            'name': 'Allot Sample',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sample.allotment.wizard',
            'view_id': view.id,
            'views': [[view.id, 'form']],
            'target': 'new',
            'context': {
                'active_ids': list(sample_ids),
                'active_id': sample_ids[0] if sample_ids else False,
                'hod_blocker_require_due_date': True,
            },
        }
