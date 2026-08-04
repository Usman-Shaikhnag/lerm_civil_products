def _seed_salesperson_group(env):
    group = env.ref(
        "customer_ageing_dashboard.group_accounts_saleperson_ageing",
        raise_if_not_found=False,
    )
    if not group or group.users:
        return
    invoice_users = (
        env["account.move"]
        .search([
            ("move_type", "in", ["out_invoice", "out_refund"]),
            ("state", "=", "posted"),
            ("invoice_user_id", "!=", False),
        ])
        .mapped("invoice_user_id")
    )
    if invoice_users:
        group.write({"users": [(4, u.id) for u in invoice_users]})
