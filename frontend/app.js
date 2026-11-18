'use strict';
const $ = id => document.getElementById(id);
const names = {rain:'Rain',sea_waves:'Waves',wind:'Wind',pouring_water:'Water',thunderstorm:'Thunder'};
const symbols = {rain:'☂',sea_waves:'≈',wind:'〰',pouring_water:'◌',thunderstorm:'ϟ'};
const sceneSound = {forest:'wind',coast:'sea_waves',mountain:'wind',river:'pouring_water',waterfall:'pouring_water',lake:'wind',desert:'wind'};
const presetLevels = {relax:{rain:35,wind:15},sleep:{rain:25,wind:10},focus:{pouring_water:30,wind:10},nature:{wind:35,pouring_water:20}};
let levels = {...presetLevels.relax};
let intensity = 'gentle', preset = 'relax', generationAvailable = false, visionAvailable = false;
let objectUrl = null, imageUrl = null, requestVersion = 0;
const player = $('soundPlayer');
let context = null, master = null, gains = {}, loadingMixer = false;
let promptTimer=null, promptVersion=0;

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
    slider.addEventListener('input',()=>{levels[key]=Number(slider.value);value.textContent=slider.value+'%';if(levels[key]===0 && $('weatherSelect').value===(key==='rain'?'rain':key==='wind'?'wind':''))$('weatherSelect').value='none';invalidate();});
    row.append(text,slider,value); container.append(row);
  });
}
function effectiveLevels() {
  const gain=($('comfortMode').checked ? .7 : 1)*({gentle:.75,moderate:.9,strong:1}[intensity]);
  const total=Object.values(levels).reduce((sum,value)=>sum+value,0);
  const headroom=Math.min(1, 100/Math.max(100,total));
  return Object.fromEntries(Object.keys(names).map(key=>[key,Math.round((levels[key]||0)*gain*headroom)]));
}
function description() {
  const active=Object.keys(names).filter(key=>(levels[key]||0)>0).map(key=>names[key]);
  return (active.length?active.join(' + '):'No layers')+' · '+($('sceneSelect').value==='unknown'?'nature':$('sceneSelect').value);
}
function updateGains() {
  if(!context || !master)return;
  const current=effectiveLevels();
  for(const [key,node] of Object.entries(gains))node.gain.setTargetAtTime(current[key]/100,context.currentTime,.04);
  master.gain.setTargetAtTime(Number($('previewVolume').value)/100,context.currentTime,.04);
}
function invalidate() {
  requestVersion++;
  updateGains();
  schedulePrompt();
  if(player.hidden){$('player-title').textContent=description();$('previewOrigin').textContent='Live mix of saved layers · sound character adjusts volume';}
  else status('Preferences updated. Your generated recording is unchanged.');
}
function currentSettings() {
  const entries=Object.entries(names).map(([key])=>[key,levels[key]||0]).sort((a,b)=>b[1]-a[1]);
  return {scene:$('sceneSelect').value,sound:entries[0][0],levels:Object.fromEntries(entries.filter(entry=>entry[1]>0)),preset,intensity,comfort_mode:$('comfortMode').checked,weather:$('weatherSelect').value,seconds:10};
}
function schedulePrompt(){
  clearTimeout(promptTimer);const version=++promptVersion;
  if(!Object.values(levels).some(value=>value>0)){$('promptDescription').textContent='Choose at least one sound.';return;}
  promptTimer=setTimeout(async()=>{
    try{const data=await (await api('compose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(currentSettings())})).json();if(version===promptVersion)$('promptDescription').textContent=data.prompt;}
    catch(error){if(version===promptVersion)$('promptDescription').textContent='Prompt unavailable.';}
  },200);
}
async function ensureMixer() {
  if(context)return;
  const AudioContextClass=window.AudioContext||window.webkitAudioContext;
  if(!AudioContextClass)throw new Error('Live mixing is unavailable in this browser. Download a mix instead.');
  const ctx=new AudioContextClass();
  const activation=ctx.resume();
  try {
    const buffers=await Promise.all(Object.keys(names).map(async key=>{
      const response=await api('preview/'+key);return ctx.decodeAudioData(await response.arrayBuffer());
    }));
    master=ctx.createGain();master.gain.value=0;master.connect(ctx.destination);
    Object.keys(names).forEach((key,index)=>{
      const source=ctx.createBufferSource(), node=ctx.createGain();
      source.buffer=buffers[index];source.loop=true;node.gain.value=0;source.connect(node).connect(master);source.start(ctx.currentTime+.1);
      gains[key]=node;
    });
    context=ctx;updateGains();await activation;
  } catch(error){await ctx.close();master=null;gains={};throw error;}
}
async function togglePreview() {
  if(loadingMixer)return;
  if(!Object.values(levels).some(value=>value>0)){status('Choose at least one sound layer.',true);return;}
  const button=$('previewPlay');loadingMixer=true;button.disabled=true;
  try {
    if(!context){status('Loading saved sound layers…');await ensureMixer();}
    if(context.state==='running' && button.getAttribute('aria-pressed')==='true') {
      await context.suspend();button.setAttribute('aria-pressed','false');button.textContent='▶ Play live mix';if(!generationAvailable)$('generateBtn').textContent='Play live mix ↗';status('Live mix paused.');
    } else {
      player.pause();player.hidden=true;$('downloadSound').hidden=true;
      await context.resume();button.setAttribute('aria-pressed','true');button.textContent='❚❚ Pause live mix';
      if(!generationAvailable)$('generateBtn').textContent='Pause live mix Ⅱ';
      $('player-title').textContent=description();$('previewOrigin').textContent='Live mix of saved layers · sound character adjusts volume';
      status('Live mix playing. Adjust the layers as you listen.');
    }
  }catch(error){status(error.message,true);}finally{loadingMixer=false;button.disabled=false;}
}
$('previewPlay').addEventListener('click',()=>void togglePreview());
$('previewVolume').addEventListener('input',()=>{updateGains();requestVersion++;});
$('downloadMix').addEventListener('click',async()=>{
  const button=$('downloadMix'), version=requestVersion;button.disabled=true;
  try {
    const volume=Number($('previewVolume').value)/100;
    const mix=Object.fromEntries(Object.entries(effectiveLevels()).map(([key,value])=>[key,Math.round(value*volume)]));
    const response=await api('mix',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({seconds:30,levels:mix})});
    const blob=await response.blob();if(version!==requestVersion){status('Settings changed. Download the updated mix.');return;}
    const url=URL.createObjectURL(blob), link=document.createElement('a');link.href=url;link.download='soundscape_mix.wav';link.click();setTimeout(()=>URL.revokeObjectURL(url),60000);status('Mix downloaded.');
  }catch(error){status(error.message,true);}finally{button.disabled=false;}
});
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
      if($('weatherSelect').value!=='none')$('weatherSelect').dispatchEvent(new Event('change'));
      else { updateGains();schedulePrompt();if(player.hidden)$('player-title').textContent=description(); }
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
document.querySelectorAll('[data-preset]').forEach(button=>button.addEventListener('click',()=>{preset=button.dataset.preset;levels={...presetLevels[preset]};setActive('presets','data-preset',preset);if($('weatherSelect').value!=='none')$('weatherSelect').dispatchEvent(new Event('change'));else{renderLevels();invalidate();}}));
document.querySelectorAll('[data-intensity]').forEach(button=>button.addEventListener('click',()=>{intensity=button.dataset.intensity;setActive('segments','data-intensity',intensity);invalidate();}));
$('comfortMode').addEventListener('change',invalidate);
$('sceneSelect').addEventListener('change',()=>{
  const sound=sceneSound[$('sceneSelect').value]||'wind';
  levels={[sound]:45};
  if($('weatherSelect').value!=='none')$('weatherSelect').dispatchEvent(new Event('change'));
  else {renderLevels();invalidate();}
});
$('weatherSelect').addEventListener('change',()=>{
  const weather=$('weatherSelect').value;
  if(weather==='rain'){
    levels.rain=Math.max(levels.rain||0,60);
    if($('sceneSelect').value==='coast')levels.sea_waves=Math.max(levels.sea_waves||0,40);
    if($('sceneSelect').value==='forest')levels.wind=Math.min(levels.wind||0,20);
  }else if(weather==='wind')levels.wind=Math.max(levels.wind||0,60);
  renderLevels();invalidate();
  if(weather==='snow'||weather==='fog')status('Weather is a visual preference; choose the sounds you want to hear.');
});
$('generateBtn').addEventListener('click',async()=>{
  if(!generationAvailable){await togglePreview();return;}
  const version=++requestVersion, button=$('generateBtn');
  if(!Object.values(levels).some(v=>v>0)){status('Choose at least one sound layer.',true);return;}
  button.disabled=true; status(generationAvailable?'Creating your new soundscape…':'Preparing your preview from saved layers…');
  try {
    const settings=currentSettings();
    const composed=await (await api('compose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(settings)})).json();
    const response=await api('generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:composed.prompt,adapter:$('adapterSelect').value,seconds:10,seed:Math.floor(Math.random()*4294967296)})});
    const blob=await response.blob(); if(version!==requestVersion)return;
    if(context && context.state==='running'){await context.suspend();$('previewPlay').setAttribute('aria-pressed','false');$('previewPlay').textContent='▶ Play live mix';}
    if(objectUrl)URL.revokeObjectURL(objectUrl); objectUrl=URL.createObjectURL(blob);
    player.src=objectUrl; player.hidden=false;player.load(); $('downloadSound').href=objectUrl; $('downloadSound').hidden=false;
    $('player-title').textContent='Requested: '+Object.keys(settings.levels).map(key=>names[key]).join(' + ')+' · '+settings.scene;
    $('previewOrigin').textContent='New AI-generated recording · 10 seconds · requested sounds may vary';
    status('Your new soundscape is ready.');
  } catch(error){if(version===requestVersion)status('Generation unavailable: '+error.message+' Use Play live mix for saved layers.',true);} finally {button.disabled=false;}
});
$('comparisonSelect').addEventListener('change',renderComparisons);
function renderComparisons(){const container=$('comparisonPlayers');container.replaceChildren();for(const [id,label] of [['original','Original'],['intensity','Intensity LoRA'],['comfort','Comfort LoRA']]){const row=document.createElement('div');const title=document.createElement('span');title.textContent=label;const audio=document.createElement('audio');audio.controls=true;audio.preload='metadata';audio.src='/api/compare/'+$('comparisonSelect').value+'/'+id;row.append(title,audio);container.append(row);}}
async function initialize(){renderLevels();renderComparisons();schedulePrompt();try{const data=await (await api('status')).json();visionAvailable=String(data.vision).includes('ready');generationAvailable=!!data.generation?.available;for(const option of $('adapterSelect').options){option.disabled=!(data.generation?.available_models||['original']).includes(option.value);}$('connection').textContent=generationAvailable?'Generation configured':'Live mix available';$('generateBtn').textContent=generationAvailable?'Generate soundscape ↗':'Play live mix ↗';$('generationHint').textContent=generationAvailable?'Requests a new recording from the selected model.':'New AI generation is offline. Listen to and download a mix of existing layers.';}catch(error){$('connection').textContent='Service unavailable';$('generationHint').textContent='The sound service could not be reached.';status(error.message,true);}}
void initialize();
