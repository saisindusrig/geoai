"""Bounded catalogue-aware decomposition; model enrichment remains policy-gated."""
import re
from app.core.project_catalog import ASSET_DEFINITIONS
from app.core.asset_families import asset_definition

ALIASES={key.replace("_"," "):key.upper() for key in ASSET_DEFINITIONS}
ALIASES.update({"approach road":"APPROACH_ROAD","drainage":"DRAINAGE","stormwater drainage":"DRAINAGE","utility crossing":"UTILITY_CROSSING",
    "parking":"PARKING","grading":"SITE_GRADING","cofferdam":"COFFERDAM","building":"BUILDING","bridge":"BRIDGE",
    "skywalk":"PEDESTRIAN_BRIDGE"})
COUNTS={"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"eight":8,"nine":9,"ten":10}


def decompose(text):
    objective=text
    text=text.lower()
    matches=[]
    for phrase,asset_type in sorted(ALIASES.items(),key=lambda item:len(item[0]),reverse=True):
        expression=r"\b(?:(one|two|three|four|five|six|seven|eight|nine|ten|\d+)\s+)?"+re.escape(phrase)+r"(s)?\b"
        for match in re.finditer(expression,text):
            if any(match.start()<end and match.end()>start for start,end,*_ in matches):continue
            raw=match[1];count=COUNTS.get(raw,int(raw) if raw and raw.isdigit() else 1)
            assumed=not raw and asset_type=="APPROACH_ROAD" and bool(match[2])
            matches.append((match.start(),match.end(),asset_type,2 if assumed else min(count,20),assumed))
    result=[]
    for _,__,asset_type,count,assumed in sorted(matches):
        definition=asset_definition(asset_type)
        for i in range(count):
            if len(result)==100:return result
            result.append({"id":f"A{len(result)+1:02d}","assetType":asset_type,"assetFamily":definition["family"],
                "requestedAssetName":f"{definition['displayName']} {i+1}" if count>1 else definition["displayName"],
                "requirements":(["Assumption: two approach roads; confirm the quantity and connections."] if assumed else [])+["User objective: "+objective[:3900]]})
    return result or [{"id":"A01","assetType":"UNREGISTERED_CIVIL_ASSET","assetFamily":"CUSTOM","requestedAssetName":text[:255] or "Civil project"}]
