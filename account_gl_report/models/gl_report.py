import json
from datetime import datetime

from odoo import api, fields, models, _
from odoo.tools import date_utils


class AccountGLReport(models.TransientModel):
    _name = 'account.gl.report'
    _description = 'General Ledger Report Wizard'

    account_id = fields.Many2one('account.account', string='Account',
                                 required=True, index=True)
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    date_filter = fields.Selection([
        ('today', 'Today'),
        ('yesterday', 'Yesterday'),
        ('this_week', 'This Week'),
        ('last_week', 'Last Week'),
        ('this_month', 'This Month'),
        ('last_month', 'Last Month'),
        ('quarter', 'Quarter'),
        ('fiscal_year', 'Fiscal Year'),
        ('custom', 'Custom Range'),
    ], string='Date Range', default='this_month')
    journal_ids = fields.Many2many('account.journal', string='Journals')
    partner_id = fields.Many2one('res.partner', string='Partner')
    analytic_account_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account')
    target_move = fields.Selection([
        ('posted', 'Posted'),
        ('draft', 'Draft'),
        ('all', 'All'),
    ], string='Target Moves', default='all')
    currency_id = fields.Many2one('res.currency', string='Currency')
    group_by = fields.Selection([
        ('none', 'None'),
        ('journal', 'Journal'),
        ('month', 'Month'),
        ('partner', 'Partner'),
        ('account', 'Account'),
        ('analytic_account', 'Analytic Account'),
    ], string='Group By', default='none')
    show_initial_balance = fields.Boolean(
        string='Include Initial Balances', default=True)
    search_term = fields.Char(string='Search')
    sort_by = fields.Char(string='Sort Field', default='date')
    sort_order = fields.Selection([
        ('asc', 'Ascending'),
        ('desc', 'Descending'),
    ], string='Sort Order', default='asc')
    limit = fields.Integer(string='Page Size', default=50)
    offset = fields.Integer(string='Offset', default=0)

    def _build_query(self, params):
        cr = self.env.cr
        date_from, date_to = params.get('date_from'), params.get('date_to')
        account_id = params.get('account_id')
        journal_ids = params.get('journal_ids', [])
        partner_id = params.get('partner_id')
        analytic_id = params.get('analytic_account_id')
        target_move = params.get('target_move', 'all')
        search_term = params.get('search_term', '')
        sort_by = params.get('sort_by', 'date')
        sort_order = params.get('sort_order', 'asc')
        offset = params.get('offset', 0)
        limit = params.get('limit', 50)
        show_initial = params.get('show_initial_balance', True)

        conditions = ['l.account_id = %s']
        sql_params = [account_id]

        if date_from:
            conditions.append('l.date >= %s')
            sql_params.append(date_from)
        if date_to:
            conditions.append('l.date <= %s')
            sql_params.append(date_to)
        if journal_ids:
            conditions.append('l.journal_id = ANY(%s)')
            sql_params.append(journal_ids)
        if partner_id:
            conditions.append('l.partner_id = %s')
            sql_params.append(partner_id)
        if analytic_id:
            conditions.append("l.analytic_distribution ? %s")
            sql_params.append(str(analytic_id))
        if target_move == 'posted':
            conditions.append("m.state = 'posted'")
        elif target_move == 'draft':
            conditions.append("m.state = 'draft'")
        if search_term:
            conditions.append(
                "(l.name ILIKE %s OR l.ref ILIKE %s OR p.name ILIKE %s OR j.code ILIKE %s)")
            like = f'%{search_term}%'
            sql_params.extend([like, like, like, like])

        where_clause = ' AND '.join(conditions)

        sort_map = {
            'date': 'l.date',
            'journal': 'j.code',
            'partner': 'p.name',
            'move': 'm.name',
            'debit': 'l.debit',
            'credit': 'l.credit',
            'balance': 'l.balance',
        }
        sort_field = sort_map.get(sort_by, 'l.date')
        sort_dir = 'DESC NULLS LAST' if sort_order == 'desc' else 'ASC NULLS LAST'

        analytic_join = """
            LEFT JOIN LATERAL (
                SELECT aa.id AS analytic_id, aa.name AS analytic_name
                FROM jsonb_object_keys(l.analytic_distribution) AS jkey(acc_id)
                JOIN account_analytic_account aa ON aa.id::text = jkey.acc_id
                LIMIT 1
            ) analytic ON TRUE
        """

        user_join = """
            LEFT JOIN res_users cu ON l.create_uid = cu.id
            LEFT JOIN res_partner cup ON cu.partner_id = cup.id
            LEFT JOIN res_users wu ON l.write_uid = wu.id
            LEFT JOIN res_partner wup ON wu.partner_id = wup.id
        """

        count_sql = f"""
            SELECT COUNT(*) as total
            FROM account_move_line l
            JOIN account_move m ON l.move_id = m.id
            LEFT JOIN res_partner p ON l.partner_id = p.id
            LEFT JOIN account_journal j ON l.journal_id = j.id
            WHERE {where_clause}
        """
        cr.execute(count_sql, sql_params)
        total_records = cr.dictfetchone()['total']

        data_sql = f"""
            SELECT
                l.id,
                l.date,
                l.name AS label,
                l.ref,
                COALESCE(l.debit, 0.0) AS debit,
                COALESCE(l.credit, 0.0) AS credit,
                COALESCE(l.balance, 0.0) AS balance,
                l.amount_currency,
                l.currency_id,
                l.quantity,
                l.partner_id,
                p.name AS partner_name,
                j.code AS journal_code,
                j.name AS journal_name,
                m.name AS move_name,
                m.id AS move_id,
                m.state,
                m.move_type,
                analytic.analytic_name,
                analytic.analytic_id,
                l.account_id,
                acc.code AS account_code,
                acc.name AS account_name,
                l.create_uid,
                l.create_date,
                l.write_uid,
                l.write_date,
                cup.name AS create_user_name,
                wup.name AS write_user_name
            FROM account_move_line l
            JOIN account_move m ON l.move_id = m.id
            JOIN account_account acc ON l.account_id = acc.id
            LEFT JOIN res_partner p ON l.partner_id = p.id
            LEFT JOIN account_journal j ON l.journal_id = j.id
            {analytic_join}
            {user_join}
            WHERE {where_clause}
            ORDER BY {sort_field} {sort_dir}, l.id
            OFFSET %s LIMIT %s
        """
        sql_params_ext = sql_params + [offset, limit]
        cr.execute(data_sql, sql_params_ext)
        records = cr.dictfetchall()

        window_sql = f"""
            SELECT
                COALESCE(SUM(l.debit), 0.0) AS total_debit,
                COALESCE(SUM(l.credit), 0.0) AS total_credit,
                COALESCE(SUM(l.balance), 0.0) AS closing_balance
            FROM account_move_line l
            JOIN account_move m ON l.move_id = m.id
            LEFT JOIN res_partner p ON l.partner_id = p.id
            LEFT JOIN account_journal j ON l.journal_id = j.id
            WHERE {where_clause}
        """
        cr.execute(window_sql, sql_params)
        totals = cr.dictfetchone()

        opening_balance = 0.0
        if show_initial and date_from:
            init_sql = f"""
                SELECT COALESCE(SUM(l.balance), 0.0) AS opening
                FROM account_move_line l
                JOIN account_move m ON l.move_id = m.id
                WHERE l.account_id = %s AND l.date < %s
            """
            init_params = [account_id, date_from]
            if target_move == 'posted':
                init_sql += " AND m.state = 'posted'"
            elif target_move == 'draft':
                init_sql += " AND m.state = 'draft'"
            cr.execute(init_sql, init_params)
            opening_balance = cr.dictfetchone()['opening']

        running = opening_balance
        for rec in records:
            running += rec['debit'] - rec['credit']
            rec['running_balance'] = running

        return {
            'records': records,
            'total_records': total_records,
            'summary': {
                'opening_balance': opening_balance,
                'opening_balance_positive': opening_balance if opening_balance > 0 else 0,
                'opening_balance_negative': -opening_balance if opening_balance < 0 else 0,
                'total_debit': totals['total_debit'],
                'total_credit': totals['total_credit'],
                'closing_balance': totals['closing_balance'],
                'transaction_count': total_records,
            },
        }

    def get_grouped_data(self, params):
        group_by = params.get('group_by', 'none')
        if group_by == 'none':
            return self._build_query(params)

        cr = self.env.cr
        date_from, date_to = params.get('date_from'), params.get('date_to')
        account_id = params.get('account_id')
        journal_ids = params.get('journal_ids', [])
        partner_id = params.get('partner_id')
        analytic_id = params.get('analytic_account_id')
        target_move = params.get('target_move', 'all')
        search_term = params.get('search_term', '')
        show_initial = params.get('show_initial_balance', True)

        conditions = ['l.account_id = %s']
        sql_params = [account_id]
        if date_from:
            conditions.append('l.date >= %s')
            sql_params.append(date_from)
        if date_to:
            conditions.append('l.date <= %s')
            sql_params.append(date_to)
        if journal_ids:
            conditions.append('l.journal_id = ANY(%s)')
            sql_params.append(journal_ids)
        if partner_id:
            conditions.append('l.partner_id = %s')
            sql_params.append(partner_id)
        if analytic_id:
            conditions.append("l.analytic_distribution ? %s")
            sql_params.append(str(analytic_id))
        if target_move == 'posted':
            conditions.append("m.state = 'posted'")
        elif target_move == 'draft':
            conditions.append("m.state = 'draft'")
        if search_term:
            conditions.append(
                "(l.name ILIKE %s OR l.ref ILIKE %s OR p.name ILIKE %s OR j.code ILIKE %s)")
            like = f'%{search_term}%'
            sql_params.extend([like, like, like, like])

        where_clause = ' AND '.join(conditions)

        analytic_join = """
            LEFT JOIN LATERAL (
                SELECT aa.id AS analytic_id, aa.name AS analytic_name
                FROM jsonb_object_keys(l.analytic_distribution) AS jkey(acc_id)
                JOIN account_analytic_account aa ON aa.id::text = jkey.acc_id
                LIMIT 1
            ) analytic ON TRUE
        """

        group_field_map = {
            'month': "to_char(l.date, 'YYYY-MM')",
            'journal': 'j.code',
            'partner': 'p.name',
            'account': 'acc.code',
            'analytic_account': 'analytic.analytic_name',
        }
        group_col = group_field_map.get(group_by, 'j.code')
        group_label = f"COALESCE({group_col}, 'Undefined')"

        group_sql = f"""
            SELECT {group_label} AS group_key,
                   COUNT(*) AS count,
                   COALESCE(SUM(l.debit), 0.0) AS total_debit,
                   COALESCE(SUM(l.credit), 0.0) AS total_credit,
                   COALESCE(SUM(l.balance), 0.0) AS total_balance
            FROM account_move_line l
            JOIN account_move m ON l.move_id = m.id
            LEFT JOIN res_partner p ON l.partner_id = p.id
            LEFT JOIN account_journal j ON l.journal_id = j.id
            {analytic_join}
            LEFT JOIN account_account acc ON l.account_id = acc.id
            WHERE {where_clause}
            GROUP BY group_key
            ORDER BY group_key
        """
        cr.execute(group_sql, sql_params)
        groups = cr.dictfetchall()

        opening_balance = 0.0
        if show_initial and date_from:
            init_sql = f"""
                SELECT COALESCE(SUM(l.balance), 0.0) AS opening
                FROM account_move_line l
                JOIN account_move m ON l.move_id = m.id
                WHERE l.account_id = %s AND l.date < %s
            """
            init_params = [account_id, date_from]
            if target_move == 'posted':
                init_sql += " AND m.state = 'posted'"
            elif target_move == 'draft':
                init_sql += " AND m.state = 'draft'"
            cr.execute(init_sql, init_params)
            opening_balance = cr.dictfetchone()['opening']

        return {
            'groups': groups,
            'summary': {
                'opening_balance': opening_balance,
                'total_debit': sum(g['total_debit'] for g in groups),
                'total_credit': sum(g['total_credit'] for g in groups),
                'closing_balance': opening_balance + sum(
                    g['total_debit'] - g['total_credit'] for g in groups),
                'transaction_count': sum(g['count'] for g in groups),
            },
        }

    def get_line_details(self, line_id):
        cr = self.env.cr
        analytic_join = """
            LEFT JOIN LATERAL (
                SELECT aa.id AS analytic_id, aa.name AS analytic_name
                FROM jsonb_object_keys(l.analytic_distribution) AS jkey(acc_id)
                JOIN account_analytic_account aa ON aa.id::text = jkey.acc_id
                LIMIT 1
            ) analytic ON TRUE
        """
        user_join = """
            LEFT JOIN res_users cu ON l.create_uid = cu.id
            LEFT JOIN res_partner cup ON cu.partner_id = cup.id
            LEFT JOIN res_users wu ON l.write_uid = wu.id
            LEFT JOIN res_partner wup ON wu.partner_id = wup.id
        """
        sql = f"""
            SELECT
                l.id, l.name AS label, l.ref,
                COALESCE(l.debit, 0.0) AS debit,
                COALESCE(l.credit, 0.0) AS credit,
                COALESCE(l.balance, 0.0) AS balance,
                l.date, l.quantity,
                l.partner_id, p.name AS partner_name,
                l.account_id, acc.code AS account_code, acc.name AS account_name,
                l.journal_id, j.code AS journal_code, j.name AS journal_name,
                analytic.analytic_id, analytic.analytic_name,
                l.tax_line_id, t.name AS tax_name, t.amount AS tax_amount,
                l.tax_ids,
                l.move_id, m.name AS move_name, m.ref AS move_ref, m.state,
                l.product_id, pr.name AS product_name,
                l.create_uid, cup.name AS create_user_name, l.create_date,
                l.write_uid, wup.name AS write_user_name, l.write_date
            FROM account_move_line l
            JOIN account_move m ON l.move_id = m.id
            LEFT JOIN account_account acc ON l.account_id = acc.id
            LEFT JOIN res_partner p ON l.partner_id = p.id
            LEFT JOIN account_journal j ON l.journal_id = j.id
            {analytic_join}
            {user_join}
            LEFT JOIN account_tax t ON l.tax_line_id = t.id
            LEFT JOIN product_product pr ON l.product_id = pr.id
            WHERE l.id = %s
        """
        cr.execute(sql, [line_id])
        return cr.dictfetchone()

    def get_attachments(self, move_id):
        return self.env['ir.attachment'].search_read(
            [('res_model', '=', 'account.move'), ('res_id', '=', move_id)],
            ['name', 'id', 'mimetype', 'file_size', 'create_date'],
            order='create_date DESC')
