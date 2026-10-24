/** Display interpolation of a STATIC saved case; never a time-history result. */
export function deformationPhase(elapsedSeconds:number,periodSeconds=4){
 if(!Number.isFinite(elapsedSeconds)||!Number.isFinite(periodSeconds)||periodSeconds<=0)return 0;
 return (1-Math.cos(2*Math.PI*Math.max(0,elapsedSeconds)/periodSeconds))/2;
}
