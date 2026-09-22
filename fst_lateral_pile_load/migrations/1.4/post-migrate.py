from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    """Recompute stored ELN-derived fields on existing records.

    Stored computed columns added by a module update are never recomputed for
    rows that predate the column, so report_no/ulr/test_standard/discipline/group
    can be empty on already-created records until something touches them.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env['fst.lateral.pile.load.test'].search([])
    if records:
        records = records.with_context(_fst_no_recompute=True)
        records._compute_srf_data()
        records._compute_eln_fields()
