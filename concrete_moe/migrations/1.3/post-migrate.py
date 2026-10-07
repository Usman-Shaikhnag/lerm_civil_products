def migrate(cr, version):
    """Replay the parked cube_strength_1/2/3 values into the dynamic cube lines.

    The pre migration script copied the values out before the columns were
    dropped. One cube line is created per entered value, numbered 1, 2, 3 in
    order, so the average Fc and both reference stresses come out unchanged.
    """
    cr.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_name IN (
            'concrete_moe_cube_legacy',
            'mechanical_concrete_moe_cube_line'
        )
    """)
    tables = {row[0] for row in cr.fetchall()}
    if not {
        'concrete_moe_cube_legacy',
        'mechanical_concrete_moe_cube_line',
    } <= tables:
        return

    cr.execute("""
        SELECT parent_id, cube_strength_1, cube_strength_2, cube_strength_3
        FROM concrete_moe_cube_legacy
        ORDER BY parent_id
    """)
    rows = cr.fetchall()

    for row in rows:
        parent_id = row[0]
        values = [value for value in row[1:] if value]
        if not values:
            continue

        # Already migrated, never duplicate the cube specimens.
        cr.execute(
            "SELECT 1 FROM mechanical_concrete_moe_cube_line WHERE parent_id = %s",
            (parent_id,),
        )
        if cr.fetchone():
            continue

        for specimen, strength in enumerate(values, start=1):
            cr.execute(
                """
                INSERT INTO mechanical_concrete_moe_cube_line
                    (parent_id, specimen, compressive_strength)
                VALUES (%s, %s, %s)
                """,
                (parent_id, specimen, strength),
            )

    cr.execute("DROP TABLE IF EXISTS concrete_moe_cube_legacy")
