import{published,pending,overview}from'../api/peaks.js';
import{header}from'../components/common/header.js';
import{table}from'../components/common/table.js';
import{esc}from'../utils/html.js';
const keys=a=>a&&a.length?a.map(esc).join('、'):'（空）';
const hourRows=hours=>hours.map(h=>[esc(h.hour.slice(0,13)+'时'),'<strong>'+h.peak+'</strong>',h.start_keys?keys(h.start_keys):h.start,h.end_keys?keys(h.end_keys):h.end,h.source?esc(h.source):'<span class="badge staged">预览 · 未发布</span>']);
export async function peaksPage(el){
  const[ov,pub,pen]=await Promise.all([overview(),published(),pending()]);
  el.innerHTML=header('01','每一小时，最多多少键同时存活','乱序记录按发生时间处理、同一时刻按接收顺序；小时起点承接上一小时的键状态。已发布峰值来自结算水位线之内的修订，待结算为实时预览、不落库。')
  +`<div class="metrics"><div>结算水位（已发布到）<strong>${esc(ov.horizon?ov.horizon.slice(0,13)+'时':'尚未结算')}</strong></div><div>已发布小时<strong>${ov.published_hours}</strong></div><div>待结算小时<strong>${ov.pending_hours}</strong></div><div>待发布/切换中修订<strong>${ov.open_revisions}</strong></div><div>进行中结算<strong>${ov.open_settlements}</strong></div></div>`
  +`<section class="panel"><h2>已发布峰值</h2>${table(['小时 (UTC)','峰值','起点键集','终点键集','来源'],hourRows(pub.hours))}</section>`
  +`<section class="panel subtle"><h2>待结算预览</h2>${pen.truncated?'<p class="error">预览过长，仅显示前 744 小时；请分段结算。</p>':''}${table(['小时 (UTC)','峰值','起点键数','终点键数','状态'],hourRows(pen.hours))}<p class="helper">预览按当前全部已发布修订实时演算；提交结算后才写入已发布峰值。</p></section>
  <div class="actions"><button id="reload">刷新</button></div>`;
  el.querySelector('#reload').onclick=()=>peaksPage(el);
}
