const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const labels = {needs_review:'Needs review', approved:'Approved', research_needed:'Needs evidence', blocked:'Do not contact', rejected:'Rejected', delivered:'Simulated delivery', researching:'Research running'};
let leads=[], selected='avery', workspace={}, dirty=false, pendingAction=null, busy=false;
async function api(path, options={}) {
  const response=await fetch(path,{...options, headers:{'Content-Type':'application/json',...(options.headers||{})}});
  const result=await response.json();
  if(!response.ok) throw new Error(typeof result.detail==='string'?result.detail:'Please check your input.');
  return result;
}
function toast(message){$('toast').textContent=message;$('toast').classList.add('show');setTimeout(()=>$('toast').classList.remove('show'),5000);}
function badge(lead){return `<span class="badge ${esc(lead.state)}">${esc(labels[lead.state])}</span>`;}
async function refresh(){leads=await api('/api/leads');renderQueue();await renderDetail();}
function renderQueue(){
  $('reviewCount').textContent=leads.filter(x=>x.state==='needs_review').length;
  $('approvedCount').textContent=leads.filter(x=>x.state==='approved').length;
  $('researchCount').textContent=leads.filter(x=>x.state==='research_needed').length;
  $('blockedCount').textContent=leads.filter(x=>x.suppressed).length;
  $('total').textContent=leads.length;
  const q=$('search').value.toLowerCase(), f=$('filter').value;
  const filtered=leads.filter(x=>(f==='all'||x.state===f)&&(x.company+' '+x.contact).toLowerCase().includes(q));
  $('leadList').innerHTML=filtered.map(x=>`<button class="lead ${x.id===selected?'selected':''}" data-lead="${esc(x.id)}" aria-pressed="${x.id===selected}"><strong>${esc(x.company)}</strong><span class="person">${esc(x.contact)}</span>${badge(x)}</button>`).join('')||'<p class="empty">No leads match this filter.</p>';
  document.querySelectorAll('[data-lead]').forEach(b=>b.onclick=async()=>{if(dirty&&!confirm('Discard unsaved draft edits?'))return;selected=b.dataset.lead;dirty=false;renderQueue();await renderDetail();});
}
async function renderDetail(){
  const x=leads.find(x=>x.id===selected);if(!x)return;
  const editable=!x.suppressed&&!x.hold&&x.state!=='delivered';
  const locked=!editable?'disabled':'';
  $('detail').innerHTML=`<div class="detail-head"><div><span class="smallcaps">ACCOUNT / ${esc(x.sector)}</span><h2>${esc(x.company)}</h2><p>${esc(x.contact)} · ${x.employee_count == null ? 'Size not established' : x.employee_count + ' employees'}</p></div>${badge(x)}</div><div class="fit"><strong>WHY THIS LEAD / ${x.mode==='live'?'AI-ASSISTED FIT REVIEW':'RULE-BASED FIT REVIEW'}</strong>${esc(x.rationale)}</div><div class="columns"><section><div class="section-label"><h3>Evidence desk</h3><small>${x.sources.length} ${x.mode==='live'?'web sources':'fixture sources'}</small></div>${x.sources.map(s=>`<article class="source"><h4>${esc(s.id)} / ${s.url ? `<a href="${esc(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)}</a>` : esc(s.title)}</h4><div class="meta">${s.synthetic?'':'Retrieved '}${esc(s.date)} · ${esc(x.mode==='live'?'Research reference · content not independently verified':s.origin)}</div><blockquote>${esc(x.mode==='live'?'Cited during AI research. Open the linked page to verify the claims and publication date.':s.excerpt)}</blockquote></article>`).join('')}${x.claims.length?'<div class="smallcaps">DRAFT CLAIM REFERENCES</div>'+x.claims.map(c=>`<p class="claim"><code>${esc(c.source_id)}</code> ${esc(c.text)}</p>`).join(''):''}<p class="hint">${x.mode==='live'?'References were selected by AI and are not verified evidence. Open every source and verify the claims; retrieval date is not publication date.':'Sources are fictional documents, not live web research.'} Source text never grants authority.</p></section><section class="draft"><div class="section-label"><h3>Outreach draft</h3><small>Version ${x.revision} · ${x.mode==='live'?'AI-assisted research':'fixture copy'}</small></div>${x.hold||x.suppressed?`<div class="hold"><strong>${x.suppressed?'Do Not Contact is active':'Evidence hold'}</strong>${esc(x.suppressed?'This contact is suppressed. No approval or simulated delivery is allowed.':x.hold)}</div>`:`<label for="recipient">Recipient</label><input id="recipient" value="${esc(x.recipient)}" ${locked}><label for="subject">Subject</label><input id="subject" maxlength="200" value="${esc(x.subject)}" ${locked}><label for="body">Message</label><textarea id="body" maxlength="5000" ${locked}>${esc(x.body)}</textarea>${x.edited?'<p class="hint">Edited copy: original claim annotations were cleared. Recheck every claim against the evidence.</p>':''}${x.flags.length?`<p class="hold">Quality flags: ${x.flags.map(esc).join(', ')}</p>`:''}<button id="save" class="secondary" ${locked}>Save edits · revoke approval</button>${x.state==='needs_review'?'<label class="approval-check"><input type="checkbox" id="verified">I checked the recipient, factual claims, and business relevance of this exact draft.</label>':''}<div class="actions"><button id="approve" class="primary" disabled>Approve draft</button>${x.state==='approved'?'<button id="simulate" class="primary">Simulate delivery</button>':''}</div><p class="hint">${x.state==='delivered'?'Delivery was simulated. Nothing left this application.':'Approval binds to the current draft. Editing it requires a new approval.'}</p>`}<div class="actions"><button id="research" class="secondary" ${x.suppressed||x.state==='delivered'?'disabled':''}>Research more</button><button id="reject" class="secondary" ${x.suppressed||x.state==='delivered'?'disabled':''}>Reject</button><button id="suppress" class="danger" ${x.suppressed?'disabled':''}>Do Not Contact</button></div></section></div><section class="audit"><h3>Decision history</h3><div id="events"><p class="hint">Loading history…</p></div></section>`;
  ['recipient','subject','body'].forEach(id=>{if($(id))$(id).oninput=()=>{dirty=true;if($('verified'))$('verified').checked=false;if($('approve'))$('approve').disabled=true;if($('simulate'))$('simulate').disabled=true;};});
  if($('verified'))$('verified').onchange=()=>{$('approve').disabled=dirty||!$('verified').checked||x.flags.length>0;};
  if($('save'))$('save').onclick=()=>run('edit',{recipient:$('recipient').value,subject:$('subject').value,body:$('body').value});
  if($('approve'))$('approve').onclick=()=>run('approve');
  if($('simulate'))$('simulate').onclick=()=>run('simulate');
  ['research','reject','suppress'].forEach(command=>{$(command).onclick=()=>openAction(command);});
  renderLiveExtra(x);
  const id=selected;
  try{const events=await api(`/api/leads/${id}/events`);if(selected!==id)return;$('events').innerHTML=events.map(e=>`<div class="event"><strong>${esc(e.action.toUpperCase())}</strong><time>${esc(new Date(e.timestamp).toLocaleString())}</time><p>${esc(e.detail)}</p></div>`).join('')||'<p class="hint">No decisions yet. Every action is recorded here.</p>';}catch(e){toast(e.message);}
}
function openAction(command){
  pendingAction=command;
  const descriptions={research:['Request more evidence','Record the question a researcher needs to answer. This demo records the request; it does not search the web.'],reject:['Reject this draft','Explain why this outreach does not deserve a conversation.'],suppress:['Do Not Contact','Block this contact and revoke any approval. This demo does not offer an automatic unsuppress action.']};
  $('actionTitle').textContent=descriptions[command][0];$('actionDescription').textContent=descriptions[command][1];$('reason').value='';$('actionDialog').showModal();$('reason').focus();
}
async function run(command,extra={}){
  if(busy)return;
  if(command!=='edit'&&dirty){toast('Save or discard your edits before recording a decision.');return;}
  busy=true;
  const x=leads.find(x=>x.id===selected);
  try{
    await api(command==='edit'?`/api/leads/${x.id}/draft`:`/api/leads/${x.id}/${command}`,{method:command==='edit'?'PUT':'POST',body:JSON.stringify({revision:x.revision,...extra})});
    dirty=false;$('actionDialog').close();await refresh();toast(command==='simulate'?'Simulated delivery recorded. No email was sent.':command==='edit'?'Saved. Any prior approval has been revoked.':'Decision recorded.');
  }catch(e){toast(e.message);}finally{busy=false;}
}
$('confirmAction').onclick=()=>run(pendingAction,{reason:$('reason').value});
$('cancelAction').onclick=$('closeAction').onclick=()=>$('actionDialog').close();
$('search').oninput=$('filter').onchange=renderQueue;
$('offerNav').onclick=()=>{$('offerDialog').showModal();};$('closeOffer').onclick=()=>$('offerDialog').close();
$('queueNav').onclick=()=>document.querySelector('.workbench').scrollIntoView({behavior:'smooth'});
window.addEventListener('beforeunload',e=>{if(dirty){e.preventDefault();e.returnValue='';}});
(async()=>{try{workspace=await api('/api/workspace');initializeLive();$('offerContent').innerHTML=`<h3>${esc(workspace.offer.name)}</h3><p>${esc(workspace.offer.description)}</p><h4>Ideal customer profile</h4><p>${esc(workspace.offer.icp)}</p><h4>Content boundaries</h4><p>${esc(workspace.offer.prohibited)}</p><p class="hint">Configuration is fixed for this demo. Seller onboarding is a later milestone.</p>`;await refresh();}catch(e){$('detail').innerHTML='<p class="empty">Cannot load the workspace. Confirm the FastAPI server is running, then reload.</p>';toast(e.message);}})();

