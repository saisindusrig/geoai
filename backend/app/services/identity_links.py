"""Read-only, audited identity association boundary; no automatic provisioning.

This metadata is deliberately NOT registered on Base. An approved future schema
provisioning/linking process is required. Original databases are never migrated.
"""
import hashlib
from sqlalchemy import Column, Integer, MetaData, String, Table, UniqueConstraint, select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException
from app.core.firebase_auth import FirebaseIdentity
from app.db.models import AuditLog, User

identity_metadata = MetaData()
identity_links = Table('auth_identity_links', identity_metadata,
    Column('id', String(36), primary_key=True),
    Column('issuer', String(255), nullable=False),
    Column('subject', String(128), nullable=False),
    Column('user_id', Integer, nullable=False),
    Column('approved_by', Integer, nullable=False),
    Column('audit_id', Integer, nullable=False, unique=True),
    Column('state', String(16), nullable=False),
    UniqueConstraint('issuer', 'subject'),
    UniqueConstraint('issuer', 'user_id'))


def resolve_link(db, identity: FirebaseIdentity) -> int:
    try:
        row = db.execute(select(identity_links).where(
            identity_links.c.issuer == identity.issuer,
            identity_links.c.subject == identity.uid)).mappings().one_or_none()
    except SQLAlchemyError:
        raise HTTPException(503, 'Identity linking is not provisioned; no account was created') from None
    if row is None or row['state'] != 'ACTIVE':
        raise HTTPException(403, 'Firebase identity is not linked to an authorized internal account')
    user = db.get(User, row['user_id'])
    approval = db.get(AuditLog, row['audit_id'])
    approver = db.get(User, row['approved_by'])
    # Bind the association to an existing explicit audit approval; never email.
    expected = dict(issuer=identity.issuer,
                    subject_sha256=hashlib.sha256(identity.uid.encode()).hexdigest(),
                    internal_user_id=row['user_id'], approved_by=row['approved_by'])
    if (user is None or approver is None or approver.role != 'admin'
            or approval is None or approval.action != 'auth.firebase.link_approved'
            or approval.entity_type != 'identity_link' or approval.entity_id != row['id']
            or approval.user_id != row['approved_by'] or approval.metadata_json != expected):
        raise HTTPException(403, 'Identity association lacks matching audit authorization')
    return user.id
