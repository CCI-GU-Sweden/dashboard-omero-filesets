const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

test('storage charts use only total storage when billing is disabled', async () => {
  function element() {return {value: '30', textContent: '', addEventListener() {}, append() {}, removeAllListeners() {}, on() {}};}
  const elements = Object.fromEntries(['history-period', 'history-status', 'refresh', 'ranking-limit', 'groupRankingChart', 'history-group'].map(id => [id, element()]));
  elements['ranking-limit'].value = '10';
  const calls = [];
  const context = {
    document: {getElementById: id => elements[id] || null, querySelectorAll: () => [], createElement: element},
    URLSearchParams, Intl, Date,
    fetch: async url => ({ok: true, json: async () => url.includes('/history')
      ? {metric: 'bytes', history: [{date: '2026-11-01', total: 2}]}
      : url.includes('/overview') ? {billing_enabled: false, metrics: {}, groups: [{id: '42', name: 'A', total: 2}]}
      : {groups: []}}),
    Plotly: {react: async (id, traces) => calls.push({id, traces})},
  };
  vm.runInNewContext(fs.readFileSync('omero_filesets/static/js/storage_dashboard.js', 'utf8'), context);
  await new Promise(resolve => setImmediate(resolve));
  for (const id of ['omeroChart', 'groupRankingChart']) {
    const call = calls.find(entry => entry.id === id);
    assert.ok(call);
    assert.equal(call.traces.length, 1);
    assert.equal(call.traces[0].name, 'Total');
  }
});