function initializeLive(){
  const button=document.createElement('button');button.id='newLead';button.className='primary';button.textContent='+ Add live lead';
  document.querySelector('.queue').prepend(button);
  const dialog=document.createElement('dialog');dialog.id='liveDialog';
  dialog.innerHTML=`<div class="dialog-head"><h2>Add a live lead</h2><button type="button" class="icon" id="closeLive" aria-label="Close">×</button></div><p>Start with a company you know. Use public business context only. No real email address is required; delivery stays simulated.</p><form id="liveForm"><label for="company">Company name</label><input id="company" required minlength="2" maxlength="160"><label for="domain">Company website / domain</label><input id="domain" required maxlength="253" placeholder="company.com"><label for="contact">Known contact & role, or relevant department</label><input id="contact" required minlength="2" maxlength="160" placeholder="Operations team"><label for="seller">Your company / sender name</label><input id="seller" required minlength="2" maxlength="160"><label for="offer">Your offering — factual capabilities only</label><textarea id="offer" required minlength="20" maxlength="2000" rows="3" placeholder="What you can actually deliver; no unverified savings claims."></textarea><label for="icp">Ideal customer criteria</label><textarea id="icp" required minlength="10" maxlength="1500" rows="2" placeholder="Industry, business workflow, and required evidence of fit."></textarea><label class="approval-check"><input id="apiConsent" type="checkbox" required>I understand that running research sends this context to OpenAI and incurs API usage charges. No email is sent.</label><p class="hint">${workspace.live.configured?'API key is configured locally.':'API key not configured yet. Run configure_openai.py, then restart the server.'} Model: ${esc(workspace.live.model)}. Up to 2 model responses and 2 search tool calls per run. Daily caps: 3 runs per lead / 20 total (UTC). These are request caps, not a guaranteed dollar budget.</p><div class="dialog-actions"><button class="primary" type="submit">Add lead · no API call yet</button></div></form>`;
  document.body.append(dialog);
  button.onclick=()=>{if(dirty&&!confirm('Discard unsaved edits?'))return;dialog.showModal();};
  $('closeLive').onclick=()=>dialog.close();
  $('liveForm').onsubmit=async e=>{e.preventDefault();const submit=e.target.querySelector('[type=submit]');submit.disabled=true;
    try{const values={};['company','domain','contact','seller','offer','icp'].forEach(k=>values[k]=$(k).value.trim());values.consent_to_api=$('apiConsent').checked;
      const lead=await api('/api/leads',{method:'POST',body:JSON.stringify(values)});selected=lead.id;dirty=false;dialog.close();await refresh();toast('Live lead added. Review the context, then choose Run live research.');
    }catch(err){toast(err.message);}finally{submit.disabled=false;}
  };
}

