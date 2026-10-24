const form=document.getElementById('form');const output=document.getElementById('results');
function el(tag,text,parent,cls){const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;parent.appendChild(n);return n;}
form.addEventListener('submit',async e=>{e.preventDefault();output.replaceChildren();const b=form.querySelector('button');b.disabled=true;el('p','Preparing fictional preview…',output);try{const data=Object.fromEntries(new FormData(form).entries());data.max_results=Number(data.max_results);const r=await fetch('/api/acquisition/preview',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const body=await r.json();if(!r.ok)throw new Error(typeof body.detail==='string'?body.detail:'Check the form values.');output.replaceChildren();el('h2','Fictional prospect shortlist',output);el('p',body.disclaimer,output,'warning');if(!body.candidates.length)el('p','No examples returned.',output);for(const c of body.candidates){const card=el('article',undefined,output,'card');el('h3',c.company,card);el('p',c.fit_reason,card);el('small','Domain: '+c.domain+' · Human review required',card,'muted');el('h4','Illustrative references',card);const ul=el('ul',undefined,card);for(const ev of c.evidence){const li=el('li',undefined,ul);el('span',ev.finding+' — ',li);const link=el('a',ev.url,li);link.href=ev.url;link.target='_blank';link.rel='noopener noreferrer';}el('h4','Unverified',card);el('p',c.unknowns.join(' · ')||'No unknowns supplied',card,'muted');}}catch(err){output.replaceChildren();el('p',err.message,output,'warning');}finally{b.disabled=false;}});


const liveButton=document.getElementById('live-research');
function renderLive(body){output.replaceChildren();el('h2','Live candidate companies — unverified',output);el('p',body.disclaimer,output,'warning');if(!body.candidates.length){el('p','No adequately supported candidates found. This is a valid result.',output);return;}for(const c of body.candidates){const card=el('article',undefined,output,'card');el('h3',c.company,card);el('p',c.fit_reason,card);el('small','Company domain: '+c.domain+' · Human review required',card,'muted');el('h4','Provider-returned citation links — check every claim',card);const ul=el('ul',undefined,card);for(const ev of c.evidence){const li=el('li',undefined,ul);el('span',ev.finding+' — ',li);const link=el('a',ev.url,li);link.href=ev.url;link.target='_blank';link.rel='noopener noreferrer';}el('h4','Still unknown',card);el('p',c.unknowns.join(' · ')||'No unknowns supplied; verify completeness',card,'muted');const save=el('button','Save for human review',card);save.type='button';save.addEventListener('click',async()=>{save.disabled=true;try{await queueApi('/api/acquisition/queue',{company:c.company,domain:c.domain,fit_reason:c.fit_reason,evidence:c.evidence,unknowns:c.unknowns});save.textContent='Added to review queue';await refreshQueue();}catch(err){save.disabled=false;alert(err.message);}});}}
liveButton.addEventListener('click',async()=>{output.replaceChildren();if(!document.getElementById('api-consent').checked){el('p','Check the live research consent box first. The fictional preview remains available.',output,'warning');return;}const data=Object.fromEntries(new FormData(form).entries());data.max_results=Number(data.max_results);data.consent_to_api=true;liveButton.disabled=true;form.querySelector('button[type="submit"]').disabled=true;el('p','Running one bounded web research request. Please do not click again.',output);try{const r=await fetch('/api/acquisition/live',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});const body=await r.json();if(!r.ok)throw new Error(typeof body.detail==='string'?body.detail:'Live research was not accepted.');renderLive(body);}catch(err){output.replaceChildren();el('p',err.message,output,'warning');}finally{liveButton.disabled=false;form.querySelector('button[type="submit"]').disabled=false;}});

async function queueApi(url,data){
  const response=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  const body=await response.json();
  if(!response.ok){const message=typeof body.detail==='string'?body.detail:Array.isArray(body.detail)?body.detail.map(x=>((x.loc||[]).slice(-1)[0]||'Field')+': '+x.msg).join('; '):'Review request failed';throw Error(message);}
  return body;
}
function inputField(parent,labelText,name,type='text'){
  const label=el('label',labelText,parent);
  const input=document.createElement('input');
  input.type=type;input.name=name;input.required=true;label.appendChild(input);return input;
}
async function refreshQueue(){
  const root=document.getElementById('queue-items');root.replaceChildren();
  try{
    const resp=await fetch('/api/acquisition/queue');
    if(!resp.ok)throw Error('Could not load review queue');
    const rows=await resp.json();
    if(!rows.length){el('p','No companies queued for review.',root);return;}
    for(const item of rows){
      const card=el('article',undefined,root,'card');
      el('h3',item.candidate.company,card);
      el('p','Status: '+item.state+' · '+item.candidate.domain,card,'muted');
      el('p',item.candidate.fit_reason,card);
      const links=el('ul',undefined,card);
      for(const ev of item.candidate.evidence){
        const li=el('li',undefined,links);
        el('span',ev.finding+' — ',li);
        const a=el('a',ev.url,li);a.href=ev.url;a.target='_blank';a.rel='noopener noreferrer';
      }
      if(item.state==='pending'){
        const form=el('form',undefined,card);
        const reviewed=el('label',undefined,form);const checkbox=document.createElement('input');
        checkbox.type='checkbox';reviewed.appendChild(checkbox);
        el('span',' I opened the sources and verified the claims',reviewed);
        const note=inputField(form,'Review notes','note');note.minLength=3;
        for(const [label,approve] of [['Approve company for handoff',true],['Reject company',false]]){
          const button=el('button',label,form);button.type='button';
          button.addEventListener('click',async()=>{if(!note.value.trim() || note.value.trim().length<3){alert('Enter review notes of at least 3 characters.');note.focus();return;}if(approve&&!checkbox.checked){alert('Open and verify the sources before approving, then check the evidence confirmation box.');return;}button.disabled=true;try{
            await queueApi('/api/acquisition/queue/'+item.id+'/decision',{approve,evidence_reviewed:checkbox.checked,note:note.value.trim()});
            await refreshQueue();
          }catch(err){button.disabled=false;alert(err.message);}});
        }
      }
      if(item.state==='reviewed'){
        const form=el('form',undefined,card);
        el('p','Complete the missing business details before creating a review-only lead.',form);
        inputField(form,'Real contact or department','contact');
        inputField(form,'Seller name','seller');
        const offer=inputField(form,'Offer (20+ characters)','offer');offer.minLength=20;
        const icp=inputField(form,'Ideal customer profile (10+ characters)','icp');icp.minLength=10;
        const confirm=el('label',undefined,form);
        const checkbox=document.createElement('input');checkbox.type='checkbox';confirm.appendChild(checkbox);
        el('span',' I authorize creation of a research-needed lead (no messaging)',confirm);
        const button=el('button','Transfer to SDR workspace',form);button.type='submit';
        form.addEventListener('submit',async e=>{e.preventDefault();button.disabled=true;try{
          const data=Object.fromEntries(new FormData(form).entries());
          data.confirm_create=checkbox.checked;
          await queueApi('/api/acquisition/queue/'+item.id+'/handoff',data);
          await refreshQueue();
        }catch(err){button.disabled=false;alert(err.message);}});
      }
      if(item.state==='transferred')el('p','Transferred lead: '+item.lead_id+' (research needed; no message sent)',card);
    }
  }catch(err){el('p',err.message,root,'warning');}
}
document.getElementById('refresh-queue').addEventListener('click',refreshQueue);
refreshQueue();
