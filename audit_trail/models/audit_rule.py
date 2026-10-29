import json
import logging

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

PATCHED_METHODS = ("create", "write", "unlink")
SKIP_FIELDS = {"id", "create_uid", "create_date", "write_uid", "write_date", "__last_update"}
SKIP_PREFIXES = ("message_", "activity_", "website_message", "rating_")
SKIP_TYPES = {"one2many", "binary", "properties", "properties_definition"}
BLOCKED_MODEL_PREFIXES = ("audit.", "bus.")


# Odoo 16+ dropped BaseModel._patch_method, so the rules carry their own pair.
def _patch_method(cls, name, method):
    origin = getattr(cls, name)
    method.origin = origin
    method.audit_own_attr = name in cls.__dict__
    if hasattr(origin, "_returns"):
        method._returns = origin._returns
    setattr(cls, name, method)


def _revert_method(cls, name):
    method = cls.__dict__.get(name)
    if method is None or not hasattr(method, "origin"):
        return
    if method.audit_own_attr:
        setattr(cls, name, method.origin)
    else:
        delattr(cls, name)


def _make_create():
    @api.model_create_multi
    def create(self, vals_list):
        origin = create.origin
        if getattr(origin, "_api", None) == "model_create_multi":
            records = origin(self, vals_list)
        else:
            records = self.browse().concat(*(origin(self, vals) for vals in vals_list))
        rule = self.env["audit.rule"]._get_active_rule(self._name)
        if rule.log_create and records:
            fnames = rule._audit_field_names(records)
            new = rule._audit_read(records, fnames)
            rule._audit_log("create", records, {}, new)
        return records

    return create


def _make_write():
    def write(self, vals):
        rule = self.env["audit.rule"]._get_active_rule(self._name)
        fnames = [f for f in rule._audit_field_names(self) if f in vals] if rule.log_write else []
        if not fnames or not self:
            return write.origin(self, vals)
        old = rule._audit_read(self, fnames)
        result = write.origin(self, vals)
        new = rule._audit_read(self, fnames)
        rule._audit_log("write", self, old, new)
        return result

    return write


def _make_unlink():
    def unlink(self):
        rule = self.env["audit.rule"]._get_active_rule(self._name)
        if not rule.log_unlink or not self:
            return unlink.origin(self)
        # The records are gone after the real unlink, so prepare the logs first.
        log_vals = rule._audit_prepare_unlink(self)
        result = unlink.origin(self)
        self.env["audit.log"].sudo().create(log_vals)
        return result

    return unlink


