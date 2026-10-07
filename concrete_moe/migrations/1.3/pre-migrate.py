def migrate(cr, version):
    """Park the old fixed cube_strength_1/2/3 values before the columns are dropped.

    The first table became a one2many, so these three parent level fields are
    removed by this upgrade and their columns disappear with them. A post
    migration script then replays them into the cube lines, which cannot happen
    from here because that table does not exist yet.
    """
    cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'mechanical_concrete_moe'
    """)
    available = {row[0] for row in cr.fetchall()}

    legacy = [
        name
        for name in ("cube_strength_1", "cube_strength_2", "cube_strength_3")
        if name in available
    ]
    if not legacy:
        return

    cr.execute("""
        CREATE TABLE IF NOT EXISTS concrete_moe_cube_legacy (
            parent_id integer PRIMARY KEY,
            cube_strength_1 double precision,
            cube_strength_2 double precision,
            cube_strength_3 double precision
        )
    """)

    cr.execute(
        """
        INSERT INTO concrete_moe_cube_legacy
            (parent_id, cube_strength_1, cube_strength_2, cube_strength_3)
        SELECT id, %s FROM mechanical_concrete_moe
        ON CONFLICT (parent_id) DO UPDATE SET
            cube_strength_1 = EXCLUDED.cube_strength_1,
            cube_strength_2 = EXCLUDED.cube_strength_2,
            cube_strength_3 = EXCLUDED.cube_strength_3
        """
        % ", ".join(legacy)
    )
