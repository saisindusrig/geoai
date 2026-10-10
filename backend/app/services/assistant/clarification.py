"""Suppress only exclusive questions answered by frozen authoritative context."""
import re

def redundant(question,selection_kind,selected_count):
    text=(question or '').lower()
    if re.search(r'\b(soil|bearing|loads?|height|width|materials?|capacity|groundwater|elevation|clearance|slope|survey|code|dimensions?|distance|amount|thickness|how much)\b',text):return False
    if re.search(r'\b(and|also|additionally)\b',text) and not re.search(r'\b(starts?\s*(?:and|/)\s*ends?|start\s*/\s*end|two endpoint|two point)\b',text):return False
    asks=bool(re.search(r'\b(select|mark|specify|provide|which|where|indicate|identify)\b',text))
    if not asks:return False
    if selection_kind=='ENDPOINTS' and re.search(r'\b(endpoints?|two points?|start|ends?)\b',text):return True
    if selection_kind=='AREA' and re.search(r'\b(area|plot|boundary)\b',text):return True
    return selected_count==1 and bool(re.search(r'\b(which|select|identify)\b.*\b(component|object|wall|column|beam|door|window)\b',text))

def suppress_intent(intent,selection_kind,selected_count,diagnostics):
    if intent.needs_clarification and redundant(intent.clarification_question,selection_kind,selected_count):
        diagnostics.append({'event':'REDUNDANT_CLARIFICATION_SUPPRESSED','source':'FROZEN_CONTEXT'})
        return intent.model_copy(update={'needs_clarification':False,'clarification_question':None})
    return intent
