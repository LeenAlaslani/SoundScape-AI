'use strict';
const $ = id => document.getElementById(id);
const sceneName = {forest:'Forest',coast:'Coast',desert:'Desert',river:'River',waterfall:'Waterfall',mountain:'Mountain',lake:'Lake',unknown:'Uncertain scene'};
// Suggested sound is an artistic default, NOT a weather or sound event detected in the photo.
const sceneSound = {forest:'wind',coast:'sea_waves',desert:'wind',river:'pouring_water',waterfall:'pouring_water',mountain:'wind',lake:'wind'};
const presets = {
  forest:{wind:45},coast:{sea_waves:65,wind:15},
  desert:{wind:55},river:{pouring_water:70,wind:10},waterfall:{pouring_water:85},
  mountain:{wind:40},lake:{wind:20,pouring_water:10}
};
const layerNames={rain:'🌧 Rain',sea_waves:'◉ Waves',wind:'〰 Wind',pouring_water:'≋ Water',thunderstorm:'✧ Thunder'};
let chosenImage = null;
let visionEnabled = false;
let intensity='gentle';
let wavUrl=null;
let imageFlowToken=0;
let controlDebounce=null;
const levels={rain:35,sea_waves:0,wind:20,pouring_water:0,thunderstorm:0};
function updateStatus(message,bad=false){$('statusMessage').textContent=message;$('statusMessage').style.color=bad?'#a7694b':'#839689'}
function applyPreset(scene){const p=presets[scene];if(!p)return;Object.keys(levels).forEach(k=>{levels[k]=p[k]||0});renderLevels()}
function renderLevels(){
  const parent=$('mixerSliders');parent.replaceChildren();
  for(const [key,title] of Object.entries(layerNames)){
    const row=document.createElement('div');row.className='level-row';
    const lab=document.createElement('label');lab.textContent=title;lab.setAttribute('for','level-'+key);
    const input=document.createElement('input');input.type='range';input.min=0;input.max=100;input.step=5;input.id='level-'+key;input.value=levels[key];
    const out=document.createElement('output');out.textContent=levels[key]+'%';
    input.addEventListener('input',()=>{levels[key]=Number(input.value);out.textContent=input.value+'%'});
    row.append(lab,input,out);parent.append(row);
  }
}
async function api(path,opts={}){
  const resp=await fetch('/api/'+path,opts);
  if(!resp.ok){let message='Request failed ('+resp.status+')';try{const err=await resp.json();message=err.detail||message}catch{}throw new Error(message)}
  return resp;
}
function clearPreviousPreview(){
  if(wavUrl){URL.revokeObjectURL(wavUrl);wavUrl=null;}
  $('mixPlayer').hidden=true;$('mixPlayer').removeAttribute('src');$('mixPlayer').load();
  $('downloadMix').hidden=true;$('downloadMix').removeAttribute('href');
  $('promptText').value='';
  $('previewOrigin').textContent='Waiting for an image. The preview mixes existing AI-generated WAVs, not fresh model inference.';
}
function selectImage(file){
  if(!file)return;
  if(!['image/jpeg','image/png','image/webp'].includes(file.type)){updateStatus('Choose a JPEG, PNG or WebP image.',true);return}
  if(file.size>8*1024*1024){updateStatus('Image is larger than 8 MB.',true);return}
  imageFlowToken++;
  chosenImage=file;
  clearPreviousPreview();
  const reader=new FileReader();
  reader.onload=()=>{$('imagePreview').src=reader.result;$('imagePreview').hidden=false;$('dropPlaceholder').hidden=true;$('imageLabel').hidden=false};
  reader.readAsDataURL(file);
  $('analyzeBtn').disabled=!visionEnabled;
  $('analysisResult').textContent=visionEnabled
    ? 'Image received. Automatically analyzing the scene and preparing its soundscape…'
    : 'Image received. The vision service is unavailable; choose the environment manually.';
  if(visionEnabled){void createImageSoundscape();}
  else{updateStatus('Select an environment manually and choose Create audio prompt.');}
}
$('imageInput').addEventListener('change',e=>selectImage(e.target.files[0]));
const drop=$('dropZone');
drop.addEventListener('dragover',e=>{e.preventDefault();drop.classList.add('dragover')});
drop.addEventListener('dragleave',()=>drop.classList.remove('dragover'));
drop.addEventListener('drop',e=>{e.preventDefault();drop.classList.remove('dragover');selectImage(e.dataTransfer.files[0])});
function audioSettings(){
  return {scene:$('sceneSelect').value,sound:$('soundSelect').value,intensity,
          comfort_mode:$('comfortMode').checked,seconds:10};
}
async function composeCurrentPrompt(token=null){
  const response=await api('compose',{method:'POST',headers:{'Content-Type':'application/json'},
                              body:JSON.stringify(audioSettings())});
  const data=await response.json();
  if(token!==null && token!==imageFlowToken)return false;
  $('promptText').value=data.prompt;
  return true;
}
async function mixCurrentLayers(token=null){
  const response=await api('mix',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({seconds:30,levels})});
  const result=await response.blob();
  if(token!==null && token!==imageFlowToken)return false;
  if(wavUrl)URL.revokeObjectURL(wavUrl);
  wavUrl=URL.createObjectURL(result);
  $('mixPlayer').src=wavUrl;$('mixPlayer').hidden=false;
  $('downloadMix').href=wavUrl;$('downloadMix').hidden=false;
  $('previewOrigin').textContent='30-second audio preview: a new mix of previously generated WAV layers. Not a newly generated AudioLDM 2 sample.';
  return true;
}
async function createImageSoundscape(){
  if(!chosenImage || !visionEnabled)return;
  const token=++imageFlowToken;
  $('analyzeBtn').disabled=true;
  $('analyzeBtn').textContent='Analyzing image and building soundscape…';
  updateStatus('Step 1/3 · Understanding your image using the fine-tuned vision model…');
  try{
    const form=new FormData();form.append('image',chosenImage);
    const data=await(await api('analyze',{method:'POST',body:form})).json();
    if(token!==imageFlowToken)return;
    const scene=data.scene||'unknown';
    const el=$('analysisResult');el.replaceChildren();
    const strong=document.createElement('strong');strong.textContent=sceneName[scene]||scene;
    const label=document.createElement('span');label.className='tag';
    label.textContent='Fine-tuned Computer Vision';
    const p=document.createElement('div');p.className='muted';p.style.marginTop='5px';
    const score=typeof data.score==='number'?(' · model confidence: '+Math.round(data.score*100)+'%'):'';
    p.textContent=(data.accepted===false?'Low-confidence scene. ':'Suggested environment'+score+'. ')+
      'Audio is an artistic suggestion, not a sound detected in the photo. You can change it.';
    el.append(strong,label,p);
    // Street/building/out-of-scope images should not silently become forest/rain.
    if(scene==='unknown' || data.accepted===false){
      $('sceneSelect').value='unknown';
      updateStatus('Scene uncertain or outside supported nature scenes. Choose an environment before creating sound.',true);
      return;
    }
    $('sceneSelect').value=scene;
    $('soundSelect').value=sceneSound[scene]||'wind';
    applyPreset(scene);
    updateStatus('Step 2/3 · Composing a scene-appropriate sound prompt…');
    if(!await composeCurrentPrompt(token))return;
    updateStatus('Step 3/3 · Mixing your playable audio preview…');
    if(!await mixCurrentLayers(token))return;
    updateStatus('Ready: image → '+(sceneName[scene]||scene)+' → audio prompt → playable 30-second mix. For a NEW AI recording, connect a GPU and use Generate new sound.');
    $('mixPlayer').scrollIntoView({behavior:'smooth',block:'nearest'});
  }catch(err){
    if(token===imageFlowToken){
      updateStatus('Could not complete image-to-sound flow: '+err.message,true);
      $('analysisResult').textContent='The image or sound service returned an error. Adjust the scene manually and retry.';
    }
  }finally{
    if(token===imageFlowToken){
      $('analyzeBtn').disabled=false;
      $('analyzeBtn').textContent='✳ Rebuild from this image';
    }
  }
}
$('analyzeBtn').addEventListener('click',()=>{void createImageSoundscape()});
function setMainSoundLayer(sound){
  for(const key of Object.keys(levels))levels[key]=0;
  if(Object.hasOwn(levels,sound))levels[sound]=60;
  renderLevels();
}
function schedulePromptRefresh(remix=false){
  clearTimeout(controlDebounce);
  controlDebounce=setTimeout(async()=>{
    try{
      await composeCurrentPrompt();
      if(remix){
        await mixCurrentLayers();
        updateStatus('Sound and scene updated: the audio prompt and saved-WAV preview are ready.');
      } else {
        updateStatus('Audio generation prompt updated. Intensity and Comfort Mode describe NEW audio when GPU generation is connected.');
      }
    }catch(err){updateStatus('Unable to refresh the soundscape: '+err.message,true)}
  },220);
}
$('sceneSelect').addEventListener('change',()=>{
  const scene=$('sceneSelect').value;
  if(sceneSound[scene]){
    $('soundSelect').value=sceneSound[scene];
    applyPreset(scene);
    schedulePromptRefresh(true);
  }else{
    updateStatus('Choose a nature environment for an automatic sound suggestion.',true);
  }
});
$('soundSelect').addEventListener('change',()=>{
  setMainSoundLayer($('soundSelect').value);
  schedulePromptRefresh(true);
});
$('comfortMode').addEventListener('change',()=>schedulePromptRefresh());
document.querySelectorAll('[data-intensity]').forEach(btn=>btn.addEventListener('click',()=>{
  intensity=btn.dataset.intensity;
  document.querySelectorAll('[data-intensity]').forEach(b=>{
    b.classList.toggle('active',b===btn);
    b.setAttribute('aria-pressed',String(b===btn));
  });
  schedulePromptRefresh();
}));
$('composeBtn').addEventListener('click',async()=>{
  try{
    await composeCurrentPrompt();
    updateStatus('Audio prompt ready. Adjust the sliders to customize the saved-audio mix, or use GPU Generate when enabled.');
    $('promptText').scrollIntoView({behavior:'smooth',block:'nearest'});
  }catch(err){updateStatus(err.message,true)}
});
$('copyBtn').addEventListener('click',async()=>{if(!$('promptText').value)return;try{await navigator.clipboard.writeText($('promptText').value);updateStatus('Prompt copied.')}catch{ $('promptText').select();document.execCommand('copy');updateStatus('Prompt selected for copying.')}});
$('mixBtn').addEventListener('click',async()=>{
  $('mixBtn').disabled=true;updateStatus('Preparing a new mix from saved AI-generated audio layers…');
  try{
    await mixCurrentLayers();
    updateStatus('Your preview mix is ready. This mixes saved WAVs; it does not run AudioLDM 2 inference.');
  }catch(err){updateStatus(err.message,true)}finally{$('mixBtn').disabled=false}
});
async function initialize(){renderLevels();try{const data=await(await api('status')).json();visionEnabled=String(data.vision).includes('ready');if(chosenImage && visionEnabled){void createImageSoundscape()} if(!visionEnabled){$('analyzeBtn').disabled=true;$('analyzeBtn').title='Add your trained model export to enable scene analysis.';$('analysisResult').textContent='Photo upload preview and manual scene selection work now. CV predictions become available after adding the trained model export.';} $('connection').innerHTML='<span class="connection-dot"></span> '+(data.available_layers.length?data.available_layers.length+' nature sounds ready':'Vision studio online');if(data.available_layers.length){updateStatus('Ready: '+data.available_layers.length+' original generated audio layers and two fine-tuned comparison sets.')}else{updateStatus('Vision and prompt tools ready. The audio generation model and WAV exports are not connected yet.')}}catch{$('connection').textContent='API connection unavailable';updateStatus('Open via the FastAPI server rather than the HTML file directly.',true)}}
initialize();
// Sound library is initialized after layerCards declaration (avoid temporal dead zone).


