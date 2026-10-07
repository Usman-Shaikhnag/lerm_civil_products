# -*- coding: utf-8 -*-
"""CS Pipe: align the pass/fail columns of ``cs_pipe`` with the field definitions.

Older versions of this module stored the conformity/nabl results as Boolean
columns, while other versions stored them as ``fields.Selection`` columns with
the ``pass`` / ``fail`` values. Odoo 17 repairs a column whose database type no
longer matches the field definition with::

    ALTER TABLE "cs_pipe" ALTER COLUMN "x" DROP DEFAULT,
    ALTER COLUMN "x" TYPE <new type> USING "x"::<new type>

that statement casts the existing values, so it aborts the upgrade as soon as a
value does not belong to the old type, e.g.::

    psycopg2.errors.InvalidTextRepresentation:
    invalid input syntax for type boolean: "fail"

The ``requirement_*`` columns went through the same kind of change, from a
free text column (``'450 Min'``) to a ``fields.Float`` column, which aborts on::

    psycopg2.errors.InvalidTextRepresentation:
    invalid input syntax for type double precision: "450 Min"

This script runs in the ``pre`` stage of the upgrade, i.e. before Odoo
initialises ``cs.pipe`` and before it attempts any conversion, and makes the
automatic conversion a no-op by writing castable values and fixing the column
type itself. No record is ever created, removed or dropped.
"""

import logging

_logger = logging.getLogger(__name__)

TABLE = 'cs_pipe'

# Free text columns that became numeric fields, the leading number of the
# stored text is kept ('450 Min' -> 450) and a value without any number
# becomes NULL.
NUMERIC_FIELDS = (
    'requirement_yield',
    'requirement_utl',
    'requirement_elongation',
)

# field name -> (expected column type, value of True, value of False)
# Fields listed here are the pass/fail results of cs.pipe plus the stored
# boolean ``conformity`` inherited from lerm.eln, which used to be a
# pass/fail selection of cs.pipe and is therefore still present in the
# database as a character varying column.
FIELDS = {
    'conformity': ('bool', 'pass', 'fail'),
    'uts_conformity': ('varchar', 'pass', 'fail'),
    'yield_conformity': ('varchar', 'pass', 'fail'),
    'elongation_conformity': ('varchar', 'pass', 'fail'),
    'ts_ys_conformity': ('varchar', 'pass', 'fail'),
    'weight_per_meter_conformity': ('varchar', 'pass', 'fail'),
    'uts_nabl': ('varchar', 'pass', 'fail'),
    'yield_nabl': ('varchar', 'pass', 'fail'),
    'elongation_nabl': ('varchar', 'pass', 'fail'),
    'ts_ys_nabl': ('varchar', 'pass', 'fail'),
    'weight_per_meter_nabl': ('varchar', 'pass', 'fail'),
    'bend_test': ('varchar', 'satisfactory', 'non-satisfactory'),
    'bend_test2': ('varchar', 'satisfactory', 'non-satisfactory'),
    're_bend_test': ('varchar', 'satisfactory', 'non-satisfactory'),
}

VARCHAR_TYPES = ('character varying', 'character', 'text')


def _column_type(cr, name):
    """Return the type of the column owned by ``cs_pipe``, None when absent."""
    cr.execute("""
        SELECT a.atttypid::regtype::text, a.attinhcount
        FROM pg_attribute a
        JOIN pg_class c ON c.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relname = %s
          AND c.relkind = 'r'
          AND n.nspname = current_schema()
          AND a.attname = %s
          AND a.attnum > 0
          AND NOT a.attisdropped
    """, (TABLE, name))
    row = cr.fetchone()
    if not row or row[1]:
        return None
    return row[0]


