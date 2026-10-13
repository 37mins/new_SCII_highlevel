// Static scientific figure; same colours/rolling-8 definition as L7 plots.
import fs from 'node:fs';
import crypto from 'node:crypto';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const sharp = require(process.env.SC2_SHARP_MODULE || '/Users/yangjinyue/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/sharp');
const [input, output] = process.argv.slice(2);
if (!input || !output?.endsWith('.png')) throw Error('Usage: node plot-l8same-curve.mjs INPUT.json OUTPUT.png');
const bytes = fs.readFileSync(input), d = JSON.parse(bytes), rows = d.rows;
if (d.schema !== 'sc2-l8same-partial-win-curve-v1' || rows.length < 8 || rows.length > 96 || rows.length !== d.last_returned_step) throw Error('Invalid snapshot');
if (rows.some((r, i) => r.step !== i + 1 || r.games !== 8 || !Number.isInteger(r.wins) || r.wins < 0 || r.wins > 8)) throw Error('Invalid observations');
for (const key of ['wins', 'games']) if (d.summary[key] !== rows.reduce((s, r) => s + r[key], 0)) throw Error('Incorrect totals');
const rolling = rows.flatMap((r, i) => i < 7 ? [] : [{step: r.step, pct: rows.slice(i - 7, i + 1).reduce((s, v) => s + v.wins, 0) / 64 * 100}]);
if (d.summary.last8_wins !== rows.slice(-8).reduce((s, r) => s + r.wins, 0) || d.summary.last8_games !== 64) throw Error('Incorrect rolling window');
const W = 1440, H = 910, L = 115, R = 1370, T = 330, B = 695;
const ink = '#1d3047', muted = '#586f89', blue = '#2873ce', orange = '#cc7b0b', purple = '#9063b5';
const esc = s => String(s).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
const text = (s, x, y, size = 22, color = ink, extra = '') => `<text x="${x}" y="${y}" font-size="${size}" fill="${color}" ${extra}>${esc(s)}</text>`;
const line = (x1, y1, x2, y2, color = '#dee6ef', width = 1, extra = '') => `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${color}" stroke-width="${width}" ${extra}/>`;
const x = s => L + (s - 1) / (rows.length - 1) * (R - L), y = pct => B - pct / 100 * (B - T);
const pct = (a, b) => (100 * a / b).toFixed(1) + '%';
const at = d.checked_at_beijing.slice(0, 16).replace('T', ' ');
let svg = `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><title>L8 Qwen same 训练胜率，截至第 ${rows.length} 步</title><desc>蓝线每步八局训练胜率，橙线最近八步算术均值；只含真实完成批次，不补未来数据，不混入评测。</desc><rect width="100%" height="100%" fill="white"/><g font-family="Arial Unicode MS, Heiti SC, sans-serif">`;
svg += text('L8 · Qwen same 训练胜率', 52, 60, 37, ink, 'font-weight="bold"');
svg += text(`进行中 · 截至 ${at} 北京时间 · 原始 Qwen 起训 / 8 卡`, 52, 103, 23, muted);
const cards = [
  ['已完成 PPO 步数', `${rows.length} / 96`, `${rows.length * 8} 局训练对局`],
  ['累计训练胜率', pct(d.summary.wins, d.summary.games), `${d.summary.wins} / ${d.summary.games} 胜`],
  ['最近 8 步胜率', pct(d.summary.last8_wins, 64), `${d.summary.last8_wins} / 64 胜 · 非独立终评`],
];
cards.forEach(([label, value, note], i) => {
  const left = 52 + i * 457;
  svg += `<rect x="${left}" y="130" width="422" height="121" rx="10" fill="#f5f8fc"/>`;
  svg += text(label, left + 20, 162, 20, muted) + text(value, left + 20, 204, 33, ink, 'font-weight="bold"') + text(note, left + 20, 233, 19, muted);
});
svg += line(56, 289, 101, 289, blue, 2.8) + text('每步实测（8 局）', 113, 296, 22);
svg += line(384, 289, 431, 289, orange, 4, 'stroke-dasharray="9 6"') + text('最近 8 步均值（64 局）', 443, 296, 22);
svg += line(856, 275, 856, 300, purple, 2, 'stroke-dasharray="5 5"') + text('自身 CP2 续跑边界', 871, 296, 22);
for (const tick of [0, 25, 50, 75, 100]) svg += line(L, y(tick), R, y(tick)) + text(tick + '%', L - 15, y(tick) + 7, 20, muted, 'text-anchor="end"');
const ticks = [...new Set([1, ...Array.from({length: Math.floor(rows.length / 8)}, (_, i) => (i + 1) * 8), rows.length])];
for (const tick of ticks) svg += line(x(tick), T, x(tick), B, '#eef2f7') + text(tick, x(tick), B + 31, 20, muted, 'text-anchor="middle"');
svg += line(x(2.5), T, x(2.5), B, purple, 1.8, 'stroke-dasharray="5 5"');
const poly = (points, color, width, extra = '') => `<polyline points="${points.map(([s, p]) => `${x(s)},${y(p)}`).join(' ')}" fill="none" stroke="${color}" stroke-width="${width}" stroke-linejoin="round" ${extra}/>`;
svg += poly(rows.map(r => [r.step, 100 * r.wins / 8]), blue, 2.5);
for (const r of rows) svg += `<circle cx="${x(r.step)}" cy="${y(100 * r.wins / 8)}" r="3.5" fill="${blue}"/>`;
svg += poly(rolling.map(r => [r.step, r.pct]), orange, 4, 'stroke-dasharray="9 6"');
svg += text('训练 global step（只画已完成部分）', (L + R) / 2, 760, 22, muted, 'text-anchor="middle"');
svg += text('same：每步 8 局共享场景 seed，跨步重抽；0% 表示该批 0/8 胜，不是回答有效率为 0。', 52, 812, 21, muted);
svg += text('前 2 步为保留的已验收训练前缀，3–34 步从自身 CP2 续跑；不重复计数，不补未来点。'.replace('3–34', `3–${rows.length}`), 52, 846, 21, muted);
svg += text('训练曲线受场景难度变化影响；CP96 终评尚未开始，不能据此断言 RL 学习提升或退化。', 52, 880, 21, muted);
svg += '</g></svg>';
fs.writeFileSync(output.replace(/\.png$/, '.svg'), svg);
await sharp(Buffer.from(svg)).png().toFile(output);
console.log(JSON.stringify({points: rows.length, wins: d.summary.wins, games: d.summary.games, last8: rolling.at(-1), input_sha256: crypto.createHash('sha256').update(bytes).digest('hex'), output}));
