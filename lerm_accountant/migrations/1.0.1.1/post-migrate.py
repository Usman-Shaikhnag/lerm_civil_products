def migrate(cr, version):
    cr.execute("""
        UPDATE lerm_srf_sample
        SET invoice_status = '3-invoiced'
        WHERE invoice_status = '2-invoiced'
    """)
