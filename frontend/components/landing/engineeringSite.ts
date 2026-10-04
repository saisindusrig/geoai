/** Synthetic site for the homepage only. One scene unit represents 10 metres. */
export const SITE = { metresPerUnit: 10, bridgeLength: 200, bridgeWidth: 9.6, span: 40, pierStations: [-6,-2,2,6], datum: 600 } as const;
export function terrainHeight(x: number, z: number) {
  const river = Math.sin(z * .24) * 1.5;
  const valley = 1 - Math.exp(-Math.pow((x - river) / 3.1, 2));
  const ridges = 2.1 + Math.sin(x * .44 + z * .19) * .8 + Math.cos(z * .39 - x * .13) * .9;
  const detail = Math.sin(x * 1.8 + z * .8) * .16 + Math.cos(z * 2.4 - x * .65) * .1 + Math.sin(x * 5 + z * 4) * .035;
  return .08 + valley * Math.max(.3, ridges + detail);
}
export function alignmentZ(x: number, offset = 0) { return .0025*x*x + offset; }
export function bridgeGrade(x: number) { return 3.8 + .02*x; }
export function roadGrade(x: number) { return 1.4 + .0006*x*x + .008*x; }
export function roadZ(x: number) { return alignmentZ(x, 6); }
export function smooth01(x: number) { const t=Math.max(0,Math.min(1,x)); return t*t*(3-2*t); }
export function storyPosition(progress: number) {
  const cursor=Math.min(4.9999,Math.max(0,progress)*5);
  return {stage:Math.floor(cursor),progress:cursor-Math.floor(cursor)};
}
/** Numerically integrated demo earthwork only; not a site-survey quantity. */
export function approachEarthwork() {
  let cut=0,fill=0;
  const step=.12;
  for(let x=-17;x<17;x+=step) {
    if(Math.abs(x)<10)continue;
    for(let z=-2.5;z<2.5;z+=step) {
      const weight=1-smooth01((Math.abs(z)-.56)/1.64);
      const change=(bridgeGrade(x)-.08-terrainHeight(x,alignmentZ(x)+z))*weight;
      const volume=change*step*step*1000;
      if(volume>0)fill+=volume;else cut-=volume;
    }
  }
  return {cut:Math.round(cut/10)*10,fill:Math.round(fill/10)*10};
}
