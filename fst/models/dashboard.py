from odoo import models


class ERTDashboard(models.Model):
    _name = "lerm.ert.dashboard"
    _description = "ERT Dashboard"

    def search(self, args, offset=0, limit=None, order=None, count=False):
        res = super(ERTDashboard, self).search(args, offset=offset, limit=limit, order=order, count=count)
        if not res and not count:
            return self.create({})
        return res
