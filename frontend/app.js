'use strict';
const $ = id => document.getElementById(id);
const names = {rain:'Rain',sea_waves:'Waves',wind:'Wind',pouring_water:'Water',thunderstorm:'Thunder'};
const symbols = {rain:'☂',sea_waves:'≈',wind:'〰',pouring_water:'◌',thunderstorm:'ϟ'};
const sceneSound = {forest:'wind',coast:'sea_waves',mountain:'wind',river:'pouring_water',waterfall:'pouring_water',lake:'wind',desert:'wind'};
const presetLevels = {relax:{rain:35,wind:15},sleep:{rain:25,wind:10},focus:{pouring_water:30,wind:10},nature:{wind:35,pouring_water:20}};
let levels = {...presetLevels.relax};
let intensity = 'gentle', generationAvailable = false, visionAvailable = false;
let objectUrl = null, imageUrl = null, requestVersion = 0;
const player = $('soundPlayer');

function status(message, isError=false) { $('statusMessage').textContent=message; $('statusMessage').classList.toggle('error',isError); }
async function api(path, options={}) {
  const controller=new AbortController();
  const timer=setTimeout(()=>controller.abort(), path==='generate'?180000:30000);
  try {
    const response = await fetch('/api/' + path, {...options,signal:controller.signal});
    if (!response.ok) { let message = 'Request failed ('+response.status+').'; try { message=(await response.json()).detail || message; } catch {} throw new Error(message); }
    return response;
  } catch(error) {
    if(error.name==='AbortError')throw new Error('The request timed out. Please try again.');
    throw error;
  } finally {clearTimeout(timer);}
}
function setActive(group, attribute, value) {
  document.querySelectorAll('['+attribute+']').forEach(button => {
    const active=button.getAttribute(attribute)===value;
    button.classList.toggle('active',active); button.setAttribute('aria-pressed',String(active));
  });
}
function renderLevels() {
  const container=$('mixerSliders'); container.replaceChildren();
  Object.entries(names).forEach(([key,label]) => {
    const row=document.createElement('div'); row.className='level';
    const text=document.createElement('label'); text.htmlFor='level-'+key; text.textContent=symbols[key]+'  '+label;
    const slider=document.createElement('input'); Object.assign(slider,{type:'range',min:'0',max:'100',step:'5',value:String(levels[key]||0),id:'level-'+key});
    const value=document.createElement('output'); value.textContent=(levels[key]||0)+'%';
    slider.addEventListener('input',()=>{levels[key]=Number(slider.value);value.textContent=slider.value+'%';invalidate();});
    row.append(text,slider,value); container.append(row);
  });
}
function invalidate() { requestVersion++; status('Your preferences changed. Create a new soundscape to hear them.'); }
function currentSettings() {
  const entries=Object.entries(names).map(([key])=>[key,levels[key]||0]).sort((a,b)=>b[1]-a[1]);
  return {scene:$('sceneSelect').value,sound:entries[0][0],intensity,comfort_mode:$('comfortMode').checked,weather:$('weatherSelect').value,seconds:10};
}
async function analyzeFile(file) {
  if (!file || !['image/jpeg','image/png','image/webp'].includes(file.type) || file.size>8*1024*1024) { status('Choose a JPEG, PNG or WebP image under 8 MB.',true); return; }
  const version=++requestVersion;
  if(imageUrl) URL.revokeObjectURL(imageUrl); imageUrl=URL.createObjectURL(file); $('imagePreview').src=imageUrl;
  $('imagePreview').alt='Your uploaded scene'; $('imageLabel').textContent='Your chosen place';
  if(!visionAvailable){$('analysisResult').textContent='Scene analysis is unavailable. Choose an environment below.';return;}
  status('Understanding your scene…');
  try {
    const form=new FormData();form.append('image',file);
    const result=await (await api('analyze',{method:'POST',body:form})).json();
    if(version!==requestVersion)return;
    if(result.scene && result.scene!=='unknown' && result.accepted!==false) {
      $('sceneSelect').value=result.scene;
      const sound=sceneSound[result.scene]||'wind'; levels={[sound]:45}; renderLevels();
      $('analysisResult').textContent='Suggested scene: '+result.scene+'. You can change it below.';
      status('Scene ready. Choose the atmosphere you want to hear.');
    } else { $('sceneSelect').value='unknown'; $('analysisResult').textContent='Scene uncertain. Choose the closest environment below.'; status('Choose an environment to continue.'); }
  } catch(error) { if(version===requestVersion){$('analysisResult').textContent='Scene analysis unavailable. Choose an environment below.';status(error.message,true);} }
}
$('imageInput').addEventListener('change', event=>void analyzeFile(event.target.files[0]));
const drop=$('dropZone');
drop.addEventListener('dragover',event=>{event.preventDefault();drop.classList.add('dragover');});
drop.addEventListener('dragleave',()=>drop.classList.remove('dragover'));
drop.addEventListener('drop',event=>{event.preventDefault();drop.classList.remove('dragover');void analyzeFile(event.dataTransfer.files[0]);});
$('useSampleBtn').addEventListener('click',async()=>{try {const r=await fetch('/static/images/forest_sample.webp');if(!r.ok)throw Error('Sample image unavailable');await analyzeFile(new File([await r.blob()],'forest.webp',{type:'image/webp'}));}catch(e){status(e.message,true);}});
document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{levels={...presetLevels[button.dataset.preset]};setActive('presets','data-preset',button.dataset.preset);renderLevels();invalidate();}));
document.querySelectorAll('[data-intensity]').forEach(button=>button.addEventListener('click',()=>{intensity=button.dataset.intensity;setActive('segments','data-intensity',intensity);invalidate();}));
['sceneSelect','weatherSelect','comfortMode'].forEach(id=>$(id).addEventListener('change',invalidate));
$('generateBtn').addEventListener('click',async()=>{
  const version=++requestVersion, button=$('generateBtn');
  if(!Object.values(levels).some(v=>v>0)){status('Choose at least one sound layer.',true);return;}
  button.disabled=true; status(generationAvailable?'Creating your new soundscape…':'Preparing your preview from saved layers…');
  try {
    const settings=currentSettings();
    const composed=await (await api('compose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings)})).json();
    let response, generated=false, fallbackReason='';
    if(generationAvailable) {
      try {
        response=await api('generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:composed.prompt,adapter:$('adapterSelect').value,seconds:10,seed:Math.floor(Math.random()*4294967296)})});
        generated=true;
      } catch(error) { fallbackReason=error.message; }
    }
    if(!generated) {
      const gain=(settings.comfort_mode ? .7 : 1)*({gentle:.75,moderate:.9,strong:1}[settings.intensity]);
      const mix=Object.fromEntries(Object.entries(levels).map(([key,value])=>[key,Math.round(value*gain)]));
      response=await api('mix',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seconds:30,levels:mix})});
    }
    const blob=await response.blob(); if(version!==requestVersion)return;
    if(objectUrl)URL.revokeObjectURL(objectUrl); objectUrl=URL.createObjectURL(blob);
    player.src=objectUrl; player.load(); $('downloadSound').href=objectUrl; $('downloadSound').hidden=false;
    $('player-title').textContent=names[settings.sound]+' in your '+(settings.scene==='unknown'?'nature scene':settings.scene)+'.';
    $('previewOrigin').textContent=generated?'New AI-generated recording · 10 seconds':'Saved-layer preview · 30 seconds · character adjusts volume';
    status(generated?'Your new soundscape is ready.':fallbackReason?'Generation unavailable: '+fallbackReason+' A saved-layer preview is ready.':'Your preview is ready. New AI generation is currently unavailable.',!!fallbackReason);
  } catch(error){if(version===requestVersion)status(error.message,true);} finally {button.disabled=false;}
});
$('comparisonSelect').addEventListener('change',renderComparisons);
function renderComparisons(){const container=$('comparisonPlayers');container.replaceChildren();for(const [id,label] of [['original','Original'],['intensity','Intensity LoRA'],['comfort','Comfort LoRA']]){const row=document.createElement('div');const title=document.createElement('span');title.textContent=label;const audio=document.createElement('audio');audio.controls=true;audio.preload='metadata';audio.src='/api/compare/'+$('comparisonSelect').value+'/'+id;row.append(title,audio);container.append(row);}}
async function initialize(){renderLevels();renderComparisons();try{const data=await (await api('status')).json();visionAvailable=String(data.vision).includes('ready');generationAvailable=!!data.generation?.available;for(const option of $('adapterSelect').options){option.disabled=!(data.generation?.available_models||['original']).includes(option.value);}$('connection').textContent=generationAvailable?'Generation configured':'Preview available';$('generationHint').textContent=generationAvailable?'Requests a new recording; the strongest layer guides the model. Service availability is checked on request.':'Creates a preview from previously generated audio. New generation is offline.';}catch(error){$('connection').textContent='Service unavailable';$('generationHint').textContent='The sound service could not be reached.';status(error.message,true);}}
void initialize();
