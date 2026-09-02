# -*- coding: utf-8 -*-

from odoo import fields, models


class DmsDepartment(models.Model):
    _name = 'dms.department'
    _description = 'DMS Department'
    _order = 'name'

    name = fields.Char(string='Department', required=True)
    active = fields.Boolean(default=True)
    parent_id = fields.Many2one('dms.department', string='Parent Department', ondelete='restrict')
    user_ids = fields.Many2many('res.users', string='Members')
    manager_id = fields.Many2one('res.users', string='Manager')
    note = fields.Text(string='Notes')


class DmsTeam(models.Model):
    _name = 'dms.team'
    _description = 'DMS Team'
    _order = 'name'

    name = fields.Char(string='Team', required=True)
    active = fields.Boolean(default=True)
    department_id = fields.Many2one('dms.department', string='Department', ondelete='restrict')
    leader_id = fields.Many2one('res.users', string='Team Leader')
    member_ids = fields.Many2many('res.users', string='Members')


class DmsRole(models.Model):
    _name = 'dms.role'
    _description = 'DMS Role'
    _order = 'name'

    name = fields.Char(string='Role', required=True)
    active = fields.Boolean(default=True)
    user_ids = fields.Many2many('res.users', string='Users')
    group_ids = fields.Many2many('res.groups', string='Odoo Groups')
    note = fields.Text(string='Notes')


class DmsTag(models.Model):
    _name = 'dms.tag'
    _description = 'DMS Tag'
    _order = 'name'

    name = fields.Char(string='Tag', required=True)
    active = fields.Boolean(default=True)
    color = fields.Char(string='Color', help='Hex color e.g. #1f6feb')
    file_count = fields.Integer(string='Files', compute='_compute_counts')

    def _compute_counts(self):
        for tag in self:
            tag.file_count = self.env['dms.file'].search_count([('tag_ids', 'in', tag.id)])


class DmsDocumentType(models.Model):
    _name = 'dms.document.type'
    _description = 'DMS Document Type'
    _order = 'name'

    name = fields.Char(string='Document Type', required=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(default=True)


class DmsProject(models.Model):
    _name = 'dms.project'
    _description = 'DMS Project'
    _order = 'name'

    name = fields.Char(string='Project', required=True)
    code = fields.Char(string='Code')
    active = fields.Boolean(default=True)
    department_id = fields.Many2one('dms.department', string='Department')
    user_ids = fields.Many2many('res.users', string='Team Members')
    start_date = fields.Date(string='Start Date')
    end_date = fields.Date(string='End Date')
