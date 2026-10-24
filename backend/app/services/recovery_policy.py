"""Conservative recovery decisions only; never dispatches, authorizes or solves.

Future queue consumers must still call existing owner/revision/authorization gates.
This policy is not connected to current synchronous engineering execution.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class RecoveryDecision:
    state: str
    action: str
    may_execute: bool = False


def assess_recovery(*, state: str, exact_authorization: bool, current_source: bool,
                    database_available: bool, storage_available: bool,
                    complete_manifest: bool, artifact_hashes_match: bool) -> RecoveryDecision:
    if not database_available:
        return RecoveryDecision('UNAVAILABLE', 'Restore database access; do not acknowledge delivery or execute.')
    if not exact_authorization or not current_source:
        return RecoveryDecision('REJECTED', 'Reopen existing authorization workflow against current saved sources.')
    if not storage_available:
        return RecoveryDecision('UNAVAILABLE', 'Restore storage access; preserve evidence and do not rerun.')
    if state == 'COMPLETED' and complete_manifest and artifact_hashes_match:
        return RecoveryDecision('COMPLETED', 'Return the existing exact saved result; do not execute duplicate delivery.')
    if state in ('AUTHORIZED', 'RUNNING', 'PUBLISHING', 'COMPLETED', 'INTERRUPTED', 'FAILED'):
        return RecoveryDecision('REVIEW_REQUIRED', 'Uncertain attempt or incomplete evidence: reconcile manually; never auto-rerun.')
    return RecoveryDecision('REVIEW_REQUIRED', 'Use existing authorization gates; this policy cannot grant execution.')