// Real WAV outputs reconstructed directly from the executed teammate notebook.
const layerCards = [
  {key:'rain',name:'Gentle rain',icon:'🌧',desc:'Soft, steady rainfall'},
  {key:'sea_waves',name:'Ocean waves',icon:'🌊',desc:'Quiet sandy coastline'},
  {key:'wind',name:'Soft wind',icon:'🍃',desc:'Rustling through leaves'},
  {key:'pouring_water',name:'Flowing stream',icon:'💧',desc:'Water over smooth stones'},
  {key:'thunderstorm',name:'Distant thunder',icon:'🌩',desc:'Low rumbling weather'},
];
function initializeSoundLibrary(){
  const parent=$('layerCards');
  for(const item of layerCards){
    const card=document.createElement('article'); card.className='layer-card';
    const art=document.createElement('div');art.className='layer-art';art.textContent=item.icon;
    const title=document.createElement('h3');title.textContent=item.name;
    const desc=document.createElement('p');desc.textContent=item.desc+' · 60 s loop';
    const player=document.createElement('audio');player.controls=true;player.preload='none';player.src='/api/preview/'+item.key;
    card.append(art,title,desc,player);parent.append(card);
  }
  renderComparisons();
}
function renderComparisons(){
  const group=$('comparisonPlayers');group.replaceChildren();
  const comparison=$('comparisonSelect').value;
  for(const [key,title] of [['original','Original'],['intensity','LoRA · Intensity'],['comfort','LoRA · Comfort']]){
    const row=document.createElement('div');row.className='comparison-row';
    const label=document.createElement('span');label.className='comparison-name';label.textContent=title;
    const audio=document.createElement('audio');audio.controls=true;audio.preload='none';audio.src='/api/compare/'+comparison+'/'+key;
    row.append(label,audio);group.append(row);
  }
}
$('comparisonSelect').addEventListener('change',renderComparisons);
$('useSampleBtn').addEventListener('click',async()=>{
  try{
    const res=await fetch('/static/images/forest_sample.webp');
    if(!res.ok)throw new Error('Example photo missing');
    const file=new File([await res.blob()],'example_forest.webp',{type:'image/webp'});
    selectImage(file);
    updateStatus('Example forest image selected. Building the audio prompt and preview automatically…');
  }catch(err){updateStatus(err.message,true)}
});
let generatedURL=null;
$('generateBtn').addEventListener('click',async()=>{
  const btn=$('generateBtn');btn.disabled=true;
  try{
    // Always build the current scene-dependent prompt first.
    const payload={scene:$('sceneSelect').value,sound:$('soundSelect').value,intensity,comfort_mode:$('comfortMode').checked,seconds:10};
    const compose=await(await api('compose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)})).json();
    $('promptText').value=compose.prompt;
    updateStatus('Generating a fresh recording on the CUDA model...');
    const response=await api('generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({prompt:compose.prompt,adapter:$('adapterSelect').value,seed:Number($('seedInput').value),seconds:10})});
    if(generatedURL)URL.revokeObjectURL(generatedURL);
    generatedURL=URL.createObjectURL(await response.blob());
    $('generatedPlayer').src=generatedURL;$('generatedPlayer').hidden=false;
    $('downloadGenerated').href=generatedURL;$('downloadGenerated').hidden=false;
    updateStatus('New audio generated using '+$('adapterSelect').value+'. Listen or download your result.');
  }catch(err){updateStatus(err.message,true)}finally{btn.disabled=false}
});

// Status is updated when the original initialization resolves; verify GPU separately.
(async function checkGeneration(){
  try{
    const d=await(await api('status')).json();
    const g=d.generation||{};
    $('generateBtn').disabled=!g.available;
    if(g.available){
      $('generationHint').textContent=g.space_configured?'External GPU Space configured. It may queue requests, fail or reach daily limits; click Generate to test actual availability.':(g.adapter_checkpoint_present?'GPU ready; adapters available.':'GPU ready for original-model inference only.');
      $('soundAvailability').textContent=g.space_configured?'5 WAV LAYERS · REMOTE GPU CONFIGURED':'5 WAV LAYERS · LOCAL GPU';
    }else{
      $('generationHint').textContent='GPU generation is not connected in this runtime. Play and mix all five real WAV layers and compare the LoRA samples above. To enable new generation, see RUN_GPU.md.';
      $('soundAvailability').textContent='5 WAV LAYERS READY';
    }
    for(const option of $('adapterSelect').options){option.disabled=!((g.available_models||['original']).includes(option.value))}
  }catch(err){$('generationHint').textContent='Could not check GPU model availability.'}
})();
initializeSoundLibrary();
