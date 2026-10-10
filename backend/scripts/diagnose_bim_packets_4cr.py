"""Offline request reconstruction and byte accounting. No model/HTTP calls."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.experimental.bim_authoring import stage_packet,stage_context
from app.experimental.cad_contract import digest


def serialized(value):return json.dumps(value,separators=(",",":"),default=str)


def measure(system,packet):
    user=serialized(packet)
    body=dict(model="Qwen/Qwen3.5-397B-A17B",messages=[dict(role="system",content=system),dict(role="user",content=user)],
        temperature=.1,max_tokens=3500,response_format={"type":"json_object"})
    content=len(system.encode())+len(user.encode())
    return dict(systemBytes=len(system.encode()),userBytes=len(user.encode()),messageContentBytes=content,
        completeBodyBytes=len(serialized(body).encode()),jsonFramingAndControlsBytes=len(serialized(body).encode())-content,
        schemaBytes=len(serialized(packet["outputSchema"]).encode()),
        packetFieldBytes={k:len(serialized(v).encode()) for k,v in packet.items()},
        conservativeCanaryInputReservation=content+1024)


def diagnose():
    output=Path(__file__).resolve().parents[1]/".cad-proof-output"
    original=json.loads((output/"4cr-original.json").read_text())
    frozen=original["frozen"]
    old=original["originalPacket"]
    new=stage_packet("UNDERSTAND",request_text=frozen["userRequest"])
    new["trustedContext"]=stage_context("UNDERSTAND",frozen,digest(frozen))
    system=new.pop("instruction")
    old_measure=measure(old["instruction"],old)
    new_measure=measure(system,new)
    old_retry=measure(old["instruction"],{**old,"repair":original["originalRepair"]})
    result=dict(original=old_measure,optimized=new_measure,originalRetry=old_retry,
        reductionPercent=round(100*(1-new_measure["messageContentBytes"]/old_measure["messageContentBytes"]),2),
        tokenizer="Actual tokenizer unavailable locally; bytes measured, token counts below estimates only",
        empiricalTokenEstimate=round(new_measure["messageContentBytes"]*7143/old_measure["messageContentBytes"]),
        canary=dict(status="PREPARED_NOT_EXECUTED_REQUIRES_NEW_AUTHORIZATION",model="Qwen/Qwen3.5-397B-A17B",stage="UNDERSTAND",
            maximumCalls=1,maximumOutputTokens=3500,timeoutSeconds=45,automaticRetry=False,continueToPlan=False,
            inputReservation=new_measure["conservativeCanaryInputReservation"],nativeBuild=False,automaticApproval=False,modelMutation=False))
    (output/"4cr-measurements.json").write_text(json.dumps(result,indent=2))
    (output/"4cr-understand-canary-request.json").write_text(json.dumps(dict(system=system,payload=new,controls=result["canary"]),indent=2))
    print(json.dumps(result,indent=2))


if __name__=="__main__":diagnose()
