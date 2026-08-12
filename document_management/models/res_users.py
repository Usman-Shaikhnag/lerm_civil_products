# -*- coding: utf-8 -*-

import logging

import odoo
from odoo import models

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = 'res.users'

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        try:
            res = super()._login(db, login, password, user_agent_env)
        except odoo.exceptions.AccessDenied:
            cls._log_login_event(db, login, False, user_agent_env)
            raise
        cls._log_login_event(db, login, True, user_agent_env)
        return res

    @classmethod
    def _log_login_event(cls, db, login, success, user_agent_env):
        try:
            ip = user_agent_env.get('ip') if user_agent_env else False
            session = user_agent_env.get('session') if user_agent_env else False
            registry = odoo.registry(db)
            with registry.cursor() as cr:
                env = odoo.api.Environment(cr, odoo.SUPERUSER_ID, {})
                icp = env['ir.config_parameter'].sudo()
                if icp.get_param('document_management.enable_audit', 'True') == 'True':
                    user = env['res.users'].search([('login', '=', login)], limit=1)
                    env['dms.audit.trail'].create({
                        'action': 'login_success' if success else 'login_fail',
                        'model_name': 'res.users',
                        'record_id': user.id if user else 0,
                        'user_id': user.id if user else 1,
                        'login': login,
                        'ip_address': ip or False,
                        'session_id': session or False,
                    })
        except Exception:
            _logger.warning('Failed to record login audit event', exc_info=True)
