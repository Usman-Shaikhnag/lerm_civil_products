from datetime import datetime, timedelta

from odoo import api, fields, models

STATE_LABELS = {
    '2-alloted': 'Alloted',
    '7-calculated': 'In-Test',
}


class TechnicianBlocker(models.Model):
    _name = 'lerm.technician.blocker'
    _description = 'Technician New Work / Due Date Blocker'

    WORK_STATES = ['2-alloted', '7-calculated']

    # ----------------------------------------------------------------
    # Config helpers
    # ----------------------------------------------------------------
    @api.model
    def _get_param(self, key, default):
        return self.env['ir.config_parameter'].sudo().get_param(key, default)

    @api.model
    def _set_param(self, key, value):
        self.env['ir.config_parameter'].sudo().set_param(key, value)

    @api.model
    def _is_enabled(self):
        value = self._get_param('technician_blocker.enabled', 'False')
        return str(value).lower() in ('1', 'true', 'yes', 'on')

    @api.model
    def _is_due_enabled(self):
        value = self._get_param('technician_blocker.due_enabled', 'False')
        return str(value).lower() in ('1', 'true', 'yes', 'on')

    @api.model
    def _get_window_times(self):
        """List of daily new-work notification windows as 'HH:MM' strings."""
        value = self._get_param('technician_blocker.window_times', '13:00,15:00,18:00')
        windows = []
        for item in str(value).split(','):
            item = item.strip()
            if not item:
                continue
            try:
                datetime.strptime(item, '%H:%M')
            except (TypeError, ValueError):
                continue
            windows.append(item)
        return windows or ['13:00', '15:00', '18:00']

    @api.model
    def _get_morning_time(self):
        value = self._get_param('technician_blocker.morning_time', '09:00')
        try:
            datetime.strptime(str(value), '%H:%M')
        except (TypeError, ValueError):
            return '09:00'
        return str(value)

    @api.model
    def _get_tz(self):
        tz = self._get_param('technician_blocker.tz', '')
        if not tz:
            tz = self.env.user.tz or 'UTC'
        return tz or 'UTC'

    @api.model
    def _now_local(self):
        return fields.Datetime.context_timestamp(
            self.with_context(tz=self._get_tz()), fields.Datetime.now())

    @api.model
    def _parse_hhmm(self, item):
        try:
            hour, minute = (int(p) for p in str(item).split(':'))
        except (TypeError, ValueError):
            return None
        return (hour, minute)

    @api.model
    def _window_start_datetimes(self, now, minutes_only=None):
        """Build local datetime starts for the given clock times (default all
        configured new-work windows plus the morning window)."""
        times = []
        if minutes_only is not None:
            times = [m for m in minutes_only if m]
        else:
            times = self._get_window_times() + [self._get_morning_time()]
        starts = []
        for item in times:
            hm = self._parse_hhmm(item)
            if not hm:
                continue
            for delta_days in (0, 1):
                base = now + timedelta(days=delta_days)
                starts.append(base.replace(
                    hour=hm[0], minute=hm[1], second=0, microsecond=0))
        return starts

    @api.model
    def _fire_stamp_now(self, key, minutes_only):
        """True when current local time is inside one of `minutes_only`
        (grace a couple of minutes for delayed ticks) and that window has not
        already fired today under `key`. Stamps the fired window start."""
        now = self._now_local()
        current_minute = now.replace(second=0, microsecond=0)
        active = None
        for item in minutes_only:
            hm = self._parse_hhmm(item)
            if not hm:
                continue
            window_start = current_minute.replace(
                hour=hm[0], minute=hm[1])
            if window_start <= current_minute <= \
                    window_start + timedelta(minutes=3):
                if active is None or window_start > active:
                    active = window_start
        if active is None:
            return False
        stamp = active.strftime('%Y-%m-%d %H:%M')
        if self._get_param(key, '') == stamp:
            return False
        self._set_param(key, stamp)
        return True

    @api.model
    def _is_technician(self):
        group = self.env.ref(
            'lerm_civil.kes_technician_access_group', raise_if_not_found=False)
        return bool(group and self.env.user in group.users)

    # ----------------------------------------------------------------
    # Work discovery (shared by all pipelines)
    # ----------------------------------------------------------------
    @api.model
    def _get_owner_users(self):
        """res.users that own a material AND belong to the Technician group
        (the popup audience)."""
        group = self.env.ref(
            'lerm_civil.kes_technician_access_group', raise_if_not_found=False)
        products = self.env['product.template'].sudo().search([
            ('ownership_ids', '!=', False),
        ])
        owners = products.mapped('ownership_ids')
        if group:
            owners = owners.filtered(lambda u: u in group.users)
        return owners

    @api.model
    def _get_owned_materials(self, user_id):
        return self.env['product.template'].sudo().search([
            ('ownership_ids', 'in', user_id),
        ])

    @api.model
    def _get_working_samples(self, user_id):
        """Confirmed samples of owned materials currently in working state."""
        owned = self._get_owned_materials(user_id)
        if not owned:
            return self.env['lerm.srf.sample']
        return self.env['lerm.srf.sample'].sudo().search([
            ('status', '=', '2-confirmed'),
            ('state', 'in', self.WORK_STATES),
            ('material_id', 'in', owned.ids),
        ])

    @api.model
    def _get_unnotified(self, user_id, samples, notification_type):
        """Subset of samples never notified to this user for the given type."""
        if not samples:
            return samples
        notified = self.env['lerm.technician.notification'].sudo().search([
            ('technician_id', '=', user_id),
            ('sample_id', 'in', samples.ids),
            ('notification_type', '=', notification_type),
        ])
        return samples - notified.sample_id

    @api.model
    def _get_new_jobs(self, user_id):
        """Working samples never notified as NEW WORK (notify-once rule)."""
        return self._get_unnotified(
            user_id, self._get_working_samples(user_id), '1-new_work')

    @api.model
    def _get_due_jobs(self, user_id, due_type):
        """Working samples whose report is due tomorrow / today and that were
        never notified for that specific message type."""
        today = self._now_local().date()
        offset = 1 if due_type == '2-due_tomorrow' else 0
        target = today + timedelta(days=offset)
        samples = self._get_working_samples(user_id).filtered(
            lambda s: s.report_due_date == target)
        return self._get_unnotified(user_id, samples, due_type)

    @api.model
    def _get_overdue_jobs(self, user_id):
        """Working samples already past their report due date (live query)."""
        today = self._now_local().date()
        samples = self._get_working_samples(user_id).filtered(
            lambda s: s.report_due_date and s.report_due_date < today)
        return samples

    # ----------------------------------------------------------------
    # Message builders
    # ----------------------------------------------------------------
    @api.model
    def _sample_srf_ref(self, sample):
        return sample.srf_id.srf_id if sample.srf_id and sample.srf_id.srf_id \
            else (sample.srf_id.kes_number if sample.srf_id else False)

    @api.model
    def _sample_material(self, sample):
        return sample.material_id_lab_name or (
            sample.material_id.name if sample.material_id else False)

    @api.model
    def _sample_parameters(self, sample):
        return ', '.join(
            name for name in sample.parameters.mapped('parameter_name') if name)

    @api.model
    def _build_due_message(self, sample, due_type):
        material = self._sample_material(sample) or 'Material'
        parts = ['sample %s' % (sample.kes_no or sample.sample_no or '')]
        if material:
            parts.insert(0, material)
        srf = self._sample_srf_ref(sample)
        if srf:
            parts.insert(0, 'SRF %s' % srf)
        ref = ' — '.join(parts)
        if due_type == '2-due_tomorrow':
            return '%s is due tomorrow. Please complete the work.' % ref
        if due_type == '2-due_today':
            return '%s is due today. Please complete and submit the report.' % ref
        if due_type == '2-overdue':
            due = fields.Date.to_string(sample.report_due_date) \
                if sample.report_due_date else False
            suffix = ' (due %s).' % due if due else '.'
            return '%s is Overdue%s Pending Reassignment.' % (ref, suffix)
        return ref

    @api.model
    def _row(self, sample, due_type=None):
        row = {
            'id': sample.id,
            'kes_no': sample.kes_no,
            'sample_no': sample.sample_no,
            'material_name': self._sample_material(sample),
            'parameters': self._sample_parameters(sample),
            'srf_id': self._sample_srf_ref(sample),
            'received_date': fields.Date.to_string(sample.sample_received_date)
                if sample.sample_received_date else False,
            'due_date': fields.Date.to_string(sample.report_due_date)
                if sample.report_due_date else False,
            'state': STATE_LABELS.get(sample.state, sample.state),
        }
        if due_type:
            row['message'] = self._build_due_message(sample, due_type)
        return row

    # ----------------------------------------------------------------
    # Cron entry point
    # ----------------------------------------------------------------
    @api.model
    def _cron_generate_digests(self):
        """Run every minute; fires the new-work windows and the morning
        due-date digest independently."""
        self._maybe_generate_new_work_digests()
        self._maybe_generate_due_digests()

    @api.model
    def _maybe_generate_new_work_digests(self):
        if not self._is_enabled():
            return
        if not self._fire_stamp_now(
                'technician_blocker.last_fire', self._get_window_times()):
            return
        self._create_digests('1-new_work',
                             lambda u: self._get_new_jobs(u.id))

    @api.model
    def _maybe_generate_due_digests(self):
        if not self._is_due_enabled():
            return
        morning = [self._get_morning_time()]
        if not self._fire_stamp_now('technician_blocker.last_fire_due', morning):
            return
        # Both messages are fired in the same morning run: samples due today
        # and samples due tomorrow each get their own once-only digest.
        self._create_digests('2-due_tomorrow',
                             lambda u: self._get_due_jobs(u.id, '2-due_tomorrow'))
        self._create_digests('2-due_today',
                             lambda u: self._get_due_jobs(u.id, '2-due_today'))

    @api.model
    def _create_digests(self, notification_type, job_fn):
        for user in self._get_owner_users():
            jobs = job_fn(user)
            if not jobs:
                continue
            digest = self.env['lerm.tech.digest'].sudo().create({
                'technician_id': user.id,
                'notification_type': notification_type,
            })
            for sample in jobs:
                self.env['lerm.technician.notification'].sudo().create({
                    'technician_id': user.id,
                    'sample_id': sample.id,
                    'digest_id': digest.id,
                    'notification_type': notification_type,
                })

    # ----------------------------------------------------------------
    # RPC surface used by the popup
    # ----------------------------------------------------------------
    @api.model
    def _pending_digests(self, types=None):
        domain = [('technician_id', '=', self.env.user.id),
                  ('state', '=', '1-pending')]
        if types is not None:
            domain.append(('notification_type', 'in', types))
        return self.env['lerm.tech.digest'].sudo().search(domain)

    @api.model
    def _active_digest_data(self, digests):
        """From pending digests, return still-relevant notifications (samples
        still confirmed and in a working state). A digest is only auto-seen
        (cleaned up) when none of its lines refer to active work any more."""
        notifications = self.env['lerm.technician.notification'].sudo().search([
            ('digest_id', 'in', digests.ids),
        ])
        if not notifications:
            return digests, notifications

        def _is_active(n):
            return n.sample_id.status == '2-confirmed' \
                and n.sample_id.state in self.WORK_STATES

        # A digest is kept while it still holds at least one active line.
        kept = self.env['lerm.tech.digest'].sudo()
        stale = self.env['lerm.tech.digest'].sudo()
        for digest in digests:
            lines = notifications.filtered(lambda n: n.digest_id == digest)
            if any(_is_active(n) for n in lines):
                kept |= digest
            else:
                stale |= digest
        if stale:
            stale.write({'state': '2-seen'})
        active = notifications.filtered(
            lambda n: n.digest_id in kept and _is_active(n))
        return kept, active

    @api.model
    def _new_work_payload(self):
        digests = self._pending_digests(types=['1-new_work'])
        digests, notifications = self._active_digest_data(digests)
        samples = notifications.mapped('sample_id')
        return {
            'pending_count': len(samples),
            'digest_ids': digests.ids,
            'samples': [self._row(s)
                        for s in samples.sorted('kes_no')],
        }

    @api.model
    def _due_payload(self):
        """Aggregate pending due-tomorrow/due-today digests, one row per sample
        with the message matching that sample's pending notification type."""
        digests = self._pending_digests(
            types=['2-due_tomorrow', '2-due_today'])
        digests, notifications = self._active_digest_data(digests)
        samples = notifications.mapped('sample_id')
        rows = []
        for sample in samples.sorted('kes_no'):
            line_notifs = notifications.filtered(
                lambda n: n.sample_id.id == sample.id)
            # A sample may carry both types; prefer the most urgent (today).
            n_type = '2-due_today' if any(
                n.notification_type == '2-due_today' for n in line_notifs) \
                else '2-due_tomorrow'
            rows.append(self._row(sample, due_type=n_type))
        return {
            'due_pending_count': len(samples),
            'due_digest_ids': digests.ids,
            'due_samples': rows,
        }

    @api.model
    def check(self):
        eligible = self._is_technician()
        new_enabled = self._is_enabled() and eligible
        due_enabled = self._is_due_enabled() and eligible
        result = {
            'enabled': new_enabled,
            'eligible': eligible,
            'active': eligible and (new_enabled or due_enabled),
            'next_check_seconds': self._next_check_seconds(),
            'overdue_blocked': False,
            'overdue': [],
            'due_pending_count': 0,
            'due_digest_ids': [],
            'due_samples': [],
            'pending_count': 0,
            'digest_ids': [],
            'samples': [],
        }
        if not (new_enabled or due_enabled):
            return result

        if due_enabled:
            # Overdue block is derived live and takes priority.
            overdue = self._get_overdue_jobs(self.env.user.id)
            if overdue:
                result['overdue_blocked'] = True
                result['overdue'] = [self._row(s, due_type='2-overdue')
                                     for s in overdue.sorted('kes_no')]
                return result
            result.update(self._due_payload())
        if new_enabled:
            result.update(self._new_work_payload())
        return result

    @api.model
    def mark_seen(self, digest_ids):
        if not digest_ids:
            return
        if isinstance(digest_ids, int):
            digest_ids = [digest_ids]
        digests = self.env['lerm.tech.digest'].sudo().search([
            ('id', 'in', list(digest_ids)),
            ('technician_id', '=', self.env.user.id),
            ('state', '=', '1-pending'),
        ])
        digests.write({'state': '2-seen'})

    @api.model
    def get_sample_action(self, sample_id):
        sample = self.env['lerm.srf.sample'].sudo().browse(sample_id)
        if not sample.exists():
            return False
        return {
            'name': 'Sample',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'lerm.srf.sample',
            'res_id': sample.id,
            'target': 'current',
        }

    @api.model
    def _next_check_seconds(self):
        """Seconds until the next poll. Poll every 30s while inside a new-work
        window, the morning window, or shortly after one (catch a late cron).
        Otherwise sleep until the nearest upcoming enabled window."""
        now = self._now_local()
        times = []
        if self._is_enabled():
            times += self._get_window_times()
        if self._is_due_enabled():
            times += [self._get_morning_time()]
        if not times:
            return 3600
        starts = self._window_start_datetimes(now, minutes_only=times)
        for start in starts:
            if start <= now <= start + timedelta(minutes=5):
                return 30
        future = [s for s in starts if s > now]
        if not future:
            return 3600
        seconds = int((min(future) - now).total_seconds())
        return max(60, seconds)
