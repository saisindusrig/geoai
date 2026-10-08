"""Metadata extension for the existing relationship table; v1 schema remains frozen."""
import sqlalchemy as sa

RELATIONSHIP_KINDS=("CONNECTS_TO","CROSSES","SUPPORTED_BY","HOSTED_BY","SERVES","DRAINS_TO","ALIGNS_WITH","DEPENDS_ON","ADJACENT_TO","PART_OF","INTERSECTS")
KIND_CHECK="kind IN ("+",".join(repr(k) for k in RELATIONSHIP_KINDS)+")"


def extend(metadata):
    target=metadata.tables["asset_relationships"]
    for constraint in list(target.constraints):
        if isinstance(constraint,sa.CheckConstraint) and "kind IN" in str(constraint.sqltext):
            target.constraints.remove(constraint)
    target.append_constraint(sa.CheckConstraint(KIND_CHECK,name="ck_asset_relationships_1"))
