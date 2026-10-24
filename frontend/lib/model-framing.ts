/** Frame the whole bounding sphere with a margin in the actual viewport. */
export function modelFitRange(radius:number,verticalFov:number,aspect:number){
  const half=Math.max(.15,Math.min(1.2,verticalFov/2));
  const horizontal=Math.atan(Math.tan(half)*Math.max(.25,aspect));
  return Math.max(1.5,Math.max(.01,radius)/Math.sin(Math.min(half,horizontal))*1.04);
}
