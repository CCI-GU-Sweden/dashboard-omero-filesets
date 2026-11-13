(() => {
  const status = document.getElementById('overview-omero-status');
  const ids = {filesets: 'filesets', storage_gb: 'storage', daily_sek: 'billable'};
  fetch('/api/modules/omero/overview', {credentials: 'same-origin'}).then(async response => {
    if (response.status === 403) throw new Error('An administrator must verify your OMERO group access.');
    if (!response.ok) throw new Error('Storage summary is currently unavailable.');
    return response.json();
  }).then(data => {
    if (data.version !== 1 || !Array.isArray(data.metrics)) throw new Error('Storage summary is currently unavailable.');
    for (const metric of data.metrics) {
      if (metric.key === 'status') { status.textContent = metric.value; continue; }
      const id = ids[metric.key];
      if (!id) continue;
      const value = document.getElementById(`overview-omero-${id}`);
      const change = document.getElementById(`overview-omero-${id}-change`);
      if (value) value.textContent = metric.value;
      if (change) change.textContent = metric.detail || '';
    }
  }).catch(error => {status.textContent = error.message;});
})();
