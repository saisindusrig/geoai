"""New design requests must not spend provider requests on stale frozen models."""
from app.db.models import ModelRevision
from app.services.ai.provider import AssistantProviderError
from app.services.assistant.storage import owned_row

def assert_current_model(db,p,context):
    # An unanchored discussion has no frozen model to refresh and cannot save geometry.
    if not any(context.get(k) for k in ('modelRevisionId','scenarioId','siteSelectionVersionId')):return
    if context.get('modelRevisionId'):owned_row(db,'model_revisions',p,context['modelRevisionId'])
    query=db.query(ModelRevision).filter_by(project_id=p)
    if context.get('scenarioId'):query=query.filter_by(design_scenario_id=int(context['scenarioId']))
    latest=query.order_by(ModelRevision.id.desc()).first()
    if (str(latest.id) if latest else None)!=context.get('modelRevisionId'):
        raise AssistantProviderError('CONTEXT_REFRESH_REQUIRED')
