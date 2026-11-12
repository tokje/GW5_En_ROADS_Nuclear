// extract_enroads.js
// ---------------------------------------------------------------------------
// Exports the data behind En-ROADS graphs to a CSV file.
//
// How to use (one simulation at a time):
//   1. Open a scenario link from Appendix A of the report in Chrome/Edge/Firefox.
//   2. Close the welcome dialog.
//   3. Open the developer console (F12 -> Console), paste this whole file,
//      edit RUN_NAME below if you like, and press Enter.
//   4. A file  enroads_<RUN_NAME>.csv  is downloaded. Put it in  analysis/data/.
//
// The script selects each graph from the "Graphs" menu, reads the plotted data
// (annual values 1990-2100) and writes one row per graph, series and year:
//   graph,series,year,value
// For single-variable graphs, series is "baseline" or "scenario".
// For "Global Sources of Primary Energy", series is the energy source.
// ---------------------------------------------------------------------------

(async () => {
  const RUN_NAME = window.RUN_NAME || 'run';   // set window.RUN_NAME before pasting to rename

  const GRAPHS = [
    'Temperature Change',
    'Greenhouse Gas Net Emissions',
    'Nuclear Primary Energy Demand',
    'Nuclear Capacity',
    'Global Sources of Primary Energy',
    'Price of Electricity',
    'Average Price of Energy to Consumers',
    'Net Revenue from Energy Taxes & Subsidies',
    'GDP per Capita',
    'GDP per Capita Growth Rate',
    'Reduction in GDP from Climate Impacts',
    'Air Pollution from Energy',
  ];

  // Line colours used by En-ROADS (v26.x) to identify the series.
  const LINE = { '#000000': 'baseline', '#00b6f1': 'scenario' };
  const SOURCE = {
    '#5b2b2f': 'Coal', '#cc3b09': 'Oil', '#0063b0': 'Natural gas',
    '#00a651': 'Renewables', '#e55aa1': 'Bioenergy', '#85d2dd': 'Nuclear',
    '#f79554': 'New zero-carbon',
  };

  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const norm = s => s.normalize('NFKD').replace(/[^A-Za-z0-9]/g, '').toLowerCase();

  // Close the welcome dialog if it is still open.
  document.querySelectorAll('button').forEach(b => {
    if (b.textContent.trim() === 'Get Started') b.click();
  });
  await sleep(500);

  async function selectGraph(name) {
    const item = [...document.querySelectorAll('li.menuitem')]
      .find(li => norm(li.querySelector('.text')?.textContent || '') === norm(name));
    if (!item) throw new Error('Graph not found in menu: ' + name);
    (item.querySelector('.menuitem-content') || item).click();
    await sleep(2500);                                  // let the chart redraw
    // The most recently created chart is the one just selected.
    return Object.values(Chart.instances).sort((a, b) => b.id - a.id)[0];
  }

  const rows = [['graph', 'series', 'year', 'value']];
  for (const g of GRAPHS) {
    const chart = await selectGraph(g);
    for (const ds of chart.data.datasets) {
      const col = String(ds.borderColor || ds.backgroundColor || '').toLowerCase();
      const series = g === 'Global Sources of Primary Energy' ? SOURCE[col] : LINE[col];
      if (!series) continue;                            // skip reference lines
      for (const p of ds.data) {
        if (p && Number.isFinite(+p.y)) rows.push([g, series, p.x, +p.y]);
      }
    }
  }

  const csv = rows.map(r => r.map(v => /[",]/.test(String(v))
    ? '"' + String(v).replace(/"/g, '""') + '"' : v).join(',')).join('\n');

  // Record which settings the data came from.
  const header = '# url=' + location.href + '\n';

  window.ENROADS_CSV = header + csv;                    // also kept in memory
  const a = document.createElement('a');
  a.href = URL.createObjectURL(new Blob([window.ENROADS_CSV], { type: 'text/csv' }));
  a.download = 'enroads_' + RUN_NAME + '.csv';
  a.click();
  console.log('Exported', rows.length - 1, 'values to', a.download);
})();
