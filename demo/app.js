/* Saved CSV replay. No remote APIs, imputation, trained model or availability claim. */
function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/), keys = lines.shift().split(',');
  return lines.map(line => Object.fromEntries(line.split(',').map((v, i) => [keys[i],
    v !== '' && /^-?\d+(\.\d+)?$/.test(v) ? Number(v) : v])));
}
function inPeriod(row, period) {
  const h = Number(row.timestamp.slice(11, 13));
  return period === 'all_day' || (period === 'commute' && [7,8,9,16,17,18,19].includes(h)) ||
    (period === 'morning' && [7,8,9].includes(h)) || (period === 'evening' && [16,17,18,19].includes(h));
}
function metric(rows, model) {
  if (!rows.length) return {n:0, mae:null, rmse:null};
  const errors = rows.map(r => r[model] - r.actual);
  return {n:rows.length, mae:errors.reduce((s,e)=>s+Math.abs(e),0)/rows.length,
    rmse:Math.sqrt(errors.reduce((s,e)=>s+e*e,0)/rows.length)};
}
function actualVisible(row, decision, reveal) { return reveal || row.target_interval_end <= decision; }
if (typeof module !== 'undefined') module.exports = {parseCSV, inPeriod, metric, actualVisible};

if (typeof document !== 'undefined') (async () => {
  const el = id => document.getElementById(id);
  const models = ['persistence','historical','residual_baseline'];
  const names = {persistence:'維持目前值',historical:'歷史同時段',residual_baseline:'殘差校正'};
  const colors = {actual:'#18334c',persistence:'#00857c',historical:'#cf8535',residual_baseline:'#8050b3'};
  const get = async path => {const r = await fetch(path); if(!r.ok) throw Error(`資料載入失敗 ${r.status}`); return parseCSV(await r.text());};
  try {
    const [obs,p15,p30] = await Promise.all([get('/data/baseline/selected-observations.csv'),get('/data/baseline/predictions-15min.csv'),get('/data/baseline/predictions-30min.csv')]);
    const predictions = {15:p15,30:p30};
    const option = (value, text) => {const o=document.createElement('option');o.value=value;o.textContent=text;return o;};
    [...new Set(obs.map(r=>r.link))].sort().forEach(l => el('link').append(option(l,l+' · '+(l.split('>')[0].endsWith('S')?'南向':'北向'))));
    [...new Set(obs.map(r=>r.timestamp.slice(0,10)))].sort().forEach(d=>el('date').append(option(d,d+(d==='2026-09-02'?' · 測試':' · 觀測'))));
    el('date').value='2026-09-02';
    let rows=[], selected=[];
    const fmt = x => x===null?'—':x.toFixed(2);
    const time = s => s.slice(11,16)+(s.slice(0,10)!==el('date').value?'（次日）':'');
    function update(reset=false) {
      rows=predictions[el('horizon').value].filter(r=>r.link===el('link').value && r.timestamp.startsWith(el('date').value) && inPeriod(r,el('period').value));
      selected=rows.length ? rows : obs.filter(r=>r.link===el('link').value && r.timestamp.startsWith(el('date').value) && inPeriod(r,el('period').value));
      if(reset){const old=el('moment').value;el('moment').replaceChildren();selected.forEach((r,i)=>{const d=r.decision_time || plus5(r.timestamp);el('moment').append(option(i,time(d)));});const idx=selected.findIndex(r=>r.timestamp.slice(11,16)==='08:00');el('moment').value=String(idx>=0?idx:Math.min(Number(old)||0,Math.max(0,selected.length-1)));}
      const r=selected[Number(el('moment').value)];
      const decision=r?(r.decision_time || plus5(r.timestamp)):'';
      if(rows.length){const start=plusMinutes(r.target_interval_end,-5);el('detail').textContent=`名義決策：${r.decision_time} +08:00 ｜ 輸入區間：${r.timestamp}–${time(r.decision_time)} ｜ 目標區間：${start}–${time(r.target_interval_end)} ｜ ${models.map(m=>names[m]+' '+fmt(r[m])+'秒').join(' / ')} ｜ 實際值：${el('reveal').checked?fmt(r.actual)+'秒（事後揭露）':'決策當時未知'}`;}
      else el('detail').textContent=r?`觀測區間：${r.timestamp}–${time(decision)}。此日期未保存逐筆預測，不能填入模型結果。`:'所選範圍沒有資料。';
      el('metrics').replaceChildren();models.forEach(m=>{const v=metric(rows,m), tr=document.createElement('tr');[names[m],v.n,fmt(v.mae),fmt(v.rmse)].forEach(t=>{const td=document.createElement('td');td.textContent=t;tr.append(td);});el('metrics').append(tr);});
      el('chart-note').textContent=rows.length?'歷史總覽：各點預測來自不同名義決策時刻，依目標區間對齊；不表示所選時刻已知道整日預測。實際值揭露由上方開關控制。':'僅顯示真實觀測；此日沒有測試預測。';
      draw(r, decision);
      el('status').textContent=`已載入 ${obs.length.toLocaleString()} 筆觀測；15分鐘 ${p15.length} 筆、30分鐘 ${p30.length} 筆測試預測。所選範圍 ${rows.length} 筆。`;
    }
    function plusMinutes(s,n){const d=new Date(s.replace(' ','T')+'+08:00');return new Date(d.getTime()+n*60000+8*3600000).toISOString().slice(0,19).replace('T',' ');}
    function plus5(s){return plusMinutes(s,5);}
    function draw(r, decision){
      const svg=el('chart');svg.replaceChildren();
      const data=rows.length?rows:selected.map(o=>({...o,actual:o.seconds,target_interval_end:plus5(o.timestamp)}));
      if(!data.length)return;
      const node=(tag,attrs,text)=>{const n=document.createElementNS('http://www.w3.org/2000/svg',tag);Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v));if(text)n.textContent=text;svg.append(n);return n;};
      const keys=rows.length?['actual',...models]:['actual'];
      const max=Math.max(1,...data.flatMap(d=>keys.map(k=>d[k])))*1.12;
      const times=data.map(d=>new Date(d.target_interval_end.replace(' ','T')+'+08:00').getTime());
      const x=i=>60+(times[i]-times[0])/Math.max(1,times[times.length-1]-times[0])*920, y=v=>260-v/max*230;
      for(let j=0;j<=4;j++){const val=max*j/4;node('line',{x1:60,x2:980,y1:y(val),y2:y(val),stroke:'#dde7ec'});node('text',{x:50,y:y(val)+4,'text-anchor':'end',fill:'#526676','font-size':12},String(Math.round(val)));}
      for(let j=0;j<=4;j++){const i=Math.round((data.length-1)*j/4);node('text',{x:x(i),y:287,'text-anchor':j===4?'end':'middle',fill:'#526676','font-size':12},time(data[i].target_interval_end));}
      keys.forEach(k=>{let chunks=[],chunk=[];data.forEach((d,i)=>{if(i>0&&times[i]-times[i-1]>300000&&chunk.length){chunks.push(chunk);chunk=[];}if(k!=='actual'||!rows.length||actualVisible(d,decision,el('reveal').checked)){chunk.push(`${x(i)},${y(d[k])}`);}else if(chunk.length){chunks.push(chunk);chunk=[];}});if(chunk.length)chunks.push(chunk);chunks.forEach(c=>node('polyline',{points:c.join(' '),fill:'none',stroke:colors[k],'stroke-width':k==='actual'?2.5:1.8}));});
      const idx=selected.indexOf(r);if(idx>=0)node('line',{x1:x(idx),x2:x(idx),y1:20,y2:260,stroke:'#193047','stroke-dasharray':'5 5'});
    }
    ['link','horizon','date','period'].forEach(id=>el(id).addEventListener('change',()=>update(true)));
    ['moment','reveal'].forEach(id=>el(id).addEventListener('change',()=>update()));
    el('next').addEventListener('click',()=>{el('moment').value=String((Number(el('moment').value)+1)%selected.length);update();});
    update(true);
  } catch(error){el('status').textContent=error.message;}
})();