class AuditRule(models.Model):
    _name = "audit.rule"
    _description = "Audit Rule"
    _order = "name"

    name = fields.Char(required=True)
    model_id = fields.Many2one(
        "ir.model", string="Model", required=True, ondelete="cascade",
        domain=[("transient", "=", False)],
    )
    model_name = fields.Char(related="model_id.model", store=True, index=True, string="Technical Name")
    state = fields.Selection(
        [("draft", "Draft"), ("subscribed", "Subscribed")], default="draft", required=True, readonly=True
    )
    log_create = fields.Boolean("Log Creates", default=True)
    log_write = fields.Boolean("Log Changes", default=True)
    log_unlink = fields.Boolean("Log Deletes", default=True)
    field_mode = fields.Selection(
        [("all", "All fields"), ("include", "Only these fields"), ("exclude", "All fields except these")],
        string="Fields to Log", default="all", required=True,
    )
    field_ids = fields.Many2many(
        "ir.model.fields", string="Fields",
        domain="[('model_id', '=', model_id), ('store', '=', True)]",
    )
    parent_field_id = fields.Many2one(
        "ir.model.fields", string="Parent Field", ondelete="set null",
        domain="[('model_id', '=', model_id), ('ttype', '=', 'many2one'), ('store', '=', True)]",
        help="Many2one pointing to the parent record. Changes here also show in the parent's Audit History "
        "(for example a specification row under its parameter).",
    )
    action_id = fields.Many2one("ir.actions.server", string="History Action", readonly=True, ondelete="set null")
    log_count = fields.Integer(compute="_compute_log_count", string="Logs")

    _sql_constraints = [
        ("model_uniq", "unique(model_id)", "There is already an audit rule for this model."),
    ]

    def _compute_log_count(self):
        counts = dict(
            self.env["audit.log"]._read_group([("rule_id", "in", self.ids)], ["rule_id"], ["__count"])
        )
        for rule in self:
            rule.log_count = counts.get(rule, 0)

    @api.constrains("model_id")
    def _check_model(self):
        for rule in self:
            model = rule.model_id.model
            if model.startswith(BLOCKED_MODEL_PREFIXES):
                raise ValidationError(_("The model %s cannot be audited.", model))
            if model in self.env and (self.env[model]._abstract or self.env[model]._transient):
                raise ValidationError(_("Only regular models can be audited, not %s.", model))

    # ------------------------------------------------------------------
    # CRUD: keep patches, history actions and the rule cache in sync
    # ------------------------------------------------------------------

    @api.model_create_multi
    def create(self, vals_list):
        rules = super().create(vals_list)
        rules.filtered(lambda r: r.state == "subscribed")._subscribe_effects()
        self.env.registry.clear_cache()
        return rules

    def write(self, vals):
        if "model_id" in vals and self.filtered(lambda r: r.state == "subscribed"):
            raise UserError(_("Unsubscribe the rule before changing its model."))
        res = super().write(vals)
        self.env.registry.clear_cache()
        return res

    def unlink(self):
        self._unpatch_models()
        self.action_id.unlink()
        res = super().unlink()
        self.env.registry.clear_cache()
        return res

    def action_subscribe(self):
        to_subscribe = self.filtered(lambda r: r.state == "draft")
        to_subscribe.write({"state": "subscribed"})
        to_subscribe._subscribe_effects()
        return True

    def action_unsubscribe(self):
        to_unsubscribe = self.filtered(lambda r: r.state == "subscribed")
        to_unsubscribe.write({"state": "draft"})
        to_unsubscribe._unpatch_models()
        to_unsubscribe.action_id.unlink()
        self.env.registry.registry_invalidated = True
        return True

    def _subscribe_effects(self):
        self._patch_models()
        for rule in self.filtered(lambda r: not r.action_id):
            rule.action_id = self.env["ir.actions.server"].sudo().create({
                "name": _("Audit History"),
                "model_id": rule.model_id.id,
                "binding_model_id": rule.model_id.id,
                "binding_view_types": "form,list",
                "state": "code",
                "code": "action = env['audit.rule'].action_open_history(model._name, records.ids)",
                "groups_id": [(4, self.env.ref("audit_trail.group_audit_viewer").id)],
            })
        # Other workers rebuild their registry and patch in _register_hook.
        self.env.registry.registry_invalidated = True

    # ------------------------------------------------------------------
    # Patching
    # ------------------------------------------------------------------

    def _register_hook(self):
        res = super()._register_hook()
        self.sudo().search([("state", "=", "subscribed")])._patch_models()
        return res

    def _patch_models(self):
        for rule in self:
            cls = self.env.registry.get(rule.model_name)
            if cls is None or cls.__dict__.get("_audit_trail_patched"):
                continue
            _patch_method(cls, "create", _make_create())
            _patch_method(cls, "write", _make_write())
            _patch_method(cls, "unlink", _make_unlink())
            cls._audit_trail_patched = True
            _logger.info("Audit trail enabled on %s", rule.model_name)

    def _unpatch_models(self):
        for rule in self:
            cls = self.env.registry.get(rule.model_name)
            if cls is None or not cls.__dict__.get("_audit_trail_patched"):
                continue
            for name in PATCHED_METHODS:
                _revert_method(cls, name)
            cls._audit_trail_patched = False
            _logger.info("Audit trail disabled on %s", rule.model_name)

    @tools.ormcache("model_name")
    def _get_active_rule_id(self, model_name):
        return self.sudo().search([("model_name", "=", model_name), ("state", "=", "subscribed")], limit=1).id

    @api.model
    def _get_active_rule(self, model_name):
        return self.sudo().browse(self._get_active_rule_id(model_name))

    # ------------------------------------------------------------------
    # Reading and logging values
    # ------------------------------------------------------------------

    def _audit_snapshot_field_names(self, records):
        """Stored fields a user can set, used for delete snapshots and restore."""
        names = []
        for fname, field in records._fields.items():
            if fname in SKIP_FIELDS or fname.startswith(SKIP_PREFIXES) or field.type in SKIP_TYPES:
                continue
            if not field.store or (field.compute and field.readonly):
                continue
            names.append(fname)
        return names

    def _audit_field_names(self, records):
        self.ensure_one()
        names = self._audit_snapshot_field_names(records)
        chosen = set(self.field_ids.mapped("name"))
        if self.field_mode == "include":
            return [f for f in names if f in chosen]
        if self.field_mode == "exclude":
            return [f for f in names if f not in chosen]
        return names

    def _audit_read(self, records, fnames):
        if not fnames:
            return {rec.id: {} for rec in records}
        rows = records.sudo().with_context(active_test=False).read(fnames, load="_classic_write")
        return {row.pop("id"): row for row in rows}

    def _audit_display(self, field, value):
        if field.type == "boolean":
            return _("Yes") if value else _("No")
        if value in (False, None, []):
            return ""
        if field.type == "many2one":
            rec = self.env[field.comodel_name].sudo().browse(value).exists()
            return rec.display_name if rec else _("#%s (deleted)", value)
        if field.type == "many2many":
            return ", ".join(self.env[field.comodel_name].sudo().browse(value).exists().mapped("display_name"))
        if field.type == "selection":
            return dict(field._description_selection(self.env)).get(value, value)
        return str(value)

    def _audit_line_vals(self, records, fname, old, new):
        field = records._fields[fname]
        ir_field = self.env["ir.model.fields"]._get(records._name, fname)
        return {
            "field_id": ir_field.id,
            "field_name": fname,
            "field_label": field.string,
            "old_value": self._audit_display(field, old) if old is not None else False,
            "new_value": self._audit_display(field, new) if new is not None else False,
        }

    def _audit_parent_vals(self, record):
        if not self.parent_field_id or self.parent_field_id.name not in record._fields:
            return {}
        parent = record.sudo()[self.parent_field_id.name]
        if not parent:
            return {}
        return {"parent_model": parent._name, "parent_res_id": parent.id, "parent_name": parent.display_name}

    @api.model
    def _audit_source(self):
        if not self.env.registry.ready:
            return "module"
        if self.env.context.get("import_file"):
            return "import"
        if request:
            return "ui"
        return "script"

    def _audit_base_vals(self, operation, record):
        parent_vals = self._audit_parent_vals(record)
        name = record.sudo().display_name
        # Models without a name field display as "model,id"; the parent reads better.
        if name == f"{record._name},{record.id}" and parent_vals:
            name = f"{parent_vals['parent_name']} / #{record.id}"
        return {
            "rule_id": self.id,
            "model_id": self.model_id.id,
            "model_name": record._name,
            "res_id": record.id,
            "res_name": name,
            "operation": operation,
            "user_id": self.env.uid,
            "source": self._audit_source(),
            **parent_vals,
        }

    def _audit_log(self, operation, records, old, new):
        self.ensure_one()
        vals_list = []
        for record in records:
            old_values, new_values = old.get(record.id, {}), new.get(record.id, {})
            lines = []
            for fname in (new_values or old_values):
                before, after = old_values.get(fname), new_values.get(fname)
                if operation == "write":
                    if isinstance(before, list):
                        before, after = sorted(before), sorted(after or [])
                    if before == after:
                        continue
                if operation == "create" and after in (False, None, [], ""):
                    continue
                lines.append((0, 0, self._audit_line_vals(records, fname, before, after)))
            if operation == "write" and not lines:
                continue
            vals_list.append({**self._audit_base_vals(operation, record), "line_ids": lines})
        if vals_list:
            self.env["audit.log"].sudo().create(vals_list)

    def _audit_children(self, record):
        """One2many children the database will orphan (set null) or delete (cascade)."""
        children = {}
        for fname, field in record._fields.items():
            if field.type != "one2many" or field.compute or not field.inverse_name:
                continue
            comodel = self.env.get(field.comodel_name)
            inverse = comodel._fields.get(field.inverse_name) if comodel is not None else None
            if inverse is None or inverse.type != "many2one" or not inverse.store:
                continue
            lines = record.sudo().with_context(active_test=False)[fname]
            if not lines:
                continue
            if inverse.ondelete == "cascade":
                fnames = self._audit_snapshot_field_names(lines)
                rows = self._audit_read(lines, [f for f in fnames if f != field.inverse_name])
                children[fname] = {"mode": "recreate", "values": list(rows.values())}
            elif inverse.ondelete == "set null":
                children[fname] = {"mode": "relink", "ids": lines.ids}
        return children

    def _audit_prepare_unlink(self, records):
        self.ensure_one()
        snapshot_values = self._audit_read(records, self._audit_snapshot_field_names(records))
        shown = set(self._audit_field_names(records))
        vals_list = []
        for record in records:
            values = snapshot_values.get(record.id, {})
            lines = [
                (0, 0, self._audit_line_vals(records, fname, value, None))
                for fname, value in values.items()
                if fname in shown and value not in (False, None, [], "")
            ]
            snapshot = {"values": values, "children": self._audit_children(record)}
            vals_list.append({
                **self._audit_base_vals("unlink", record),
                "line_ids": lines,
                "snapshot": json.dumps(snapshot, default=str),
            })
        return vals_list

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    @api.model
    def action_open_history(self, model_name, res_ids):
        action = self.env["ir.actions.act_window"]._for_xml_id("audit_trail.action_audit_log")
        action["domain"] = [
            "|",
            "&", ("model_name", "=", model_name), ("res_id", "in", res_ids),
            "&", ("parent_model", "=", model_name), ("parent_res_id", "in", res_ids),
        ]
        action["context"] = {}
        return action

    def action_view_logs(self):
        self.ensure_one()
        action = self.env["ir.actions.act_window"]._for_xml_id("audit_trail.action_audit_log")
        action["domain"] = [("rule_id", "=", self.id)]
        action["context"] = {}
        return action
