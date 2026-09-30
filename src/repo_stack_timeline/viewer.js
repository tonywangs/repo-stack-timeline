'use strict';
(() => {
  const report = JSON.parse(document.getElementById('report-data').textContent);
  const $ = id => document.getElementById(id);
  const snapshots = report.snapshots;
  const hasLocks = !!report.lockfile_semantics_version;
  $('analysis-label').hidden = !hasLocks;
  if(hasLocks) {
    document.querySelector('header p:not(.eyebrow)').textContent = report.scope;
    document.querySelector('.eyebrow').textContent = 'REPOSITORY STACK TIMELINE · DECLARATIONS + LOCKFILES / 2';
    document.querySelector('footer').firstChild.textContent = 'Offline committed evidence. JSON schema: ' + report.schema_version + '. ';
    $('view').options[1].textContent = 'All records in snapshot';
  }
  let page = 0;
  const pageSize = 100;
  const node = (tag, text, cls) => { const n = document.createElement(tag); n.textContent = text; if(cls) n.className = cls; return n; };
  const option = (select, value, text) => { const n = node('option', text); n.value = value; select.append(n); };
  snapshots.forEach((s, i) => option($('snapshot'), String(i), `${i + 1} / ${snapshots.length} · ${s.commit.slice(0,12)}`));
  const categories = [...new Set(snapshots.flatMap(s => s.manifests.flatMap(m => m.declarations.map(d => d.category))))].sort();
  categories.forEach(c => option($('category'), c, c));
  function draw() {
    const locks = $('analysis').value === 'lockfiles';
    const i = Number($('snapshot').value), s = snapshots[i];
    $('ecosystem').disabled = locks; $('category').disabled = locks;
    const comparison = i ? report.comparisons[i-1] : null;
    $('previous').disabled = i === 0;
    $('next').disabled = i === snapshots.length - 1;
    $('provenance').textContent = `Commit ${s.commit}\nTree ${s.tree}\nParents ${s.parents.join(', ') || '(root)'}`;
    $('ancestry').textContent = comparison ? `Previous selection relative to this snapshot: ${comparison.ancestry}. Comparisons follow your selection order, not timestamps.` : 'First selection is the baseline. No additions or absences are inferred before it.';
    const warnings = $('warnings'); warnings.replaceChildren();
    const relevant = comparison && $('view').value === 'changes' ? [snapshots[i-1],s] : [s];
    const warningRows = relevant.flatMap(snap => [
      ...(locks ? (snap.lockfiles || []).flatMap(f => f.diagnostics.map(d => `${snap.commit.slice(0,12)} · ${f.path} · ${d.code} · ${d.location || ''} ${d.field || ''}`)) : []),
      ...snap.diagnostics.map(d => `${snap.commit.slice(0,12)} · ${d.path || ''} · ${d.code}`),
      ...snap.manifests.flatMap(m => m.diagnostics.map(d => `${snap.commit.slice(0,12)} · ${m.path} · ${d.code}${d.category ? ' · '+d.category : ''}`))
    ]);
    if(locks && report.lockfile_status === 'incomplete') warningRows.unshift('Incomplete lockfile analysis. Unknown records cannot establish additions or absences.');
    if(warningRows.length) {
      warnings.append(node('h2', `${warningRows.length} coverage notices`));
      const list = node('ul','');
      warningRows.slice(0,100).forEach(text => list.append(node('li',text)));
      warnings.append(list);
      if(warningRows.length > 100) warnings.append(node('p','Showing first 100 notices. Full details are in report.json.'));
    }
    let rows;
    if($('view').value === 'snapshot') {
      rows = s.manifests.flatMap(m => m.declarations.map(d => ({...d, path:m.path, ecosystem:m.ecosystem, kind:'declared', before:null, after:d.values, before_commit:null, after_commit:s.commit, before_blob:null, after_blob:m.blob})));
    } else rows = comparison ? comparison.events : [];
    if(locks) {
      rows = $('view').value === 'snapshot' ? (s.lockfiles || []).flatMap(f => f.records.map(r => ({path:f.path,location:r.location,kind:'recorded',before:null,after:r.metadata,before_commit:null,after_commit:s.commit,before_blob:null,after_blob:f.blob}))) : comparison ? comparison.lockfile_events : [];
      rows = rows.map(r => ({...r,name:(r.location || '(root)') + (r.after?.name || r.before?.name ? ' · ' + (r.after?.name || r.before?.name) : ''),ecosystem:'npm',category:'recorded package'}));
    }
    $('kind').disabled = $('view').value === 'snapshot';
    const search = $('search').value.toLowerCase();
    rows = rows.filter(r => (locks || !$('ecosystem').value || r.ecosystem === $('ecosystem').value) && (locks || !$('category').value || r.category === $('category').value) && ($('view').value === 'snapshot' || !$('kind').value || r.kind === $('kind').value) && (!search || JSON.stringify([r.name,r.path,r.before,r.after]).toLowerCase().includes(search)));
    const pages = Math.max(1,Math.ceil(rows.length / pageSize));
    page = Math.min(page,pages - 1);
    $('summary').textContent = `${rows.length} ${locks ? 'lockfile records / changes' : $('view').value === 'snapshot' ? 'declared dependencies' : 'declaration changes'} match the filters.`;
    const container = $('rows'); container.replaceChildren();
    if(!rows.length) container.append(node('p', i === 0 && $('view').value === 'changes' ? `Baseline selected. Choose “${hasLocks ? 'All records' : 'All declarations'} in snapshot” to inspect its records, or select the next snapshot.` : `No matching ${locks ? 'lockfile records' : 'declarations'}. Check filters and coverage notices before interpreting an empty result.`));
    rows.slice(page * pageSize, (page+1) * pageSize).forEach(r => {
      const detail = document.createElement('details');
      const summary = document.createElement('summary');
      summary.append(node('span',r.kind,'badge '+r.kind), node('span',r.name,'name'), node('span',`${r.ecosystem} · ${r.category}`,'badge'), node('span',r.path,'path'));
      detail.append(summary);
      const evidence = node('div','','evidence');
      ['before','after'].forEach(side => {
        const col = node('div',''); col.append(node('h3',side === 'before' ? 'Before' : 'After'));
        const values = r[side];
        col.append(node('pre',values === null ? (r.kind === 'unknown' ? 'Unavailable; absence is not established.' : locks ? 'No recorded package in the supported scope.' : 'No declaration in the supported scope.') : locks ? JSON.stringify(values,null,2) : values.map(v => v.raw).join('\n')));
        col.append(node('p',`Commit: ${r[side+'_commit'] || '—'}\nPath: ${r.path}\nBlob: ${r[side+'_blob'] || '—'}`,'mono provenance'));
        evidence.append(col);
      });
      if(locks && r.changed_fields) evidence.append(node('p','Changed fields: ' + (r.changed_fields.join(', ') || (r.kind === 'unknown' ? 'unknown' : 'none; record presence changed'))));
      detail.append(evidence); container.append(detail);
    });
    $('page-status').textContent = `Page ${page+1} of ${pages}`;
    $('page-back').disabled = page === 0; $('page-next').disabled = page === pages-1;
  }
  function select(delta) { $('snapshot').value = String(Math.max(0,Math.min(snapshots.length-1,Number($('snapshot').value)+delta))); page = 0; draw(); }
  $('previous').addEventListener('click',() => select(-1)); $('next').addEventListener('click',() => select(1));
  ['analysis','snapshot','view','ecosystem','category','kind'].forEach(id => $(id).addEventListener('change',() => {page=0;draw();}));
  $('search').addEventListener('input',() => {page=0;draw();});
  $('reset').addEventListener('click',() => {['search','ecosystem','category','kind'].forEach(id => $(id).value='');page=0;draw();});
  $('page-back').addEventListener('click',() => {page--;draw();}); $('page-next').addEventListener('click',() => {page++;draw();});
  document.addEventListener('keydown',event => {
    if(event.altKey || event.ctrlKey || event.metaKey) return;
    const form = ['INPUT','SELECT','TEXTAREA','BUTTON','SUMMARY','A'].includes(event.target.tagName);
    if(event.key === 'Escape') { $('search').value='';page=0;draw(); }
    else if(event.key === '/' && !form) {event.preventDefault();$('search').focus();}
    else if(event.key === 'ArrowLeft' && !form) {event.preventDefault();select(-1);}
    else if(event.key === 'ArrowRight' && !form) {event.preventDefault();select(1);}
  });
  draw();
})();
