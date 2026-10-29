from . import models


def uninstall_hook(env):
    rules = env["audit.rule"].search([])
    rules._unpatch_models()
    rules.action_id.unlink()
