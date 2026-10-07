const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const {parseCSV,inPeriod,metric,actualVisible} = require('../demo/app.js');
test('UI metrics reproduce all 12 saved metric rows on identical samples',()=>{
  const metrics=parseCSV(fs.readFileSync('data/baseline/metrics.csv','utf8'));
  for(const h of [15,30]){
    const rows=parseCSV(fs.readFileSync(`data/baseline/predictions-${h}min.csv`,'utf8'));
    for(const expected of metrics.filter(r=>r.horizon_minutes===h)){
      const actual=metric(rows.filter(r=>inPeriod(r,expected.period)),expected.model);
      assert.equal(actual.n,expected.n);
      assert.ok(Math.abs(actual.mae-expected.mae_seconds)<1e-9);
      assert.ok(Math.abs(actual.rmse-expected.rmse_seconds)<1e-9);
    }
  }
});
test('actual target remains hidden until interval end, including midnight',()=>{
  const row={target_interval_end:'2026-09-03 00:00:00'};
  assert.equal(actualVisible(row,'2026-09-02 23:30:00',false),false);
  assert.equal(actualVisible(row,'2026-09-03 00:00:00',false),true);
  assert.equal(actualVisible(row,'2026-09-02 23:30:00',true),true);
});
test('no forecast rows is explicit, not a zero error claim',()=>{
  assert.deepEqual(metric([],'persistence'),{n:0,mae:null,rmse:null});
});
