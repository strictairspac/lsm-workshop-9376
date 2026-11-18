import{revisions}from'../stores/revisions.js';
import{create,publish}from'../api/revisions.js';
import{header}from'../components/common/header.js';
import{table}from'../components/common/table.js';
import{badge}from'../components/common/badge.js';
import{REVISION_STATUSES,OPERATIONS}from'../constants/enums.js';
import{esc,json}from'../utils/html.js';
import{submit,notify}from'../hooks/feedback.js';
import{session}from'../stores/session.js';
const SAMPLE='[\n  {"op":"put","key":"sensor-09","value":"20.1","event_time":"2026-11-18T13:05:00Z"},\n  {"op":"delete","key":"sensor-05","event_time":"2026-11-18T10:40:00Z"}\n]';
const opLine=o=>`${o.event_time}  ${OPERATIONS[o.op]||o.op}  ${o.key}${o.op==='put'?' = '+o.value:''}`;
function diffBlock(x){
  if(x.status!=='published')return'';
  const diff=x.diff&&x.diff.length?table(['小时 (UTC)','修订前峰值','修订后峰值'],x.diff.map(d=>[esc(d.hour.slice(0,13)+'时'),d.before===null?'—':d.before,'<strong>'+d.after+'</strong>'])):'<p class="helper">本次切换没有改变任何已发布小时的峰值。</p>';
  const rec=x.recomputed&&x.recomputed.length?x.recomputed.map(h=>'<span class="badge">'+esc(h.slice(0,13))+'时</span>').join(' '):'<span class="badge">无</span>';
  return`<div class="panel subtle"><h3>修订前后峰值</h3>${diff}<p class="helper">实际重算的小时（只重算受影响小时）：${rec}</p><p class="helper">影响起点 ${esc((x.affected_from||'').slice(0,13))} 时 · 发布序号 #${x.publish_seq} · ${esc(x.published_at||'')}</p></div>`;
}
function publishForm(x,writable){
  if(!writable||x.status==='published')return'';
  const label=x.status==='switching'?'恢复切换（重试幂等）':'发布切换';
  return`<form class="publish" data-id="${x.id}"><div class="actions"><button type="submit" class="primary">${label}</button><label style="margin:0"><input type="checkbox" name="simulate_crash" style="width:auto"> 演练：切换前中断</label><label style="margin:0">延迟秒 <input type="number" name="delay_seconds" min="0" max="10" value="0" style="width:70px"></label></div></form>`;
}
export async function revisionsPage(el){
  const rows=await revisions.load();
  const writable=session.get().role!=='viewer';
  el.innerHTML=header('02','补传迟到记录，整批一次性切换','每个修订批次是一组带发生时间的覆盖/删键操作。发布即原子切换：要么整批生效，要么不生效；中断可恢复，同批重试只生效一次。')
  +'<p class="modelnote">切换期间仍可提交新批次；新批次留到下一次结算。切换与结算共用同一把序列化锁，已发布峰值不会半更新。</p>'
  +`<div class="split"><section class="panel"><span class="material-tag">REVISIONS / ${rows.length}</span>${rows.map(x=>`<article class="record"><h3>${esc(x.name)}</h3><p class="muted">${esc(x.note)}</p><p>${badge(REVISION_STATUSES,x.status)} <span class="badge">${x.op_count} OPS</span>${x.publish_seq?`<span class="badge">SEQ #${x.publish_seq}</span>`:''}</p><details><summary>查看操作（按接收顺序）</summary><pre>${esc(x.ops?x.ops.map(opLine).join('\n'):'（展开详情加载中）')}</pre></details>${publishForm(x,writable)}${diffBlock(x)}</article>`).join('')||'<div class=empty>还没有修订批次。</div>'}</section>`
  +`<aside class="panel"><h2>${writable?'补传修订批次':'输入契约'}</h2>${writable?`<form id="revision-form"><label>批次名称</label><input name="name" required maxlength="120" placeholder="late-delete-sensor05"><label>业务说明</label><input name="note" maxlength="2000" placeholder="说明迟来原因与影响范围"><label>操作 · JSON 数组（提交顺序即接收顺序）</label><textarea name="ops" required rows="9">${SAMPLE}</textarea><div class="actions"><button type="submit" class="primary">登记批次（待发布）</button></div></form>`:''}<p class="helper">每批 1–500 条；键 1–64 字；put 必须带 value（≤200 字）；event_time 为 UTC ISO 时间。乱序到达的记录按发生时间处理，同一时刻按接收顺序。登记后为“待发布”，发布时才整批切换。</p></aside></div>`;
  if(writable){
    el.querySelector('#revision-form').onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const d=Object.fromEntries(new FormData(e.target));try{d.ops=JSON.parse(d.ops)}catch{throw Error('操作 JSON 格式错误，请检查引号与逗号')}await create(d);notify('修订批次已登记（待发布）');await revisionsPage(el)})};
    el.querySelectorAll('form.publish').forEach(f=>f.onsubmit=e=>{e.preventDefault();submit(f,async()=>{const d=Object.fromEntries(new FormData(f));const id=f.dataset.id;try{await publish(id,{simulate_crash:!!d.simulate_crash,delay_seconds:Number(d.delay_seconds||0)});notify('切换完成，整批已生效')}catch(err){notify(err.message)}await revisionsPage(el)})});
  }
}
