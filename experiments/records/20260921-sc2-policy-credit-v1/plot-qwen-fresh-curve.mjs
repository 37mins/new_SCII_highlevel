// Scientific figure: all observations, trailing eight-step mean, evaluations separate.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require(process.env.SC2_SHARP_MODULE || '/Users/yangjinyue/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const [input,output]=process.argv.slice(2);
if(!input||!output?.endsWith('.png'))throw Error('INPUT.json OUTPUT.png required');
const bytes=fs.readFileSync(input),d=JSON.parse(bytes),rows=d.rows;
if(d.schema!=='sc2-fresh-qwen-same-curve-v1'||rows.length!==96||rows.some((r,i)=>r.step!==i+1||r.games!==8||!Number.isInteger(r.wins)||r.wins<0||r.wins>8||r.valid_answers!==r.real_answers||!Number.isFinite(r.grad_norm)||r.grad_norm<=0||!Number.isFinite(r.reward_mean)))throw Error('Invalid data');
for(const key of ['games','wins','real_answers','valid_answers'])if(d.summary[key]!==rows.reduce((s,r)=>s+r[key],0))throw Error('Totals mismatch');
const W=1440,H=1210,L=116,R=1384,ink='#172e43',muted='#607388',blue='#3274c7',orange='#c67a13';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;');
const text=(s,x,y,size=21,color=ink,extra='')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${color}" ${extra}>${esc(s)}</text>`;
const line=(x1,y1,x2,y2,c='#dde5ed',w=1,extra='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${w}" ${extra}/>`;
const x=s=>L+(s-1)/95*(R-L);
let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img"><title>Fresh Qwen L7 same-seed training, 96 steps</title><rect width="100%" height="100%" fill="#f7f9fc"/><g font-family="Arial Unicode MS, Heiti SC, sans-serif">`;
svg+=text('Qwen L7 · 新同 seed 完整重跑',54,57,35,ink,'font-weight="bold"');
svg+=text('96 次真实 PPO · 768 局 / 660 胜（85.94%） · 3289 / 3289 消费回答合法',54,99,23,muted);
svg+=line(56,139,106,139,blue,2)+text('逐步实测',117,147)+line(303,139,353,139,orange,4,'stroke-dasharray="9 6"')+text('过去 8 步均值（从第 8 步起）',365,147);
const panels=[{label:'训练胜率 (%)',values:rows.map(r=>r.wins/8*100),lo:0,hi:100,ticks:[0,25,50,75,100]},
 {label:'平均回报',values:rows.map(r=>r.reward_mean)},
 {label:'梯度范数 · log₁₀',values:rows.map(r=>r.grad_norm),log:true,lo:-4,hi:3,ticks:[-4,-2,0,2,3]}];
panels.forEach((p,k)=>{
 const T=213+k*270,PH=185;
 if(p.lo===undefined){p.lo=Math.floor(Math.min(...p.values)/5)*5;p.hi=Math.ceil(Math.max(...p.values)/5)*5;p.ticks=Array.from({length:5},(_,i)=>p.lo+(p.hi-p.lo)*i/4);}
 const y=v=>T+PH-8-((p.log?Math.log10(v):v)-p.lo)/(p.hi-p.lo)*(PH-16);
 svg+=text(p.label,L,T-20,24);
 for(const t of p.ticks){const yy=T+PH-8-(t-p.lo)/(p.hi-p.lo)*(PH-16);svg+=line(L,yy,R,yy)+text(p.log?'10^'+t:Number(t.toFixed(1)),L-13,yy+7,18,muted,'text-anchor="end"');}
 for(const t of [1,16,32,48,64,80,96])svg+=line(x(t),T,x(t),T+PH,'#edf1f5')+text(t,x(t),T+PH+27,18,muted,'text-anchor="middle"');
 svg+=line(x(2.5),T,x(2.5),T+PH,'#9672ab',1.5,'stroke-dasharray="4 4"');
 const path=vs=>`<polyline points="${vs.map(([s,v])=>`${x(s)},${y(v)}`).join(' ')}" fill="none" stroke-linejoin="round"`;
 svg+=path(p.values.map((v,j)=>[j+1,v]))+` stroke="${blue}" stroke-width="2"/>`;
 // Arithmetic trailing mean of the actual quantity, then log display if requested.
 svg+=path(p.values.flatMap((v,j)=>j<7?[]:[[j+1,p.values.slice(j-7,j+1).reduce((s,v)=>s+v,0)/8]]))+` stroke="${orange}" stroke-width="4" stroke-dasharray="9 6"/>`;
 svg+=text('训练 global step',(L+R)/2,T+PH+56,19,muted,'text-anchor="middle"');
});
svg+=text('独立于训练曲线的 8 局评测：原始 7/8 → CP2 6/8 → CP96 8/8（复用同一组种子）',54,1066,23);
svg+=text('同 seed：同一步 8 局共享一个场景 seed，跨步重抽；紫线是自身 CP2 → 长段恢复边界。',54,1107,20,muted);
svg+=text('后 8 步 48/64 胜（75%）；曲线并非单调上升。训练胜率及 8 对复用终评不证明泛化提升。',54,1140,20,muted);
svg+=text('2026-09-24 完成 · runtime 5228e9a · binary64-v1 · 原始点保留；旧 same 的精度缺口失败不被改写。',54,1173,19,muted);
svg+='</g></svg>';
fs.writeFileSync(output.replace(/\.png$/,'.svg'),svg);
await sharp(Buffer.from(svg)).png().toFile(output);
console.log(JSON.stringify({points:rows.length,input_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),output}));