def _to_selection(cr, name, true_value, false_value):
    """Convert a boolean column into a selection column."""
    cr.execute("""
        ALTER TABLE "cs_pipe"
            ALTER COLUMN "{name}" DROP DEFAULT,
            ALTER COLUMN "{name}" TYPE varchar
            USING (CASE WHEN "{name}" IS NULL OR NOT "{name}" THEN %s ELSE %s END)
    """.format(name=name), (false_value, true_value))
    _logger.info("cs_pipe: column %s converted from boolean to varchar (%s / %s)",
                 name, true_value, false_value)


def _to_boolean(cr, name, true_value, false_value):
    """Convert a pass/fail selection column into a boolean column."""
    cr.execute("""
        SELECT "{name}"::text, count(*)
        FROM "cs_pipe"
        GROUP BY 1
    """.format(name=name))
    for value, count in cr.fetchall():
        if value is None or value.strip().lower() in (true_value, false_value, ''):
            continue
        _logger.warning("cs_pipe: column %s holds the unexpected value %r on %s record(s), "
                        "it is converted to NULL", name, value, count)

    cr.execute("""
        UPDATE "cs_pipe"
        SET "{name}" = CASE
            WHEN lower(btrim("{name}")) = %s THEN 'true'
            WHEN "{name}" IS NULL OR lower(btrim("{name}")) IN (%s, '') THEN 'false'
            ELSE NULL
        END
    """.format(name=name), (true_value, false_value))
    cr.execute("""
        ALTER TABLE "cs_pipe"
            ALTER COLUMN "{name}" DROP DEFAULT,
            ALTER COLUMN "{name}" TYPE bool USING "{name}"::bool
    """.format(name=name))
    _logger.info("cs_pipe: column %s converted from varchar to boolean (%s -> true, %s -> false)",
                 name, true_value, false_value)


def _to_numeric(cr, name):
    """Convert a free text column into a numeric column."""
    cr.execute("""
        SELECT "{name}"::text, count(*)
        FROM "cs_pipe"
        WHERE "{name}" IS NOT NULL
        GROUP BY 1
    """.format(name=name))
    for value, count in cr.fetchall():
        try:
            float(value)
        except (TypeError, ValueError):
            _logger.warning("cs_pipe: column %s holds the text value %r on %s record(s), "
                            "only its leading number is kept", name, value, count)

    cr.execute("""
        UPDATE "cs_pipe"
        SET "{name}" = nullif(substring("{name}" from '^\\s*[-+]?[0-9]*\\.?[0-9]+'), '')
    """.format(name=name))
    cr.execute("""
        ALTER TABLE "cs_pipe"
            ALTER COLUMN "{name}" DROP DEFAULT,
            ALTER COLUMN "{name}" TYPE double precision USING "{name}"::double precision
    """.format(name=name))
    _logger.info("cs_pipe: column %s converted from text to double precision", name)


def migrate(cr, installed_version):
    for name, (expected_type, true_value, false_value) in FIELDS.items():
        current_type = _column_type(cr, name)
        if current_type is None:
            _logger.info("cs_pipe: column %s does not exist yet, nothing to migrate", name)
            continue
        if expected_type == 'bool':
            if current_type in VARCHAR_TYPES:
                _to_boolean(cr, name, true_value, false_value)
            elif current_type != 'bool':
                _logger.warning("cs_pipe: column %s has the unexpected type %s, left untouched",
                                name, current_type)
        elif current_type == 'bool':
            _to_selection(cr, name, true_value, false_value)
        elif current_type not in VARCHAR_TYPES:
            _logger.warning("cs_pipe: column %s has the unexpected type %s, left untouched",
                            name, current_type)

    for name in NUMERIC_FIELDS:
        current_type = _column_type(cr, name)
        if current_type is None:
            _logger.info("cs_pipe: column %s does not exist yet, nothing to migrate", name)
        elif current_type in VARCHAR_TYPES:
            _to_numeric(cr, name)
        elif current_type not in ('double precision', 'numeric', 'real'):
            _logger.warning("cs_pipe: column %s has the unexpected type %s, left untouched",
                            name, current_type)
