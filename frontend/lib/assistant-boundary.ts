/** Assistant replies may describe a change, never invoke a model writer. */
export function assistantActionBoundary(action: { type: string } | null | undefined):
  { effect: "READ_ONLY" | "PROPOSAL_ONLY" | "REJECTED"; message?: string } {
  if (!action) return { effect: "READ_ONLY" };
  if (["show_layer", "download", "run_site_analysis"].includes(action.type)) return { effect: "READ_ONLY" };
  if (["update_parameters", "regenerate", "generate_design", "create_proposal", "revise_proposal"].includes(action.type)) {
    return { effect: "PROPOSAL_ONLY", message: "This change requires a reviewed proposal. Proposal execution is not enabled; no model changes were applied." };
  }
  return { effect: "REJECTED", message: "Unsupported assistant action rejected. No model changes were applied." };
}
