# -*- coding: utf-8 -*-
# Controller for the Lab Control Center dashboard.
from datetime import date, timedelta

from odoo import http
from odoo.http import request

import logging

_logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Metric definitions (single source of truth for backend + drill-downs)
# ---------------------------------------------------------------------------
PIPELINE_STATES = [
    '1-allotment_pending',
    '7-partially-alloted',
    '2-alloted',
    '7-calculated',
    '3-pending_verification',
    '5-pending_approval',
]

WORK_STATES = ['2-alloted', '7-calculated']

AT_RISK_STATES = ['1-allotment_pending', '7-partially-alloted']

# pipeline funnel stages (label -> sample state)
PIPELINE_STAGES = [
    {'key': 'allotted', 'label': 'Allotted', 'state': '2-alloted'},
    {'key': 'testing', 'label': 'Testing', 'state': '7-calculated'},
    {'key': 'verification', 'label': 'Verification', 'state': '3-pending_verification'},
    {'key': 'approval', 'label': 'Approval', 'state': '5-pending_approval'},
]

STATE_STAGE_LABELS = {
    '1-allotment_pending': 'Assignment Pending',
    '7-partially-alloted': 'Partially Allotted',
    '2-alloted': 'Allotted',
    '7-calculated': 'Testing',
    '3-pending_verification': 'Verification',
    '5-pending_approval': 'Approval',
}

# Sample aging buckets keyed on days remaining until report due date.
AGING_BUCKETS = [
    {'key': '0-1', 'label': '0-1 days', 'lo': 0, 'hi': 1},
    {'key': '2-3', 'label': '2-3 days', 'lo': 2, 'hi': 3},
    {'key': '4-7', 'label': '4-7 days', 'lo': 4, 'hi': 7},
    {'key': '8+', 'label': '8+ days', 'lo': 8, 'hi': None},
]

ROLE_LABELS = {
    'management': 'Management',
    'hod': 'HOD',
    'none': '',
}


