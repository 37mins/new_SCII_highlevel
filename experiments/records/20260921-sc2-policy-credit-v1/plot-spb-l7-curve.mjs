// Static scientific figure. Palette/rolling convention reused from the earlier
// plot-qwen-l7-long.mjs in this task's visualization directory; no fake points.
import fs from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require('/Users/yangjinyue/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const [input,output]=process.argv.slice(2);
if(!input||!output)throw Error('Usage: node plot-spb-l7-curve.mjs INPUT.json OUTPUT.png');
const d=JSON.parse(fs.readFileSync(input,'utf8')),rows=d.rows,n=rows.length;
if(rows.some((r,i)=>r.step!==i+1||r.games!==8||r.win_rate!==r.wins/8||r.real_answers<=0||r.valid_action_ratio!==r.valid_answers/r.real_answers))throw Error('Invalid or incomplete trajectory');
if(n!==d.summary.last_step||n!==Math.max(...d.recent_returned_ppo.map(r=>r.step)))throw Error('Pending batch included');
if(d.resume.source!=='checkpoint'||!d.resume.model_optimizer_dataloader_load_returned)throw Error('Unverified native resume');
if(rows.some(r=>![r.win_rate,r.valid_action_ratio].every(v=>Number.isFinite(v)&&v>=0&&v<=1)))throw Error('Nonfinite/out-of-range metric');
if(d.complete&&(n!==96||d.full_metrics.length!==96||d.full_metrics.some((r,i)=>r.step!==i+1)||!['short','long'].every(k=>d.terminal[k].status==='completed'&&d.terminal[k].process_exit_code===0&&d.terminal[k].result_equals_done)))throw Error('Invalid completed snapshot');
const W=1440,H=1010,L=125,R=1360,PH=220;
const ink='#172e43',muted='#607388',blue='#3274c7',orange='#c67a13',grid='#dfe7ee',boundary='#8d7c9b';
const x=s=>L+(s-1)/95*(R-L);
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const tx=(s,a,b,size=22,color=ink,extra='')=>`<text x="${a}" y="${b}" font-size="${size}" fill="${color}" ${extra}>${esc(s)}</text>`;
const ln=(a,b,c,e,color=grid,width=1,extra='')=>`<line x1="${a}" y1="${b}" x2="${c}" y2="${e}" stroke="${color}" stroke-width="${width}" ${extra}/>`;
const avg8=vs=>vs.map((v,i)=>i<7?null:vs.slice(i-7,i+1).reduce((a,b)=>a+b,0)/8);
let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img"><title>SpB Level7 同seed训练 ${n}/96步</title><desc>逐步实测蓝线，过去8步均值橙虚线。前两步与续训连续连接，评测不接入折线，未来步数不补零。合法性不等于战略学习。</desc><rect width="100%" height="100%" fill="white"/><g font-family="Arial Unicode MS, Heiti SC, sans-serif">`;
svg+=tx('SpB 5.17B · Level7｜同 seed RL 长训',54,55,34,ink,'font-weight="bold"');
svg+=tx(`截至 ${d.checked_at.slice(0,19).replace('T',' ')} 北京时间 · 已完成 ${n}/96 步 · 节点197`,54,95,23,muted);
svg+=tx(`训练累计 ${d.summary.wins}/${d.summary.games} 胜（${(100*d.summary.wins/d.summary.games).toFixed(1)}%）`,54,143,25);
svg+=tx(`最近8步 ${d.summary.last8_wins}/64 胜（${(100*d.summary.last8_wins/64).toFixed(1)}%）`,730,143,25);
svg+=ln(56,187,105,187,blue,3)+tx('逐步实测（8局）',120,195,22);
svg+=ln(410,187,460,187,orange,4,'stroke-dasharray="9 6"')+tx('过去8步均值',475,195,22);
svg+=ln(820,187,855,187,boundary,2,'stroke-dasharray="6 6"')+tx('step2→3：自身CP2恢复',870,195,22);
const panels=[
 {key:'win_rate',title:'训练胜率（%）',top:270,note:`独评：训练前 ${d.evaluations.pre.wins}/8 → step2 ${d.evaluations.post.wins}/8 → step96 ${d.evaluations.eval96 ? d.evaluations.eval96.wins+'/8' : '待评'}`},
 {key:'valid_action_ratio',title:'实际消费回答合法率（%）',top:620,note:`${d.summary.valid_answers.toLocaleString('en-US')}/${d.summary.real_answers.toLocaleString('en-US')} 合法回答；不等于策略更强`}
];
for(const p of panels){
 const vals=rows.map(r=>r[p.key]*100),mean=avg8(vals),y=v=>p.top+PH-12-v/100*(PH-24);
 svg+=tx(p.title,54,p.top-30,27,ink,'font-weight="bold"')+tx(p.note,R,p.top-30,22,muted,'text-anchor="end"');
 svg+=`<rect x="${x(n)}" y="${p.top}" width="${R-x(n)}" height="${PH}" fill="#f3f5f7"/>`;
 for(const t of [0,25,50,75,100])svg+=ln(L,y(t),R,y(t))+tx(t,L-17,y(t)+8,21,muted,'text-anchor="end"');
 for(const t of [1,8,16,24,32,40,48,56,64,72,80,88,96])svg+=ln(x(t),p.top,x(t),p.top+PH,'#edf1f5')+tx(t,x(t),p.top+PH+29,21,muted,'text-anchor="middle"');
 svg+=ln(x(2.5),p.top,x(2.5),p.top+PH,boundary,1.5,'stroke-dasharray="6 6"');
 svg+=`<polyline points="${vals.map((v,i)=>`${x(i+1)},${y(v)}`).join(' ')}" fill="none" stroke="${blue}" stroke-width="2.5" stroke-linejoin="round"/>`;
 svg+=`<polyline points="${mean.flatMap((v,i)=>v===null?[]:[`${x(i+1)},${y(v)}`]).join(' ')}" fill="none" stroke="${orange}" stroke-width="3.8" stroke-dasharray="9 6" stroke-linejoin="round"/>`;
 vals.forEach((v,i)=>svg+=`<circle cx="${x(i+1)}" cy="${y(v)}" r="2.7" fill="${blue}"/>`);
 svg+=`<rect x="${L}" y="${p.top}" width="${R-L}" height="${PH}" fill="none" stroke="#cad6df"/>`;
 if(n<96)svg+=tx('待完成',x(n)+(R-x(n))/2,p.top+PH/2+7,20,muted,'text-anchor="middle"');
 svg+=tx('已完成训练 global step',(L+R)/2,p.top+PH+65,22,muted,'text-anchor="middle"');
}
svg+=tx('每步8局同 seed，跨步重新抽 seed；胜率起伏不能直接解释为学习提升。',54,940,22,muted);
svg+=tx(d.complete?'完整1–96步终态指标已核验；前两步来自自身短训。无插值、补零或评测混入。':'含已验收短训step1–2；仅画已完成批次，不插值、不补零。独评不接入训练折线。',54,977,22,muted);
svg+='</g></svg>';
fs.writeFileSync(output.replace(/\.png$/,'.svg'),svg);
await sharp(Buffer.from(svg)).png().toFile(output);
console.log(JSON.stringify({png:output,steps:n,summary:d.summary,colors:{raw:blue,rolling8:orange}}));
