import json

from odoo import Command, fields, models, _
from odoo.exceptions import AccessError, UserError

from .audit_rule import SKIP_TYPES

OPERATIONS = [("create", "Created"), ("write", "Changed"), ("unlink", "Deleted")]
SOURCES = [
    ("ui", "User Interface / API"),
    ("import", "Import"),
    ("module", "Module Install / Upgrade"),
    ("script", "Cron / Script"),
]


class AuditLog(models.Model):
    _name = "audit.log"
    _description = "Audit Log"
    _order = "date desc, id desc"
    _rec_name = "res_name"

    date = fields.Datetime(default=fields.Datetime.now, required=True, readonly=True, index=True)
    user_id = fields.Many2one("res.users", string="User", readonly=True, ondelete="set null", index=True)
    rule_id = fields.Many2one("audit.rule", string="Rule", readonly=True, ondelete="set null")
    model_id = fields.Many2one("ir.model", string="Model", readonly=True, ondelete="set null")
    model_name = fields.Char("Technical Model", readonly=True, index=True)
    res_id = fields.Integer("Record ID", readonly=True, index=True)
    res_name = fields.Char("Record", readonly=True)
    operation = fields.Selection(OPERATIONS, readonly=True, required=True, index=True)
    source = fields.Selection(SOURCES, readonly=True)
    parent_model = fields.Char(readonly=True, index=True)
    parent_res_id = fields.Integer("Parent ID", readonly=True, index=True)
    parent_name = fields.Char("Parent Record", readonly=True)
    line_ids = fields.One2many("audit.log.line", "log_id", string="Changes", readonly=True)
    snapshot = fields.Text(readonly=True, help="JSON copy of the deleted record, used by Restore.")
    restored_res_id = fields.Integer("Restored As ID", readonly=True)

    def write(self, vals):
        if not self.env.context.get("audit_trail_internal"):
            raise UserError(_("Audit logs cannot be modified."))
        return super().write(vals)

    def unlink(self):
        raise UserError(_("Audit logs cannot be deleted."))

    def action_open_record(self):
        self.ensure_one()
        res_id = self.restored_res_id or self.res_id
        if self.model_name not in self.env or not self.env[self.model_name].browse(res_id).exists():
            raise UserError(_("This record no longer exists."))
        return {
            "type": "ir.actions.act_window",
            "res_model": self.model_name,
            "res_id": res_id,
            "view_mode": "form",
            "target": "current",
        }

    def action_restore(self):
        self.ensure_one()
        if not self.env.user.has_group("audit_trail.group_audit_manager"):
            raise AccessError(_("Only Audit Managers can restore deleted records."))
        if self.operation != "unlink" or not self.snapshot:
            raise UserError(_("Only deleted records can be restored."))
        if self.restored_res_id:
            raise UserError(_("This record was already restored (ID %s).", self.restored_res_id))
        if self.model_name not in self.env:
            raise UserError(_("The model %s is not installed.", self.model_name))

        Model = self.env[self.model_name]
        snapshot = json.loads(self.snapshot)
        record = Model.create(self._restore_vals(Model, snapshot.get("values", {})))
        for fname, child in snapshot.get("children", {}).items():
            field = Model._fields.get(fname)
            if field is None or field.type != "one2many":
                continue
            Child = self.env[field.comodel_name].with_context(active_test=False)
            if child["mode"] == "relink":
                # Only take back rows nobody has re-attached since the delete.
                orphans = Child.browse(child["ids"]).exists().filtered(lambda c: not c[field.inverse_name])
                orphans.write({field.inverse_name: record.id})
            else:
                Child.create([
                    {**self._restore_vals(Child, vals), field.inverse_name: record.id}
                    for vals in child["values"]
                ])
        self.sudo().with_context(audit_trail_internal=True).write({"restored_res_id": record.id})
        return self.action_open_record()

    def _restore_vals(self, Model, values):
        vals = {}
        for fname, value in values.items():
            field = Model._fields.get(fname)
            if field is None or not field.store or field.type in SKIP_TYPES:
                continue
            if field.compute and field.readonly:
                continue
            if field.type == "many2one":
                value = value if value and self.env[field.comodel_name].browse(value).exists() else False
            elif field.type == "many2many":
                value = [Command.set(self.env[field.comodel_name].browse(value or []).exists().ids)]
            vals[fname] = value
        return vals


class AuditLogLine(models.Model):
    _name = "audit.log.line"
    _description = "Audit Log Field Change"
    _order = "id"

    log_id = fields.Many2one("audit.log", required=True, ondelete="cascade", index=True)
    field_id = fields.Many2one("ir.model.fields", string="Field", ondelete="set null")
    field_name = fields.Char("Technical Field", readonly=True)
    field_label = fields.Char("Field", readonly=True)
    old_value = fields.Text("Old Value", readonly=True)
    new_value = fields.Text("New Value", readonly=True)

    def write(self, vals):
        raise UserError(_("Audit logs cannot be modified."))

    def unlink(self):
        raise UserError(_("Audit logs cannot be deleted."))
