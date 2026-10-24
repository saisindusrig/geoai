import type { AssistantAvailability, AssistantEvent } from "./site-assistant";
export function availabilityReason(status: AssistantAvailability | null) {
  if (!status) return "Could not check the connection. Refresh availability manually.";
  if (status.code === "DAILY_REQUEST_LIMIT") return status.requestAllowance === 3
    ? "The approved live test has used all 3 turns. No additional inference is approved. This is a test-turn limit, not a token or money limit."
    : "The configured request limit has been reached. No further request was sent.";
  if (status.code === "TOKEN_LIMIT") return "This request exceeds the remaining token allowance. No further inference was requested.";
  if (status.code === "BUDGET_LIMIT") return "This request exceeds the approved application budget, including retained reservations. Estimates are not actual provider charges.";
  return status.message;
}
export function activityLabel(busy: boolean, events: AssistantEvent[]) {
  if (!busy) return null;
  const last = [...events].reverse().find(e => ["delta","tool_start","plan","progress"].includes(e.type));
  if (last?.type === "tool_start") return "Checking your project";
  if (last?.type === "plan") return "Preparing an action";
  if (last?.type === "progress" && /context|project|saved/i.test(last.text || "")) return "Checking your project";
  return "Thinking";
}
export const toolLabels: Record<string,string> = {
  list_components:"Listed saved components",read_component_properties:"Read saved object properties",list_saved_results:"Checked available saved results",read_saved_result:"Read the exact saved result and load case",read_context:"Checked saved project evidence", list_projects:"Listed your projects", read_quantities:"Checked saved quantities",
  read_capabilities:"Checked available analysis methods", read_diagnostics:"Checked diagnostics",
};

/** Availability is independent of completed historical tasks. Fail closed while unknown. */
export function canSendAssistant(status: AssistantAvailability | null) {
  return status?.enabled === true && status.state === "AVAILABLE" && status.canSend !== false;
}
export function availabilityLabel(status: AssistantAvailability | null) {
  if (!status) return "Checking AI availability…";
  if (canSendAssistant(status)) return "New AI messages available";
  if (status.state === "AWAITING_SPENDING_APPROVAL") return "AI unavailable — awaiting activation";
  const reason = availabilityReason(status);
  return reason && !/^ready[.!]?$/i.test(reason.trim()) ? `AI unavailable — ${reason}` : "AI unavailable — awaiting activation";
}
