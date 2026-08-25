# -*- coding: utf-8 -*-

from odoo import fields, models


class DmsFieldDefinition(models.Model):
    _name = 'dms.field.definition'
    _description = 'DMS Custom Field Definition'
    _order = 'sequence, name'

    name = fields.Char(string='Field Label', required=True)
    code = fields.Char(string='Code', required=True,
                       help='Internal code used to reference this field.')
    field_type = fields.Selection([
        ('char', 'Text'),
        ('text', 'Multiline Text'),
        ('integer', 'Integer'),
        ('float', 'Number'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('boolean', 'Boolean'),
        ('selection', 'Selection'),
        ('many2one', 'Related Record'),
    ], string='Field Type', required=True, default='char')
    selection_options = fields.Char(
        string='Selection Options',
        help='Comma separated list of options for the Selection type.')
    model_id = fields.Many2one(
        'ir.model', string='Target Model',
        help='Target model for the "Related Record" type.')
    required = fields.Boolean(string='Required')
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)
    help = fields.Char(string='Help Text')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'A custom field code must be unique.'),
    ]


class DmsFileCustomValue(models.Model):
    _name = 'dms.file.custom.value'
    _description = 'DMS File Custom Value'
    _order = 'field_id'

    file_id = fields.Many2one('dms.file', string='Document', required=True, ondelete='cascade', index=True)
    field_id = fields.Many2one('dms.field.definition', string='Field', required=True, ondelete='cascade')
    value_char = fields.Char(string='Text Value')
    value_text = fields.Text(string='Multiline Value')
    value_integer = fields.Integer(string='Integer Value')
    value_float = fields.Float(string='Number Value')
    value_date = fields.Date(string='Date Value')
    value_datetime = fields.Datetime(string='Datetime Value')
    value_boolean = fields.Boolean(string='Boolean Value')
    value_many2one = fields.Integer(string='Related Record Value')

    _sql_constraints = [
        ('file_field_unique', 'unique(file_id, field_id)',
         'A field can only be set once per document.'),
    ]

    def get_display_value(self):
        self.ensure_one()
        if self.field_id.field_type == 'char':
            return self.value_char
        if self.field_id.field_type == 'text':
            return self.value_text
        if self.field_id.field_type == 'integer':
            return self.value_integer
        if self.field_id.field_type == 'float':
            return self.value_float
        if self.field_id.field_type == 'date':
            return self.value_date
        if self.field_id.field_type == 'datetime':
            return self.value_datetime
        if self.field_id.field_type == 'boolean':
            return 'Yes' if self.value_boolean else 'No'
        if self.field_id.field_type == 'many2one':
            if self.field_id.model_id and self.value_many2one:
                rec = self.env[self.field_id.model_id.model].browse(self.value_many2one)
                return rec.exists().display_name if rec else ''
            return ''
        if self.field_id.field_type == 'selection':
            return self.value_char
        return ''
