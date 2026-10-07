OLD_NAME = "Compressive Strength of Concrete (MOE)"
NEW_NAME = "Concrete MOE"


def post_init_hook(env):
    """Rename the MOE records still carrying the old product name.

    The Open Form shows `name` (the model's _rec_name) in its header, so records
    created before the rename keep displaying the old title until this runs.
    """
    records = env["mechanical.concrete.moe"].search([("name", "=", OLD_NAME)])
    if records:
        records.write({"name": NEW_NAME})
