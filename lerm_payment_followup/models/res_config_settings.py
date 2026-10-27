from datetime import datetime, timedelta

import pytz

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    followup_auto_enabled = fields.Boolean(
        string="Automatic Follow-up",
        config_parameter="lerm_payment_followup.auto_enabled",
    )
    followup_auto_time = fields.Float(
        string="Run Time",
        config_parameter="lerm_payment_followup.auto_time",
        default=9.0,
    )
    followup_auto_send_email = fields.Boolean(
        string="Send Emails Automatically",
        config_parameter="lerm_payment_followup.auto_send_email",
    )
    followup_auto_create_activity = fields.Boolean(
        string="Create Call Tasks Automatically",
        config_parameter="lerm_payment_followup.auto_create_activity",
    )

    def set_values(self):
        super().set_values()
        cron = self.env.ref("lerm_payment_followup.ir_cron_followup_auto", raise_if_not_found=False)
        if not cron:
            return
        vals = {"active": self.followup_auto_enabled}
        if self.followup_auto_enabled:
            vals["nextcall"] = self._followup_next_run(self.followup_auto_time)
        cron.sudo().write(vals)

    def _followup_next_run(self, run_time):
        """Next occurrence of ``run_time`` (hours, in the user's timezone) as naive UTC."""
        tz = pytz.timezone(self.env.user.tz or "UTC")
        now = datetime.now(tz)
        hour, minute = divmod(round((run_time or 0.0) * 60), 60)
        run = now.replace(hour=int(hour) % 24, minute=int(minute), second=0, microsecond=0)
        if run <= now:
            run += timedelta(days=1)
        return run.astimezone(pytz.utc).replace(tzinfo=None)
