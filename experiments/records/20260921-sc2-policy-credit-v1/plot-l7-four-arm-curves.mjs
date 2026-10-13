// Static scientific figure: reuses blue observations / orange trailing-8 mean
// from plot-spb-l7-curve.mjs; evaluations are kept out of training trajectories.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const sharp=require(process.env.SC2_SHARP_MODULE || '/Users/yangjinyue/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const [input,output]=process.argv.slice(2);
if(!input||!output?.endsWith('.png'))throw Error('Usage: node plot-l7-four-arm-curves.mjs INPUT.json OUTPUT.png');
const bytes=fs.readFileSync(input),d=JSON.parse(bytes);
if(d.schema!=='sc2-l7-four-arm-curves-v1'||d.arms.length!==4)throw Error('Unexpected dataset');
for(const a of d.arms){
 if(a.rows.length!==96||a.rows.some((r,i)=>r.step!==i+1||r.games!==8||!Number.isInteger(r.wins)||r.wins<0||r.wins>8||r.real_answers<=0||r.valid_answers!==r.real_answers))throw Error('Invalid rows: '+a.id);
 for(const [key,rowkey] of [['games','games'],['wins','wins'],['real_answers','real_answers'],['valid_answers','valid_answers']])if(a.summary[key]!==a.rows.reduce((n,r)=>n+r[rowkey],0))throw Error('Total mismatch: '+a.id+'/'+key);
 if(a.evaluation.games!==8)throw Error('Evaluation denominator');
}
const W=1680,H=1350,ink='#172e43',muted='#607388',blue='#3274c7',orange='#c67a13',purple='#9672ab',red='#b65249';
const esc=s=>String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const text=(s,x,y,size=22,color=ink,extra='')=>`<text x="${x}" y="${y}" font-size="${size}" fill="${color}" ${extra}>${esc(s)}</text>`;
const line=(x1,y1,x2,y2,color='#dde5ed',width=1,extra='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" ${extra}/>`;
let svg=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img"><title>L7 四组已结束训练：96 步实测胜率</title><desc>四个独立面板；蓝线每步八局胜率，橙虚线过去八步平均。Qwen同seed严格训练验收失败；SpB随机终评待入场。所有观察点保留，没有填零或插值。</desc><rect width="100%" height="100%" fill="#f7f9fc"/><g font-family="Arial Unicode MS, Heiti SC, sans-serif">`;
svg+=text('L7 · 四组训练曲线｜均已采样至 global step 96',56,58,36,ink,'font-weight="bold"');
svg+=text(`每步 8 局 · 训练与终评分开 · 状态核验 ${d.status_observed_at.slice(0,19).replace('T',' ')} 北京时间`,56,101,23,muted);
svg+=line(58,151,108,151,blue,3)+text('逐步实测胜率',121,158,22);
svg+=line(358,151,408,151,orange,4,'stroke-dasharray="9 6"')+text('过去 8 步均值（64 局）',421,158,22);
svg+=line(783,138,783,162,purple,2,'stroke-dasharray="5 4"')+text('自身 CP 恢复边界',799,158,22);
svg+=`<rect x="1170" y="142" width="15" height="15" fill="none" stroke="${red}" stroke-width="2"/>`+text('历史梯度精度缺口',1199,158,22);
for(const [i,a] of d.arms.entries()){
 const px=56+(i%2)*804,py=200+Math.floor(i/2)*514,pw=764;
 const L=px+57,R=px+732,T=py+151,PH=228;
 const x=s=>L+(s-1)/95*(R-L),y=v=>T+PH-10-v/100*(PH-20);
 const pct=(100*a.summary.wins/a.summary.games).toFixed(1),e=a.evaluation;
 svg+=`<rect x="${px}" y="${py}" width="${pw}" height="486" rx="12" fill="white" stroke="#dfe6ee"/>`;
 svg+=text(a.title,px+20,py+36,28,ink,'font-weight="bold"');
 svg+=text(`训练 ${a.summary.wins}/${a.summary.games} 胜 · ${pct}%`,px+20,py+73,24);
 svg+=text(`配对独评：CP2 ${e.cp2_wins}/8 → CP96 ${e.cp96_wins===null?'待评':e.cp96_wins+'/8'}`,px+20,py+106,22,muted);
 svg+=text(a.status,px+20,py+136,19,a.id==='qwen_same'?red:(a.id==='spb_random'?orange:muted));
 for(const v of [0,25,50,75,100])svg+=line(L,y(v),R,y(v))+text(v+'%',L-10,y(v)+7,18,muted,'text-anchor="end"');
 for(const v of [1,16,32,48,64,80,96])svg+=line(x(v),T,x(v),T+PH,'#eff3f7')+text(v,x(v),T+PH+27,18,muted,'text-anchor="middle"');
 for(const b of a.boundaries)svg+=line(x(b),T,x(b),T+PH,purple,1.6,'stroke-dasharray="5 4"');
 const vals=a.rows.map(r=>100*r.wins/r.games);
 svg+=`<polyline points="${vals.map((v,j)=>`${x(j+1)},${y(v)}`).join(' ')}" fill="none" stroke="${blue}" stroke-width="2" opacity="0.85" stroke-linejoin="round"/>`;
 const rolling=vals.flatMap((v,j)=>j<7?[]:[`${x(j+1)},${y(vals.slice(j-7,j+1).reduce((n,v)=>n+v,0)/8)}`]);
 svg+=`<polyline points="${rolling.join(' ')}" fill="none" stroke="${orange}" stroke-width="3.8" stroke-dasharray="9 6" stroke-linejoin="round"/>`;
 for(const step of a.gradient_gaps||[])svg+=`<rect x="${x(step)-4}" y="${y(vals[step-1])-4}" width="8" height="8" fill="white" stroke="${red}" stroke-width="1.7"/>`;
 svg+=`<rect x="${L}" y="${T}" width="${R-L}" height="${PH}" fill="none" stroke="#cbd5df"/>`;
 svg+=text('训练 global step', (L+R)/2,T+PH+58,19,muted,'text-anchor="middle"');
 svg+=text(`消费回答合法：${a.summary.valid_answers.toLocaleString('en-US')}/${a.summary.real_answers.toLocaleString('en-US')}（100%）`,px+20,py+463,19,muted);
}
svg+=text('同 seed＝同一步 8 局共享、跨步重抽；独立 seed＝每局从 0–100 有放回抽取。',56,1243,21,muted);
svg+=text('Qwen 随机：1–8 有效前缀 + 9–96 新续训；排除旧失败运行的重复步数，祖先非 bitwise 限制仍在。',56,1278,21,muted);
svg+=text('仅 8 对终评样本；SpB 随机另有启动时序变化。训练胜率与 100% 合法率不证明学习提升或架构优势。',56,1313,21,muted);
svg+='</g></svg>';
fs.writeFileSync(output.replace(/\.png$/,'.svg'),svg);
await sharp(Buffer.from(svg)).png().toFile(output);
console.log(JSON.stringify({input_sha256:crypto.createHash('sha256').update(bytes).digest('hex'),output,points:d.arms.map(a=>({id:a.id,count:a.rows.length,...a.summary}))}));
