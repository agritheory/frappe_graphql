import frappe

from frappe_graphql.utils.execution import DataLoader
from .locals import get_loader_from_locals, set_loader_in_locals

from collections import OrderedDict


def get_child_table_loader(child_doctype: str, parent_doctype: str, parentfield: str) -> DataLoader:
    locals_key = (child_doctype, parent_doctype, parentfield)
    loader = get_loader_from_locals(locals_key)
    if loader:
        return loader

    loader = DataLoader(_get_child_table_loader_fn(
        child_doctype=child_doctype,
        parent_doctype=parent_doctype,
        parentfield=parentfield,
    ))
    set_loader_in_locals(locals_key, loader)
    return loader


def _get_child_table_loader_fn(child_doctype: str, parent_doctype: str, parentfield: str):
    def _inner(keys):
        rows = frappe.db.sql(f"""
        SELECT 
            *,
            "{child_doctype}" as doctype
        FROM `tab{child_doctype}`
        WHERE
            parent IN %(parent_keys)s
            AND parenttype = %(parenttype)s
            AND parentfield = %(parentfield)s
        ORDER BY idx
        """, dict(
            parent_keys=keys,
            parenttype=parent_doctype,
            parentfield=parentfield,
        ), as_dict=1)

        _results = OrderedDict()
        for k in keys:
            _results[k] = []

        for row in rows:
            if row.parent not in _results:
                continue
            _results.get(row.parent).append(row)

        return _results.values()

    return _inner
