// Reproducible static scientific plots; no generated or interpolated outcomes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const sharp = require(process.env.SC2_SHARP_MODULE || '/Users/yangjinyue/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const [input, pairedInput, outDir] = process.argv.slice(2);
if (!outDir) throw Error('Usage: node plot-l8-l9-curves-20260927.mjs CURVES.json STATUS-2022.json OUTPUT_DIR');
const data = JSON.parse(fs.readFileSync(input));
const paired = JSON.parse(fs.readFileSync(pairedInput)).l8_completed;
if (data.schema !== 'sc2-l8-l9-curves-v1' || !paired.all_24_result_done_acceptance_equal || !paired.all_8_batches_seed_rng_paired) throw Error('Unverified input schema');
const l8 = data.l8.flatMap(s => s.rows), l9 = data.l9.flatMap(s => s.rows);
for (const [rows, count, wins] of [[l8, 192, 935], [l9, 96, 297]]) {
  if (rows.length !== count || rows.some((r, i) => r.step !== i + 1 || r.games !== 8 || !Number.isInteger(r.wins) || r.wins < 0 || r.wins > 8)) throw Error('Invalid per-step outcomes');
  if (rows.reduce((sum, r) => sum + r.wins, 0) !== wins) throw Error('Unexpected total');
}
const colors = {ink:'#203248', muted:'#566e8b', blue:'#2873ce', orange:'#c87a06', purple:'#9163b6', red:'#ad342f'};
const esc = s => String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
const txt = (s,x,y,size=22,color=colors.ink,attr='') => `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" ${attr}>${esc(s)}</text>`;
const line = (x1,y1,x2,y2,color='#dfe7f0',width=1,attr='') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" ${attr}/>`;
const pct = (w,n) => `${(100*w/n).toFixed(1)}%`;
const start = (h,title) => `<svg xmlns="http://www.w3.org/2000/svg" width="1440" height="${h}" viewBox="0 0 1440 ${h}"><title>${esc(title)}</title><rect width="100%" height="100%" fill="white"/><g font-family="Arial Unicode MS, Heiti SC, sans-serif">`;
const legend = y => line(58,y,107,y,colors.blue,2.6)+txt('每步实测（8 局）',122,y+7)+line(405,y,454,y,colors.orange,4,'stroke-dasharray="9 6"')+txt('最近 8 步均值（64 局）',469,y+7)+line(959,y-13,959,y+10,colors.purple,1.7,'stroke-dasharray="5 5"')+txt('自身 checkpoint 续训边界',975,y+7,21);
function training(rows,T,B,ticks,boundaries) {
  const L=108,R=1380,x=s=>L+(s-1)/(rows.length-1)*(R-L),y=p=>B-p*(B-T);
  let svg='';
  for(const t of [0,.25,.5,.75,1]) svg+=line(L,y(t),R,y(t))+txt(`${t*100}%`,L-14,y(t)+7,19,colors.muted,'text-anchor="end"');
  for(const t of ticks) svg+=line(x(t),T,x(t),B,'#edf2f7')+txt(t,x(t),B+30,19,colors.muted,'text-anchor="middle"');
  for(const b of boundaries) svg+=line(x(b+.5),T,x(b+.5),B,colors.purple,1.8,'stroke-dasharray="5 5"');
  const poly=(points,color,width,attr='')=>`<polyline points="${points.map(([s,p])=>`${x(s)},${y(p)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linejoin="round" ${attr}/>`;
  svg+=poly(rows.map(r=>[r.step,r.wins/8]),colors.blue,2);
  svg+=poly(rows.flatMap((r,i)=>i<7?[]:[[r.step,rows.slice(i-7,i+1).reduce((sum,v)=>sum+v.wins,0)/64]]),colors.orange,4,'stroke-dasharray="9 6"');
  svg+=txt('训练 global step',744,B+66,21,colors.muted,'text-anchor="middle"');
  return svg;
}
let svg=start(1150,'L8 Qwen same：完成的 192 步训练及独立配对终评');
svg+=txt('L8 · Qwen same：完整训练曲线',52,57,35,colors.ink,'font-weight="bold"');
svg+=txt('原始 Qwen → CP96 → 自身 CP192 续训；两段训练与终评均已验收',52,101,23,colors.muted);
svg+=legend(145);
svg+=txt('训练胜率：1–96 步 441/768（57.4%）；97–192 步 494/768（64.3%）',52,198,24);
svg+=training(l8,230,530,[1,16,32,48,64,80,96,112,128,144,160,176,192],[2,96]);
svg+=txt('紫线：CP2 和 CP96 续训边界；每步 8 局共享一个 seed，跨步重抽。',52,638,21,colors.muted);
svg+=line(52,667,1380,667,'#cbd7e4');
svg+=txt('单独终评 · 同一批 64 个新场景 seed · 各模型固定权重 / 0 次更新',52,714,26,colors.ink,'font-weight="bold"');
const evals=[['original','原始 Qwen'],['cp96','CP96'],['cp192','CP192']].map(([key,label])=>({label,...paired.arms[key]}));
const xs=[300,740,1180], T=770,B=987,y=p=>B-p*(B-T);
for(const t of [0,.25,.5,.75,1]) svg+=line(108,y(t),1380,y(t))+txt(`${t*100}%`,94,y(t)+7,19,colors.muted,'text-anchor="end"');
svg+=`<polyline points="${evals.map((r,i)=>`${xs[i]},${y(r.wins/r.games)}`).join(' ')}" fill="none" stroke="${colors.purple}" stroke-width="3" stroke-dasharray="7 5"/>`;
evals.forEach((r,i)=>{svg+=`<circle cx="${xs[i]}" cy="${y(r.wins/r.games)}" r="6" fill="${colors.purple}"/>`+txt(`${r.wins}/${r.games}（${pct(r.wins,r.games)}）`,xs[i],y(r.wins/r.games)-23,24,colors.purple,'text-anchor="middle" font-weight="bold"')+txt(r.label,xs[i],B+34,22,colors.ink,'text-anchor="middle"');});
svg+=txt('只测了这三个固定模型，虚线不表示中间 checkpoint 的评测；未混入上方训练曲线。',52,1070,21,colors.muted);
svg+=txt('训练胜率变高不等于泛化改善：这批 64 局中，CP96 / CP192 均低于原始模型。',52,1107,22,colors.red);
svg+='</g></svg>';
const plots=[['l8-complete-training-eval-20260927',svg]];
svg=start(850,'L9 Qwen same：96 步训练进程已结束，严格验收失败');
svg+=txt('L9 · Qwen same：已执行的 96 步训练',52,57,35,colors.ink,'font-weight="bold"');
svg+=`<rect x="52" y="80" width="1328" height="54" rx="8" fill="#fff1ee"/>`;
svg+=txt('训练进程 exit0；严格验收 failed（CP 清单键错误）。CP96 终评未运行，L10 被阻断。',69,116,23,colors.red);
svg+=txt('768 局自然训练对局：297 胜（38.7%） · 96 条实际返回 PPO 指标',52,175,25);
svg+=legend(217);
svg+=training(l9,260,602,[1,16,32,48,64,80,96],[2]);
svg+=txt('same：每步 8 局共享一个场景 seed，跨步重抽；0% 是该批 0/8 胜，不是有效率为 0。',52,712,21,colors.muted);
svg+=txt('这张图仅描述已执行训练，不等于整组通过验收；pre 7/8 → CP2 5/8，CP96 终评暂无结果。',52,751,21,colors.muted);
svg+=txt('数据核验：2026-09-27 20:55 北京时间。未重跑、未补点；不能据训练曲线断言学习提升。',52,792,21,colors.muted);
svg+='</g></svg>';
plots.push(['l9-executed-training-unaccepted-20260927',svg]);
for(const [name,body] of plots){
  const svgPath=path.join(outDir,name+'.svg'), pngPath=path.join(outDir,name+'.png');
  fs.writeFileSync(svgPath,body);
  await sharp(Buffer.from(body)).png().toFile(pngPath);
  console.log(JSON.stringify({path:pngPath,sha256:crypto.createHash('sha256').update(fs.readFileSync(pngPath)).digest('hex'),svg:svgPath}));
}