class LabControlCenter(http.Controller):

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    @staticmethod
    def _today():
        return date.today()

    def _param(self, key, default):
        return request.env['ir.config_parameter'].sudo().get_param(key, default)

    def _role(self):
        user = request.env.user
        try:
            if user.has_group('lerm_civil.kes_admin_access_group'):
                return 'management'
            if user.has_group('lerm_civil.kes_hod_access_group'):
                return 'hod'
        except Exception:
            _logger.exception('Error resolving role for user %s', user.id)
        return 'none'

    def _hod_discipline_ids(self):
        return request.env['lerm_civil.discipline'].sudo().search(
            [('hod', '=', request.env.user.id)]).ids

    @staticmethod
    def _val(value, default):
        if value is None:
            return default
        return value

    def _parse_date(self, value):
        if not value:
            return self._today()
        try:
            return date.fromisoformat(str(value))
        except (TypeError, ValueError):
            return self._today()

    def _clean(self, value):
        value = self._val(value, '')
        return value if value not in ('', 'ALL') else None

    def _at_risk_ahead(self):
        value = self._param('lab_control_center.at_risk_ahead_days', '1')
        try:
            return int(value)
        except (TypeError, ValueError):
            return 1

    def _priority_limit(self):
        value = self._param('lab_control_center.priority_limit', '15')
        try:
            return max(1, int(value))
        except (TypeError, ValueError):
            return 15

    # ------------------------------------------------------------------ #
    # Domain building (scope + filters + search) shared by data & drilldown
    # ------------------------------------------------------------------ #
    def _base_domain(self, role, discipline_id=None, lab_id=None,
                     company_id=None, search=None):
        domain = [('state', 'in', PIPELINE_STATES)]

        if role == 'hod':
            disc_ids = self._hod_discipline_ids()
            domain.append(('discipline_id', 'in', disc_ids))

        if discipline_id:
            domain.append(('discipline_id', '=', int(discipline_id)))
        if lab_id:
            domain.append(('lab_location', '=', int(lab_id)))
        if company_id:
            domain.append(('lab_location.company_id', '=', int(company_id)))

        search = (search or '').strip()
        if search:
            search_domain = [
                ('sample_no', 'ilike', search),
                ('kes_no', 'ilike', search),
                ('ulr_no', 'ilike', search),
                ('srf_id.srf_id', 'ilike', search),
                ('material_id.name', 'ilike', search),
                ('material_id_lab_name', 'ilike', search),
                ('customer_id.name', 'ilike', search),
            ]
            domain += ['|'] * (len(search_domain) - 1) + search_domain
        return domain

    def _technician_ids(self, sample):
        uids = set()
        if sample.technicians:
            uids.add(sample.technicians.id)
        eln = sample.eln_id
        if eln:
            if eln.technician:
                uids.add(eln.technician.id)
            if eln.technician_ids:
                uids.update(eln.technician_ids.ids)
            if eln.parameters_result:
                for pr in eln.parameters_result:
                    if pr.technician:
                        uids.add(pr.technician.id)
        return uids

    def _user_names(self, uids):
        users = request.env['res.users'].sudo().search(
            [('id', 'in', list(uids))])
        return {u.id: u.name for u in users}

    # ------------------------------------------------------------------ #
    # Aggregation
    # ------------------------------------------------------------------ #
    def _fetch(self, role, kw):
        as_of = self._parse_date(kw.get('as_of'))
        domain = self._base_domain(
            role,
            discipline_id=self._clean(kw.get('discipline_id')),
            lab_id=self._clean(kw.get('lab_id')),
            company_id=self._clean(kw.get('company_id')),
            search=kw.get('search'),
        )
        return domain, as_of, request.env['lerm.srf.sample'].sudo().search(domain)

    # ------------------------------------------------------------------ #
    # Routes
    # ------------------------------------------------------------------ #
    @http.route('/labcc/data', type='json', auth='user', methods=['POST'])
    def get_data(self, **kw):
        role = self._role()
        domain, as_of, samples = self._fetch(role, kw)

        total = len(samples)
        overdue = due_today = testing = approval = 0
        at_risk = 0
        ahead = self._at_risk_ahead()
        aging_counter = {b['key']: 0 for b in AGING_BUCKETS}
        pipeline_counter = {s['key']: 0 for s in PIPELINE_STAGES}
        flagged = []  # (sample, flag)

        for s in samples:
            st = s.state
            if st == '7-calculated':
                testing += 1
            elif st == '5-pending_approval':
                approval += 1
            for stage in PIPELINE_STAGES:
                if st == stage['state']:
                    pipeline_counter[stage['key']] += 1
                    break

            due = s.report_due_date
            if not due:
                continue
            delta = (due - as_of).days
            if delta < 0:
                overdue += 1
                flagged.append((s, 'overdue'))
            elif delta == 0:
                due_today += 1
                flagged.append((s, 'due_today'))
            if st in AT_RISK_STATES and delta == ahead:
                at_risk += 1
                flagged.append((s, 'at_risk'))

            if delta >= 0:
                for bucket in AGING_BUCKETS:
                    if bucket['hi'] is None:
                        in_range = delta >= bucket['lo']
                    else:
                        in_range = bucket['lo'] <= delta <= bucket['hi']
                    if in_range:
                        aging_counter[bucket['key']] += 1
                        break

        # technician workload over samples that are actually in test
        tech_counter = {}
        work_samples = samples.filtered(lambda s: s.state in WORK_STATES)
        for s in work_samples:
            for uid in self._technician_ids(s):
                tech_counter[uid] = tech_counter.get(uid, 0) + 1
        names = self._user_names(tech_counter.keys())
        workload = sorted(
            ([{'technician_id': uid, 'name': names.get(uid, 'Technician'),
               'count': cnt} for uid, cnt in tech_counter.items()]),
            key=lambda r: r['count'], reverse=True)[:10]

        # priority list (overdue, due today, at risk) sorted by due date
        flag_rank = {'overdue': 0, 'due_today': 1, 'at_risk': 2}
        priority_rows = []
        for s, flag in flagged:
            techs = self._technician_ids(s)
            names_map = self._user_names(techs) if techs else {}
            tech_name = names_map.get(next(iter(techs)), '') if techs else ''
            priority_rows.append({
                'sample_id': s.id,
                'sample_ref': s.sample_no or s.kes_no,
                'material': s.material_id_lab_name or (
                    s.material_id.name if s.material_id else ''),
                'customer': s.customer_id.name or '',
                'technician': tech_name,
                'stage': STATE_STAGE_LABELS.get(s.state, s.state),
                'due': s.report_due_date.isoformat() if s.report_due_date else False,
                'flag': flag,
            })
        priority_rows.sort(key=lambda r: (flag_rank.get(r['flag'], 3), r['due']))
        priority_rows = priority_rows[:self._priority_limit()]

        return {
            'role': role,
            'role_label': ROLE_LABELS.get(role, ''),
            'as_of': as_of.isoformat(),
            'kpis': {
                'total': total,
                'overdue': overdue,
                'due_today': due_today,
                'testing': testing,
                'approval': approval,
            },
            'attention': {
                'overdue': overdue,
                'due_today': due_today,
                'at_risk': at_risk,
                'approval': approval,
            },
            'pipeline': [
                {'key': stage['key'], 'label': stage['label'],
                 'count': pipeline_counter[stage['key']]}
                for stage in PIPELINE_STAGES
            ],
            'workload': workload,
            'aging': [
                {'key': b['key'], 'label': b['label'],
                 'count': aging_counter[b['key']]}
                for b in AGING_BUCKETS
            ],
            'priority': priority_rows,
            'priority_total': len(flagged),
        }

    @http.route('/labcc/options', type='json', auth='user', methods=['POST'])
    def get_options(self, **kw):
        role = self._role()

        companies = []
        labs = []
        disciplines = []
        disc_ids = []

        if role != 'none':
            if role == 'management':
                for comp in request.env['res.company'].sudo().search([]):
                    companies.append({'id': comp.id, 'name': comp.name})
                for lab in request.env['lerm.lab.master'].sudo().search([]):
                    labs.append({'id': lab.id, 'name': lab.lab_name,
                                 'company_id': lab.company_id.id})
                disc_ids = None  # all
            else:
                disc_ids = self._hod_discipline_ids()

            disc_domain = [('id', 'in', disc_ids)] if disc_ids is not None \
                else []
            for disc in request.env['lerm_civil.discipline'].sudo().search(
                    disc_domain):
                disciplines.append({'id': disc.id, 'name': disc.discipline})

        scope_label = 'All labs & disciplines' if role == 'management' \
            else 'My disciplines only'
        return {
            'role': role,
            'role_label': ROLE_LABELS.get(role, ''),
            'scope_label': scope_label,
            'companies': companies,
            'labs': labs,
            'disciplines': disciplines,
        }

    # ------------------------------------------------------------------ #
    # Drill-down domain helper (kept in sync with the aggregations above)
    # ------------------------------------------------------------------ #
    @http.route('/labcc/domain', type='json', auth='user', methods=['POST'])
    def get_drill_domain(self, **kw):
        role = self._role()
        as_of = self._parse_date(kw.get('as_of'))
        domain = self._base_domain(
            role,
            discipline_id=self._clean(kw.get('discipline_id')),
            lab_id=self._clean(kw.get('lab_id')),
            company_id=self._clean(kw.get('company_id')),
            search=kw.get('search'),
        )
        kind = kw.get('kind') or 'total'
        ahead = self._at_risk_ahead()
        extra = kw.get('extra') or {}

        name = 'Samples'
        context = {}

        if kind == 'total':
            name = 'All Pipeline Samples'
        elif kind == 'overdue':
            name = 'Overdue Samples'
            domain.append(('report_due_date', '<', as_of))
        elif kind == 'due_today':
            name = 'Samples Due Today'
            domain.append(('report_due_date', '=', as_of))
        elif kind == 'at_risk':
            name = 'At Risk - Unallotted Due Soon'
            domain.append(('state', 'in', AT_RISK_STATES))
            domain.append(('report_due_date', '=', as_of + timedelta(days=ahead)))
        elif kind == 'testing':
            name = 'In Test Samples'
            domain.append(('state', '=', '7-calculated'))
        elif kind == 'approval':
            name = 'Pending Approval Samples'
            domain.append(('state', '=', '5-pending_approval'))
        elif kind == 'verification':
            name = 'Pending Verification Samples'
            domain.append(('state', '=', '3-pending_verification'))
        elif kind == 'allotted':
            name = 'Allotted Samples'
            domain.append(('state', '=', '2-alloted'))
        elif kind == 'aging':
            bucket = None
            for b in AGING_BUCKETS:
                if b['key'] == extra.get('bucket'):
                    bucket = b
                    break
            if bucket is not None:
                name = 'Samples Due in %s' % bucket['label']
                domain.append(('report_due_date', '>=', as_of + timedelta(days=bucket['lo'])))
                if bucket['hi'] is not None:
                    domain.append(('report_due_date', '<=', as_of + timedelta(days=bucket['hi'])))
            else:
                name = 'Samples by Due Date'
                domain.append(('report_due_date', '!=', False))
        elif kind == 'workload':
            tech = extra.get('technician_id')
            name = 'Technician Workload'
            if tech:
                domain += [
                    '&',
                    ('state', 'in', WORK_STATES),
                    '|', '|', '|',
                    ('technicians', '=', int(tech)),
                    ('eln_id.technician', '=', int(tech)),
                    ('eln_id.technician_ids', 'in', [int(tech)]),
                    ('eln_id.parameters_result.technician', '=', int(tech)),
                ]
                context = {'group_by': ['state']}
        elif kind == 'priority':
            name = 'Priority Samples'
            domain += [
                '|',
                ('report_due_date', '<', as_of),
                '|',
                ('report_due_date', '=', as_of),
                '&',
                ('state', 'in', AT_RISK_STATES),
                ('report_due_date', '=', as_of + timedelta(days=ahead)),
            ]

        return {'name': name, 'domain': domain, 'context': context}