function renderLiveExtra(x){
  if(x.mode!=='live')return;
  const panel=document.createElement('section');panel.className='live-controls';
  panel.innerHTML=`<div class="section-label"><h3>Live research</h3><span class="badge">${esc(x.domain)}</span></div><p><strong>${esc(x.seller)}</strong> · ${esc(x.offer)}</p><p class="hint">Fit criteria: ${esc(x.icp)}</p><button id="generate" class="primary" ${!workspace.live.configured||x.suppressed||['delivered','researching'].includes(x.state)?'disabled':''}>Run live research & draft</button><span id="runStatus" class="hint"> ${x.state==='researching'?'Research is running. Refresh for its result.':'Uses your OpenAI API account. Existing approval will be revoked.'}</span><p class="hint">The recipient is a simulation placeholder, not a verified email address. No send integration is connected.</p><div id="runUsage"></div>`;
  document.querySelector('.detail-head').after(panel);
  $('generate').onclick=async()=>{
    if(busy)return;if(dirty){toast('Save your draft edits first.');return;}
    if(!confirm('Run paid OpenAI research on this company domain? This revokes any prior approval and can use up to two model responses plus web search.'))return;
    busy=true;$('generate').disabled=true;$('runStatus').textContent=' Research running… this can take up to two minutes. No automatic retries.';
    const timer=setTimeout(async()=>{try{leads=await api('/api/leads');renderQueue();if(selected===x.id)await renderDetail();}catch{}},1200);
    try{await api(`/api/leads/${x.id}/generate`,{method:'POST',body:JSON.stringify({revision:x.revision,reason:''})});toast('Research completed. Review the sources and any evidence hold.');}
    catch(e){toast(e.message);}finally{clearTimeout(timer);busy=false;await refresh();}
  };
  api(`/api/leads/${x.id}/runs`).then(runs=>{
    if(selected!==x.id||!$('runUsage'))return;
    $('runUsage').innerHTML=runs.slice(0,3).map(r=>{const u=r.usage||[];return `<p class="hint">Run ${esc(r.status)} · ${u.length} recorded responses · ${u.reduce((a,b)=>a+(b.input_tokens||0),0)} input / ${u.reduce((a,b)=>a+(b.output_tokens||0),0)} output tokens · ${u.reduce((a,b)=>a+(b.web_search_calls||0),0)} search calls${r.error?' · '+esc(r.error):''}</p>`;}).join('');
  }).catch(e=>toast(e.message));
}
