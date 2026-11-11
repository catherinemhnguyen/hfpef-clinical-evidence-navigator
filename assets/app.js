'use strict';

const state = { studies: [], filtered: [], metadata: null };
const $ = id => document.getElementById(id);
const fmt = number => Number(number).toLocaleString('en-US');

function make(tag, className, value) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (value !== undefined) el.textContent = value;
  return el;
}
function detailLink(text, href) {
  const a = make('a', '', text);
  a.href = href;
  a.target = '_blank';
  a.rel = 'noopener noreferrer';
  return a;
}
function addText(parent, tag, cls, value) { const el = make(tag, cls, value); parent.appendChild(el); return el; }
function categoryList(items, key) { return [...new Set(items.map(s => s[key]))].sort((a,b)=>a.localeCompare(b)); }
function populateSelect(el, values) {
  for (const name of values) {
    const opt = document.createElement('option'); opt.value = name; opt.textContent = name; el.appendChild(opt);
  }
}
function updateSummary(meta) {
  $('total-studies').textContent = fmt(meta.studies.length);
  $('total-participants').textContent = fmt(meta.studies.reduce((n,s) => n + s.population.sample_size,0));
  $('total-categories').textContent = String(categoryList(meta.studies,'treatment_category').length);
  $('last-updated').textContent = new Date(meta.updated_at + 'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
}
function cardFor(s) {
  const card = make('article','study-card');
  const top = make('div','card-top');
  addText(top,'span','tag',s.treatment_category);
  addText(top,'span','year',String(s.year));
  card.append(top);
  addText(card,'h3','',s.acronym);
  addText(card,'p','study-title',s.title);
  const meta = make('div','meta-row');
  addText(meta,'span','meta-pill',s.population_group);
  addText(meta,'span','meta-pill','LVEF '+s.population.lvef_eligibility);
  card.append(meta);

  const numbers = make('div','stat-line');
  const n = make('div','stat-block'); addText(n,'div','stat-label','Participants'); addText(n,'div','stat-value',fmt(s.population.sample_size));
  const ef = make('div','stat-block'); addText(ef,'div','stat-label','Publication'); addText(ef,'div','stat-value',String(s.year));
  numbers.append(n,ef); card.append(numbers);

  const result = make('div','result-box'); addText(result,'div','result-label','PRIMARY OUTCOME');
  const p = s.primary_outcomes[0];
  addText(result,'p','',p.name + ' — ' + p.result_text);
  card.append(result);
  const signals = s.primary_outcomes.map(o=>o.significant);
  const allPositive = signals.every(v=>v===true);
  const anyPositive = signals.some(v=>v===true);
  const statusText = allPositive ? '●  All primary endpoints statistically significant' : anyPositive ? '◐  Mixed primary endpoint results' : '○  Primary endpoint(s) not statistically significant';
  addText(card,'span','signal '+(allPositive?'signal-positive':'signal-neutral'),statusText);

  const details = make('details','details');
  details.append(make('summary','','Study details & references'));
  const dc = make('div','details-content');
  addText(dc,'h4','','Study population'); addText(dc,'p','',s.population.summary);
  addText(dc,'p','',s.population.additional_criteria);
  addText(dc,'h4','','Intervention & comparator');
  addText(dc,'p','',s.intervention.name + ' (' + s.intervention.dose + ') vs ' + s.intervention.comparator + '.');
  addText(dc,'h4','','Primary endpoint(s)');
  s.primary_outcomes.forEach(o => {
    const row = make('div','outcome-row');
    addText(row,'p','',o.name + ' · ' + o.analysis);
    addText(row,'p','',o.result_text);
    dc.append(row);
  });
  addText(dc,'h4','','Interpretation'); addText(dc,'p','',s.interpretation);
  addText(dc,'h4','','Read carefully');
  const ul = make('ul'); s.cautions.forEach(c=>addText(ul,'li','',c)); dc.append(ul);
  addText(dc,'h4','','Source publication'); addText(dc,'p','',s.reference.short_citation);
  const refs = make('div','source-links');
  refs.append(detailLink('PubMed ↗',s.reference.pubmed_url),detailLink('DOI ↗','https://doi.org/'+s.reference.doi));
  if (s.reference.clinicaltrials_id) refs.append(detailLink('ClinicalTrials.gov ↗','https://clinicaltrials.gov/study/'+s.reference.clinicaltrials_id));
  dc.append(refs);
  addText(dc,'p','review-note',s.curation.verification_status + ' · source check ' + s.curation.last_source_check);
  details.append(dc); card.append(details);
  return card;
}
function applyFilters() {
  const q = $('search').value.trim().toLocaleLowerCase();
  const cat = $('category').value;
  const pop = $('population').value;
  const sort = $('sort').value;
  state.filtered = state.studies.filter(s => {
    if (cat !== 'all' && s.treatment_category !== cat) return false;
    if (pop !== 'all' && s.population_group !== pop) return false;
    const text = [s.acronym,s.title,s.journal,s.population.summary,s.population.additional_criteria,s.intervention.name,s.intervention.comparator,s.interpretation,s.reference.short_citation,...s.tags,...s.primary_outcomes.flatMap(o=>[o.name,o.result_text])].join(' ').toLocaleLowerCase();
    return text.includes(q);
  });
  state.filtered.sort((a,b)=> sort==='year-asc' ? a.year-b.year : sort==='name' ? a.acronym.localeCompare(b.acronym) : b.year-a.year);
  const list = $('study-list'); list.replaceChildren(...state.filtered.map(cardFor));
  if (!state.filtered.length) {
    list.append(make('div','empty-state','No studies match these filters. Try a broader search.'));
  }
  $('result-count').textContent = 'Showing ' + state.filtered.length + ' of ' + state.studies.length + ' studies';
}
function csvCell(value) { return '"' + String(value ?? '').replaceAll('"','""') + '"'; }
function getCsv(studies) {
  const fields = [
    ['Acronym',s=>s.acronym],['Title',s=>s.title],['Year',s=>s.year],['Category',s=>s.treatment_category],
    ['Population group',s=>s.population_group],['Participants',s=>s.population.sample_size],['LVEF eligibility',s=>s.population.lvef_eligibility],
    ['Intervention',s=>s.intervention.name],['Comparator',s=>s.intervention.comparator],['Primary outcome(s)',s=>s.primary_outcomes.map(o=>o.name).join(' | ')],
    ['Outcome results',s=>s.primary_outcomes.map(o=>o.result_text).join(' | ')],['Interpretation',s=>s.interpretation],
    ['DOI',s=>s.reference.doi],['PMID',s=>s.reference.pmid],['NCT',s=>s.reference.clinicaltrials_id]
  ];
  return [fields.map(([name])=>csvCell(name)).join(','),...studies.map(s=>fields.map(([,get])=>csvCell(get(s))).join(','))].join('\r\n');
}
function download(name,content,type) {
  const blob = new Blob([content],{type}); const url = URL.createObjectURL(blob);
  const a = document.createElement('a');a.href=url;a.download=name;document.body.append(a);a.click();a.remove();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function initialize() {
  try {
    const response = await fetch('data/studies.json');
    if (!response.ok) throw Error('Could not load data/studies.json (HTTP '+response.status+').');
    const meta = await response.json();
    if (!Array.isArray(meta.studies)) throw Error('Expected a studies array in the JSON dataset.');
    state.metadata=meta;state.studies=meta.studies;
    updateSummary(meta);
    populateSelect($('category'),categoryList(state.studies,'treatment_category'));
    populateSelect($('population'),categoryList(state.studies,'population_group'));
    ['search','category','population','sort'].forEach(id => $(id).addEventListener('input',applyFilters));
    $('clear-filters').addEventListener('click',()=>{$('search').value='';$('category').value='all';$('population').value='all';$('sort').value='year-desc';applyFilters();$('search').focus();});
    $('download-json').addEventListener('click',()=>download('hfpef-filtered-studies.json',JSON.stringify({...state.metadata,studies:state.filtered},null,2),'application/json'));
    $('download-csv').addEventListener('click',()=>download('hfpef-filtered-studies.csv','\ufeff'+getCsv(state.filtered),'text/csv;charset=utf-8'));
    applyFilters();
  } catch(error) {
    $('result-count').textContent='Unable to load evidence records.';
    const el=$('error-message');el.hidden=false;
    el.textContent = error.message + ' If you are viewing local files, start a local server: python -m http.server 8000';
  }
}
document.addEventListener('DOMContentLoaded',initialize);
