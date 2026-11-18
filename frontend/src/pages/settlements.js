import{settlements}from'../stores/settlements.js';
import{create}from'../api/settlements.js';
import{header}from'../components/common/header.js';
import{table}from'../components/common/table.js';
import{badge}from'../components/common/badge.js';
import{SETTLEMENT_STATUSES}from'../constants/enums.js';
import{esc}from'../utils/html.js';
import{submit,notify}from'../hooks/feedback.js';
import{session}from'../stores/session.js';
const summary=x=>{
  if(!x.result)return x.error?'<span class="error">'+esc(x.error)+'</span>':'—';
  const r=x.result,hours=r.hours||[];
  if(!hours.length)return esc(r.note||'无小时写入')+` · 水位线 #${r.watermark}`;
  return hours.map(h=>`${esc(h.hour.slice(11,13))}时→${h.peak}`).join(' · ')+` （水位线 #${r.watermark}）`;
};
export async function settlementsPage(el){
  const rows=await settlements.load();
  const writable=session.get().role!=='viewer';
  el.innerHTML=header('03','选择结算到哪一小时','结算把待结算小时写入已发布峰值。水位线在执行时快照：发布期间到达的修订不进入本次结算，留到下一次。')
  +'<p class="modelnote">worker 异步执行；进程重启会接管 queued/running 任务并幂等重放。演练延迟可拉长发布窗口，观察并发补传被留到下一次结算。</p>'
  +`<div class="split"><section class="panel"><span class="material-tag">SETTLEMENTS / ${rows.length}</span>${table(['ID','结算到 (UTC)','状态','覆盖小时与峰值','提交时间'],rows.map(x=>['#'+x.id,esc(x.up_to_hour.slice(0,13)+'时'),badge(SETTLEMENT_STATUSES,x.status),summary(x),esc(x.created_at||'')]))}<div class="actions"><button id="reload">刷新队列</button></div></section>`
  +`<aside class="panel"><h2>${writable?'提交结算任务':'输入契约'}</h2>${writable?`<form id="settlement-form"><label>结算到哪一小时（整点，UTC）</label><input name="up_to_hour" required placeholder="2026-11-18T11:00:00Z"><label>演练延迟（秒，0–10）</label><input name="delay_seconds" type="number" min="0" max="10" value="0"><div class="actions"><button type="submit" class="primary">提交结算</button></div></form>`:''}<p class="helper">目标必须整点对齐且晚于当前结算水位；同一小时只能结算一次（409）。跨度单次不超过 744 小时。结算执行期间发布的新修订留到下一次结算。</p></aside></div>`;
  el.querySelector('#reload').onclick=()=>settlementsPage(el);
  if(writable)el.querySelector('#settlement-form').onsubmit=e=>{e.preventDefault();submit(e.target,async()=>{const d=Object.fromEntries(new FormData(e.target));await create({up_to_hour:d.up_to_hour,delay_seconds:Number(d.delay_seconds||0)});notify('结算任务已提交，worker 将异步执行');await settlementsPage(el)})};
}
