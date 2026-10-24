import { expect,it } from "vitest";
import {availabilityReason,activityLabel,availabilityLabel,canSendAssistant} from './assistant-presentation';
it('distinguishes turn, token and budget blocks without inventing charges',()=>{
 const base={enabled:false,state:'RATE_LIMITED' as const,message:'Limit',requestAllowance:3};
 expect(availabilityReason({...base,code:'DAILY_REQUEST_LIMIT'})).toContain('all 3 turns');
 expect(availabilityReason({...base,code:'TOKEN_LIMIT'})).toContain('token allowance');
 expect(availabilityReason({...base,code:'BUDGET_LIMIT'})).toContain('not actual provider charges');
});
it('only derives progress from actual active request events',()=>{
 expect(activityLabel(false,[{type:'tool_start'}])).toBeNull();
 expect(activityLabel(true,[])).toBe('Thinking');
 expect(activityLabel(true,[{type:'plan'}])).toBe('Preparing an action');
 expect(activityLabel(true,[{type:'tool_start',name:'read_context'}])).toBe('Checking your project');
});

it('never reports availability from disabled, unknown or blocked status',()=>{
 expect(availabilityLabel(null)).toBe('Checking AI availability…');
 expect(canSendAssistant(null)).toBe(false);
 expect(availabilityLabel({enabled:false,state:'DISABLED',message:'Ready'})).toBe('AI unavailable — awaiting activation');
 expect(canSendAssistant({enabled:true,state:'AVAILABLE',canSend:false,message:'Blocked'})).toBe(false);
 expect(availabilityLabel({enabled:true,state:'AVAILABLE',message:'Ready'})).toBe('New AI messages available');
});
