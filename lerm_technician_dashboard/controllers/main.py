import logging
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

DAY_DUE_LABELS = {
    'overdue': 'Overdue',
    'due_today': 'Due Today',
    'due_tomorrow': 'Due Tomorrow',
    'later': 'Upcoming',
}

DAY_DUE_BADGES = {
    'overdue': 'OVERDUE',
    'due_today': 'DUE TODAY',
    'due_tomorrow': 'DUE TOMORROW',
    'later': None,
}


class TechnicianDashboard(http.Controller):

    # ---- workflow semantics over lerm.eln (selection values are prefix-numbered) ----
    # lerm.eln carries the real technician assignment (technician / technician_ids /
    # parameters_result.technician), so a work item == one ELN (worksheet).
    WORK_STATES = ['5-alloted', '4-rejected', '1-draft']   # open / needs my action
    TODO_STATES = ['5-alloted', '4-rejected']              # not started yet
    WAIT_STATES = ['2-confirm']                            # submitted, in check
    COMPLETED_STATE = '3-approved'
    CANCELLED_STATE = '5-cancelled'

    STATE_LABELS = {
        '5-alloted': 'Allotted',
        '4-rejected': 'Rejected',
        '1-draft': 'Testing Started',
        '2-confirm': 'In Check',
        '3-approved': 'Approved',
        '5-cancelled': 'Cancelled',
    }

    WAIT_LABELS = {
        '3-pending_verification': 'Verification',
        '5-pending_approval': 'Approval',
    }

    STAGE_LABELS = {
        'allotted': 'Allotted',
        'testing': 'Testing',
        'verification': 'Verification',
        'approval': 'Approval',
        'approved': 'Approved',
    }

    HORIZON_LABELS = {
        'overdue': 'Overdue',
        'today': 'Today',
        'next_7': 'Next 7 Days',
        'next_14': 'Next 14 Days',
        'next_30': 'Next 30 Days',
    }

    # =========================================================================
    # helpers
    # =========================================================================

    def _uid(self):
        return request.env.user.id

    def _user_tz(self):
        tz_name = request.env.user.tz
        try:
            return ZoneInfo(tz_name) if tz_name else ZoneInfo('UTC')
        except Exception:
            return ZoneInfo('UTC')

    def _today(self):
        return datetime.now(self._user_tz()).date()

    def _eln_model(self):
        return request.env['lerm.eln'].sudo()

    def _my_domain(self):
        """ELNs assigned to the current user through any ELN assignment field."""
        uid = self._uid()
        return ['|', '|',
                ('technician', '=', uid),
                ('technician_ids', 'in', [uid]),
                ('parameters_result.technician', '=', uid),
                ('state', '!=', self.CANCELLED_STATE),
                ('active', '=', True)]

    def _due_date(self, eln):
        sample = eln.sample_id
        return sample.report_due_date if sample else False

    def _due_bucket(self, due_date, today):
        if not due_date:
            return None
        if due_date < today:
            return 'overdue'
        if due_date == today:
            return 'due_today'
        if due_date == today + timedelta(days=1):
            return 'due_tomorrow'
        return 'later'

    @staticmethod
    def _date_iso(value):
        return value.isoformat() if value else None

    def _row(self, eln, today):
        sample = eln.sample_id
        due_date = self._due_date(eln)
        bucket = self._due_bucket(due_date, today)
        return {
            'id': eln.id,
            'sample_id': sample.id if sample else False,
            'ref': eln.kes_no or (sample.kes_no if sample else '') or '',
            'eln_name': eln.eln_id or '',
            'customer': (sample.customer_id.display_name if sample else '') or '',
            'material': eln.material.display_name or '',
            'discipline': eln.discipline.display_name or '',
            'test_type': (eln.group.display_name or eln.discipline.display_name
                          or eln.material.display_name or ''),
            'department': eln.department_id or (sample.department_id if sample else '') or '',
            'state': eln.state,
            'state_label': self.STATE_LABELS.get(eln.state, eln.state),
            'due_date': self._date_iso(due_date),
            'due_bucket': bucket,
            'due_label': DAY_DUE_LABELS.get(bucket) if bucket else None,
            'due_badge': DAY_DUE_BADGES.get(bucket) if bucket else None,
            'eln_id': eln.id,
            'test_started': bool(eln.test_started),
        }

    def _wait_label(self, eln):
        sample = eln.sample_id
        if sample:
            return self.WAIT_LABELS.get(sample.state, 'In Check')
        return 'In Check'

    @staticmethod
    def _fmt_wait(stage_updated_at, now_dt):
        if not stage_updated_at:
            return 'Just now'
        delta = now_dt - stage_updated_at
        total_seconds = int(delta.total_seconds())
        if total_seconds < 0:
            total_seconds = 0
        hours = total_seconds // 3600
        if hours < 1:
            minutes = max(1, total_seconds // 60)
            return '%dm' % minutes
        if hours < 24:
            return '%dh' % hours
        days = hours // 24
        rem_hours = hours % 24
        if rem_hours:
            return '%dd %dh' % (days, rem_hours)
        return '%dd' % days

    def _sort_working(self, records, today):
        """Open ELNs ordered by urgency: overdue first, then due date asc."""
        bucket_rank = {'overdue': 0, 'due_today': 1, 'due_tomorrow': 2, 'later': 3, None: 4}

        def key(eln):
            bucket = self._due_bucket(self._due_date(eln), today)
            due = self._due_date(eln) or date.max
            return (bucket_rank.get(bucket, 4), due, eln.id)
        return sorted(records, key=key)

    def _stage_of(self, eln):
        """Map an ELN to a matrix row key."""
        state = eln.state
        if state == self.COMPLETED_STATE:
            return 'approved'
        if state == '2-confirm':
            sample_state = eln.sample_id.state if eln.sample_id else False
            if sample_state == '5-pending_approval':
                return 'approval'
            return 'verification'
        if state == '1-draft' and eln.test_started:
            return 'testing'
        # 5-alloted / 4-rejected / untouched 1-draft
        return 'allotted'

    def _horizon_counts(self, records, today):
        """Cumulative counts per due-date horizon column."""
        limits = {
            'overdue': today - timedelta(days=1),
            'today': today,
            'next_7': today + timedelta(days=7),
            'next_14': today + timedelta(days=14),
            'next_30': today + timedelta(days=30),
        }
        counts = {key: 0 for key in limits}
        for eln in records:
            due = self._due_date(eln)
            if not due:
                continue
            for key, limit in limits.items():
                if due <= limit:
                    counts[key] += 1
        return counts

    # =========================================================================
    # routes
    # =========================================================================

    @http.route('/technician_dashboard/data', type='json', auth='user', methods=['POST'])
    def get_data(self):
        user = request.env.user
        today = self._today()
        now_dt = datetime.utcnow()  # naive UTC, same as odoo datetime fields

        elns = self._eln_model().search(self._my_domain())

        working = [e for e in elns if e.state in self.WORK_STATES]
        in_progress = [e for e in elns if e.state == '1-draft' and e.test_started]
        waiting = [e for e in elns if e.state in self.WAIT_STATES]
        completed = [e for e in elns if e.state == self.COMPLETED_STATE]

        def count_with(records, bucket):
            return sum(1 for e in records if self._due_bucket(self._due_date(e), today) == bucket)

        # KPIs
        kpi_overdue = count_with(working, 'overdue')
        kpi_due_today = count_with(working, 'due_today')

        # "My Day" scope: OPEN work (still to do) whose due date falls in the
        # overdue / due-today / due-tomorrow window -> consistent with the KPIs.
        day_open = [e for e in working
                    if self._due_date(e) and self._due_date(e) <= today + timedelta(days=1)]

        # progress ring, tied to the same "today" window: finished worksheets
        # whose due date is overdue/today/tomorrow, vs still-open ones in it.
        done_window = [e for e in completed
                       if self._due_date(e) and self._due_date(e) <= today + timedelta(days=1)]
        ring_total = len(done_window) + len(day_open)
        pct = round(len(done_window) * 100.0 / ring_total) if ring_total else 0

        # ---- work list (my worksheets) ----
        def sort_by_due(recs):
            return sorted(recs, key=lambda e: (self._due_date(e) or date.max, e.id or 0))

        eln_rows = [self._row(e, today) for e in sort_by_due(elns)]

        def state_count(state):
            return sum(1 for r in eln_rows if r['state'] == state)

        counts = {
            'all': len(eln_rows),
            'todo': sum(1 for r in eln_rows
                        if r['state'] in self.TODO_STATES
                        or (r['state'] == '1-draft' and not r['test_started'])),
            'in_progress': sum(1 for r in eln_rows
                               if r['state'] == '1-draft' and r['test_started']),
            'waiting': state_count(self.WAIT_STATES[0]),
            'completed': state_count(self.COMPLETED_STATE),
        }
        types = sorted({r['test_type'] for r in eln_rows if r['test_type']})

        needs_action = [self._row(e, today) for e in self._sort_working(working, today)]

        next_action = needs_action[0] if needs_action else False

        waiting_rows = []
        for e in sorted(waiting, key=lambda e: e.stage_updated_at or datetime.min):
            row = self._row(e, today)
            row['wait_label'] = self._wait_label(e)
            row['wait_duration'] = self._fmt_wait(e.stage_updated_at, now_dt)
            waiting_rows.append(row)

        # ---- workload matrix: active work + completed vs due-date horizon ----
        staged = {}
        for e in elns:
            staged.setdefault(self._stage_of(e), []).append(e)

        matrix = {
            'columns': [
                {'key': 'overdue', 'label': 'OVERDUE'},
                {'key': 'today', 'label': 'TODAY'},
                {'key': 'next_7', 'label': 'NEXT 7 DAYS'},
                {'key': 'next_14', 'label': '14 DAYS'},
                {'key': 'next_30', 'label': '30 DAYS'},
            ],
            'rows': [
                {'key': key, 'label': key.upper(),
                 'counts': self._horizon_counts(staged.get(key, []), today)}
                for key in ('allotted', 'testing', 'verification', 'approval')
            ],
            'completed': {
                'key': 'approved', 'label': 'APPROVED',
                'counts': self._horizon_counts(staged.get('approved', []), today),
            },
        }

        return {
            'user': {'id': user.id, 'name': user.name},
            'kpi': {
                'overdue': kpi_overdue,
                'due_today': kpi_due_today,
                'in_progress': len(in_progress),
                'completed': len(completed),
            },
            'day': {
                'overdue': count_with(day_open, 'overdue'),
                'due_today': count_with(day_open, 'due_today'),
                'due_tomorrow': count_with(day_open, 'due_tomorrow'),
                'total': len(day_open),
                'progress_pct': pct,
                'done': len(done_window),
                'remaining': len(day_open),
                'ring_total': ring_total,
            },
            'next_action': next_action,
            'needs_action': needs_action[:10],
            'waiting': waiting_rows[:10],
            'matrix': matrix,
            'samples': {
                'counts': counts,
                'types': types,
                'rows': eln_rows,
            },
        }

    @http.route('/technician_dashboard/list_domain', type='json', auth='user', methods=['POST'])
    def get_list_domain(self, mode='all', stage=None, horizon=None):
        """Return the {name, domain, context} used to open a standard list view."""
        today = self._today()
        elns = self._eln_model().search(self._my_domain())

        def state_filter(recordset, states):
            return [e.id for e in recordset if e.state in states]

        def due_filter(recordset, bucket):
            return [e.id for e in recordset
                    if e.state in self.WORK_STATES
                    and self._due_bucket(self._due_date(e), today) == bucket]

        if mode == 'stage_horizon':
            # clicked a workload-matrix cell: stage row + cumulative due horizon
            horizon_limit = {
                'overdue': today - timedelta(days=1),
                'today': today,
                'next_7': today + timedelta(days=7),
                'next_14': today + timedelta(days=14),
                'next_30': today + timedelta(days=30),
            }.get(horizon)
            ids = []
            for e in elns:
                if self._stage_of(e) != stage:
                    continue
                if horizon_limit is not None:
                    due = self._due_date(e)
                    if not due or due > horizon_limit:
                        continue
                ids.append(e.id)
            name = '%s - %s' % (
                self.STAGE_LABELS.get(stage, stage or 'All'),
                self.HORIZON_LABELS.get(horizon, 'All') if horizon else 'All',
            )
        elif mode == 'overdue':
            ids = due_filter(elns, 'overdue')
            name = 'Overdue Worksheets'
        elif mode == 'needs_action':
            ids = state_filter(elns, self.WORK_STATES)
            name = 'Needs My Action'
        elif mode == 'due_today':
            ids = due_filter(elns, 'due_today')
            name = 'Due Today'
        elif mode == 'due_tomorrow':
            ids = due_filter(elns, 'due_tomorrow')
            name = 'Due Tomorrow'
        elif mode == 'today_work':
            ids = [e.id for e in elns
                   if e.state in self.WORK_STATES and self._due_date(e)
                   and self._due_date(e) <= today + timedelta(days=1)]
            name = "Today's Work"
        elif mode == 'in_progress':
            ids = [e.id for e in elns if e.state == '1-draft' and e.test_started]
            name = 'In Progress'
        elif mode == 'todo':
            ids = [e.id for e in elns
                   if e.state in self.TODO_STATES
                   or (e.state == '1-draft' and not e.test_started)]
            name = 'To Do'
        elif mode == 'waiting':
            ids = state_filter(elns, self.WAIT_STATES)
            name = 'Waiting on Others'
        elif mode == 'completed':
            ids = state_filter(elns, [self.COMPLETED_STATE])
            name = 'Completed'
        else:
            ids = [e.id for e in elns]
            name = 'My Worksheets'

        return {
            'name': name,
            'res_model': 'lerm.eln',
            'domain': [('id', 'in', ids)],
            'views': [[False, 'list'], [False, 'form']],
            'context': {'group_by': ['state']},
        }
