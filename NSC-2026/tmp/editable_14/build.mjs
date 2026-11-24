import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL,fileURLToPath} from 'node:url';
import sharp from 'sharp';
import {Presentation,PresentationFile} from '@oai/artifact-tool';

const ROOT='C:/Users/Raphael Angelo/Code/Competitions/NSC UB';
const DIR=path.dirname(fileURLToPath(import.meta.url));
const SKILL='C:/Users/Raphael Angelo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1011.11113/skills/presentations';
const PY='C:/Users/Raphael Angelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
process.env.RUNTIME_NODE_MODULES='C:/Users/Raphael Angelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
process.env.RUNTIME_NODE='C:/Users/Raphael Angelo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe';
const OUT=path.join(ROOT,'deliverables/presentation/BERKAS_734_14_SLIDE_EDITABLE.pptx');
const {applyPresentationChartFont,finalizePresentation}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')).href);
const P=Presentation.create({slideSize:{width:1600,height:900}});
const C={paper:'#F3EBD9',ink:'#25231F',red:'#9E241F',gray:'#766F63',green:'#57613A',blue:'#355971',tan:'#C8B188'};
const F={title:'Impact',body:'Georgia',sans:'Arial'};
const files=['01-berkas-734-script-baru-v3.png','02-jejak-sensor-script-baru-v3.png','03-periksa-bukti-script-baru-v2.png','04-petunjuk-fisika-script-baru-v2.png','05-kondisi-berubah-script-baru-v2.png','06-tim-investigasi-script-baru-v2.png','07-uji-waktu-script-baru-v2.png','08-gabungan-waktu-script-baru-v2.png','09-pola-residual-script-baru-v2.png','10-rekonsiliasi-statis-script-baru-v1.png','11-bukti-rekonsiliasi-script-baru-v1.png','12-bias-catboost-script-baru-v1.png','13-bukti-ditolak-script-baru-v1.png','14-case-closed-script-baru-v1.png'];
const script=await fs.readFile(path.join(ROOT,'SCRIPT_FINAL_DETECTIVE_NSC_2026.md'),'utf8');
const notes=script.split(/(?=### SLIDE \d+ —)/).filter(t=>t.startsWith('### SLIDE'));
await fs.mkdir(path.join(DIR,'assets'),{recursive:true});
await fs.mkdir(path.join(DIR,'renders'),{recursive:true});
const asset={};
async function crop(n,name,rect){const buf=await sharp(path.join(ROOT,'deliverables/slides',files[n-1])).extract(rect).png().toBuffer();asset[name]=buf;await fs.writeFile(path.join(DIR,'assets',name+'.png'),buf);}
await crop(1,'farmer',{left:320,top:180,width:620,height:672});
await crop(1,'leaf',{left:35,top:590,width:225,height:180});
await crop(1,'sensor',{left:40,top:212,width:233,height:188});
await crop(2,'weather-tools',{left:520,top:690,width:1045,height:141});
await crop(3,'probe',{left:916,top:435,width:118,height:236});
await crop(4,'agro-notebook',{left:36,top:139,width:372,height:465});
await crop(4,'dew-leaf',{left:590,top:680,width:287,height:157});
await crop(5,'warm',{left:19,top:290,width:213,height:222});
await crop(5,'cold',{left:1435,top:292,width:206,height:221});
await crop(6,'tool-huber',{left:31,top:342,width:294,height:224});
await crop(6,'tool-cat',{left:376,top:290,width:280,height:284});
await crop(6,'tool-enet',{left:714,top:263,width:254,height:240});
await crop(6,'tool-ridge',{left:1035,top:270,width:269,height:296});
await crop(6,'tool-l2',{left:1357,top:274,width:276,height:291});
await crop(7,'calendar',{left:1230,top:132,width:358,height:198});
await crop(8,'sky1',{left:343,top:264,width:221,height:81});
await crop(8,'sky2',{left:595,top:261,width:231,height:84});
await crop(8,'sky3',{left:853,top:252,width:226,height:92});
await crop(8,'spring',{left:577,top:683,width:277,height:44});
await crop(10,'balance',{left:642,top:330,width:355,height:295});
await crop(13,'tomato-check',{left:1050,top:590,width:305,height:155});
const bg=await fs.readFile(path.join(ROOT,'tmp/pptx_build/assets/image1.jpeg'));
const paper=await fs.readFile(path.join(ROOT,'tmp/pptx_build/assets/image48.png'));
function shape(s,name,x,y,w,h,fill='none',stroke='none',sw=0,geom='rect') {return s.shapes.add({name,geometry:geom,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw,style:'solid'}});}
function text(s,t,x,y,w,h,size=30,color=C.ink,bold=false,align='left',font=F.body){const a=shape(s,'text-'+t.slice(0,45),x,y,w,h);a.text=t;a.text.style={typeface:font,fontSize:size,color,bold,insets:0,alignment:align,verticalAlignment:'middle',wrap:'square',autoFit:'none'};return a;}
function line(s,x1,y1,x2,y2,color=C.ink,width=3,dashed=false){const minx=Math.min(x1,x2),miny=Math.min(y1,y2);return s.shapes.add({name:'evidence-line',geometry:'custom',position:{left:minx,top:miny,width:Math.max(1,Math.abs(x2-x1)),height:Math.max(1,Math.abs(y2-y1))},fill:'none',line:{fill:color,width,style:dashed?'dash':'solid'},customPaths:[{width:Math.max(1,Math.abs(x2-x1)),height:Math.max(1,Math.abs(y2-y1)),commands:[{moveTo:{x:x1-minx,y:y1-miny}},{lineTo:{x:x2-minx,y:y2-miny}}]}]});}
function dot(s,x,y,r=10,color=C.ink,hollow=false){return shape(s,'data-point',x-r,y-r,r*2,r*2,hollow?C.paper:color,color,2,'ellipse');}
function arrow(s,x,y,w=65,color=C.red){return shape(s,'direction-arrow',x,y,w,25,color,'none',0,'rightArrow');}
function connect(s,a,b,color=C.red,kind='elbow'){
 const pa=a.position,pb=b.position;
 if(pb.top>pa.top+pa.height+60){const x1=pa.left+pa.width/2,y1=pa.top+pa.height,x2=pb.left+pb.width/2,y2=pb.top;return pathLine(s,[[x1,y1],[x1,y1+30],[x2,y2-10],[x2,y2]],color,3);}
 const x1=pa.left+pa.width,y1=pa.top+pa.height/2,x2=pb.left,y2=pb.top+pb.height/2;
 return pathLine(s,kind==='straight'?[[x1,y1],[x2,y2]]:[[x1,y1],[(x1+x2)/2,y1],[(x1+x2)/2,y2],[x2,y2]],color,3);
}
function pathLine(s,pts,color=C.ink,width=3){const minx=Math.min(...pts.map(p=>p[0])),miny=Math.min(...pts.map(p=>p[1])),w=Math.max(...pts.map(p=>p[0]))-minx,h=Math.max(1,Math.max(...pts.map(p=>p[1]))-miny);return s.shapes.add({name:'editable-schematic-path',geometry:'custom',position:{left:minx,top:miny,width:w,height:h},fill:'none',line:{fill:color,width,style:'solid'},customPaths:[{width:w,height:h,commands:pts.map((p,i)=>i?{lineTo:{x:p[0]-minx,y:p[1]-miny}}:{moveTo:{x:p[0]-minx,y:p[1]-miny}})}]});}
async function img(s,name,x,y,w,h){const buf=asset[name];return s.images.add({blob:buf,contentType:'image/png',alt:'Ilustrasi detektif: '+name,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
async function page(s,x,y,w,h){shape(s,'paper-underlay',x,y,w,h,'#F5F2E4');s.images.add({blob:paper,contentType:'image/png',alt:'Lembar bukti krem',fit:'cover',position:{left:x,top:y,width:w,height:h}});}
async function base(n,title,source='Laporan final Heisenberg'){const s=P.slides.add();s.images.add({blob:bg,contentType:'image/jpeg',alt:'Latar detektif',fit:'cover',position:{left:0,top:0,width:1600,height:900}});shape(s,'case-tag',45,23,230,43,C.paper);text(s,'BERKAS 734',60,25,200,39,30,C.ink,true);text(s,n<=2?'THE MYSTERY':n<=5?'THE CLUES':n<=8?'THE INVESTIGATION':n<=13?'THE BREAKTHROUGH':'CASE CLOSED',1210,25,345,36,23,C.paper,false,'right');text(s,title,45,76,1510,62,50,C.paper,false,'left',F.title);text(s,'Heisenberg · NSC 2026',45,862,390,27,22,C.paper);text(s,source,440,862,1020,25,17,C.paper,false,'right',F.sans);text(s,String(n).padStart(2,'0'),1490,862,60,27,24,C.paper,false,'right');s.speakerNotes.text=(notes[n-1]||'')+'\n\nSumber isi: SCRIPT_FINAL_DETECTIVE_NSC_2026.md; docs/final/paper-submission-verified-extracted.md. Ilustrasi merupakan aset ImageGen yang dibuat untuk slide ini. Kurva berlabel ilustrasi tidak mewakili pengukuran atau aktual test. Angka publik dan validasi adalah evaluasi berbeda.';return s;}
function bars(s,title,cats,vals,x,y,w,h,{digits=2,max,colors}={}){
 const cc=[...cats].reverse(),vv=[...vals].reverse(),colorsRev=colors?[...colors].reverse():[],numSize=digits===3?27:35;
 const ch=s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},title,titlePlacement:'aboveChart',titleTextStyle:{fontSize:29,fill:C.ink,bold:true},categories:cc,series:[{name:title,values:vv,fill:C.red,valuesFormatCode:'0.'+'0'.repeat(digits),points:vv.map((_,i)=>({idx:i,fill:colorsRev[i]||C.red})),dataLabelOverrides:vv.map((v,i)=>({idx:i,text:v.toFixed(digits).replace('.',','),showValue:false,position:'outEnd',textStyle:{fontSize:numSize,fill:C.ink,bold:true,typeface:F.sans}}))}],hasLegend:false,barOptions:{direction:'bar',grouping:'clustered',gapWidth:90,varyColors:true},xAxis:{visible:true,textStyle:{fill:C.ink,fontSize:24},majorGridlines:null,line:{fill:'none',width:0}},yAxis:{visible:false,min:0,max,majorGridlines:null,line:{fill:'none',width:0}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.'+'0'.repeat(digits),textStyle:{fill:C.ink,fontSize:numSize,bold:true}},chartFill:'none',chartLine:{fill:'none',width:0},plotAreaFill:'none',plotAreaLine:{fill:'none',width:0}});
 applyPresentationChartFont(ch,{fontFamily:F.sans});
 return ch;
}
function legend(s,label,x,y,col=C.ink,hollow=false){dot(s,x,y+13,7,col,hollow);text(s,label,x+18,y,230,27,21,col);}
function availability(s,x,y,w,h,{labels=['Kelembapan','Suhu','Tekanan udara','Tanah & irigasi','Sensor lain'],small=false}={}){const labelW=small?140:245,bound=x+labelW+(w-labelW)*.65,ystep=h/labels.length;labels.forEach((t,i)=>{const yy=y+i*ystep;text(s,t,x,yy-3,labelW-10,34,small?18:26,C.ink,true);const start=x+labelW;for(let xx=start;xx<w+x-25;xx+=small?16:24){if(i===0&&xx>=bound)continue;shape(s,'availability-record',xx,yy+9,small?9:14,small?9:14,xx>=bound?C.green:C.ink);}if(i===0){shape(s,'unknown-target-window',bound,yy,w+x-15-bound,36,'none',C.red,2);text(s,small?'? ? ?':'Target tidak diberikan',bound+10,yy, w+x-bound-25,34,small?23:21,C.red,true);}});line(s,bound,y-22,bound,y+h-15,C.gray,2,true);return bound;}
function processRibbon(s,items,y=772){const w=1430/items.length;items.forEach((t,i)=>{text(s,t,65+i*w,y,w-38,45,27,C.ink,true,'center');if(i<items.length-1)arrow(s,65+(i+1)*w-36,y+12,35);});}

// 01: story illustration and native missing-data exhibit.
{
const s=await base(1,'THE MISSING HUMIDITY CASE','Kebun Pak Anton merupakan ilustrasi; data NSC 2026');await page(s,40,154,785,680);await page(s,850,154,710,680);
await img(s,'farmer',65,185,660,600);await img(s,'leaf',67,574,232,176);await img(s,'sensor',85,185,185,143);
shape(s,'editable-name-label',478,432,192,49,C.paper);text(s,'Pak Anton',484,437,180,34,27,C.ink,true);shape(s,'sensor-label-paper',77,330,300,45,C.paper);text(s,'Sensor lingkungan',84,332,285,40,24,C.ink,true);shape(s,'leaf-label-paper',67,750,243,43,C.paper);text(s,'Tanaman layu',74,752,230,39,27,C.ink,true);shape(s,'logbook-label-paper',312,696,185,43,C.paper);text(s,'Catatan sensor',319,698,172,38,22,C.ink,true);
text(s,'BUKTI AWAL',895,188,565,51,42,C.red,false,'center',F.title);text(s,'734',900,262,330,143,132,C.red,true);text(s,'nilai kelembapan\ntidak diketahui',900,410,355,86,30,C.ink,true);text(s,'>15 HARI',1245,283,262,89,59,C.red,false,'center',F.title);text(s,'periode tanpa target',1240,379,270,44,25,C.ink,false,'center');text(s,'Skema ketersediaan data',895,550,605,42,26,C.ink,true);availability(s,895,611,590,122,{labels:['Kelembapan','Sensor lain'],small:true});text(s,'Waktu',1355,751,128,32,22);}

// 02: availability diagram, rebuilt from new script.
{
const s=await base(2,'JEJAK SENSOR MASIH TERSEDIA','Skema ketersediaan data · train / test');await page(s,40,154,1520,590);
text(s,'2.933',454,184,300,82,74,C.red,true,'center');text(s,'catatan latih',454,268,300,40,29,C.ink,true,'center');text(s,'TRAIN',454,313,300,35,26,C.ink,true,'center');text(s,'734',1150,184,260,82,74,C.red,true,'center');text(s,'baris uji',1150,268,260,40,29,C.ink,true,'center');text(s,'TEST',1150,313,260,35,26,C.ink,true,'center');availability(s,85,384,1300,300);
text(s,'24',1401,455,110,74,65,C.green,true,'center');text(s,'kanal\nsensor lain',1390,533,140,82,26,C.ink,true,'center');line(s,330,704,1380,704,C.ink,3);text(s,'Waktu',1400,685,117,35,26);await img(s,'weather-tools',674,757,833,74);text(s,'Cukup untuk merekonstruksi 734 nilai?',63,778,602,48,30,C.paper,true);}

// 03: four-neighbour mechanism and native residual-ratio chart.
{
const s=await base(3,'SEBAGIAN BUKTI PERLU DIPERIKSA','Sumber rasio: laporan Heisenberg, Gambar 2 dan Tabel I');await page(s,40,154,990,590);await page(s,1050,154,510,590);await page(s,40,757,1520,78);
text(s,'Periksa satu titik',80,184,690,60,41,C.ink,true);line(s,135,308,135,630);line(s,135,630,908,630);text(s,'Suhu',77,417,63,54,24);text(s,'Waktu',640,642,224,34,24);
const pts=[[220,460],[370,500],[520,515],[680,500],[850,460]];pathLine(s,pts,C.gray,3);pts.forEach((p,i)=>dot(s,...p,10,C.ink,i===2));dot(s,520,321,14,C.red);line(s,520,344,520,498,C.red,3,true);text(s,'Nilai asli',553,285,262,42,30,C.red,true);text(s,'Residual',555,398,244,44,30,C.red);text(s,'Perkiraan',547,518,235,40,28);text(s,'4 titik tetangga',305,575,440,39,28,C.ink,true,'center');text(s,'Ilustrasi pemeriksaan, bukan deret pengukuran',85,694,890,31,20,C.gray);bars(s,'Rasio residual',['Suhu','Tekanan','Kelembapan'],[5.75,6.86,1.2],1070,183,465,355,{max:9.8,colors:[C.red,C.red,C.ink]});text(s,'SD residual / skala robust MAD',1100,564,410,62,25,C.ink,false,'center');text(s,'Lonjakan lebih dominan\npada sensor masukan',1090,638,422,71,27,C.red,true,'center');processRibbon(s,['LOO Quadratic Interpolation','MAD','Hampel selektif'],774);}

// 04: inverse reconstruction and editable physics equation.
{
const s=await base(4,'CATATAN HARIAN MENYIMPAN PETUNJUK','Sumber angka: laporan Heisenberg, Bagian II-D');await page(s,40,154,1520,503);await page(s,40,674,1520,162);
await img(s,'agro-notebook',66,206,299,373);text(s,'7 indeks agronomi harian',67,580,322,55,27,C.ink,true,'center');
text(s,'JALUR 1',423,190,410,42,32,C.red,true);text(s,'Rerata dan maksimum',423,234,524,42,29,C.ink,true);const a=text(s,'Tmin = 2 × Tmean − Tmax',423,294,598,64,38,C.ink,false,'left',F.sans);
text(s,'JALUR 2',423,404,410,42,32,C.red,true);text(s,'Ontario Crop Heat Unit',423,448,524,42,29,C.ink,true);const b=text(s,'Tmin = (2 × CHU − Ymax) / 1,8 + 4,4',423,502,605,72,31,C.ink,false,'left',F.sans);
const target=text(s,'Suhu\nminimum',1010,323,171,95,29,C.ink,true,'center');connect(s,a,target,C.ink);connect(s,b,target,C.ink);text(s,'0,047 °C',1200,197,330,83,70,C.red,true,'center');text(s,'SD selisih\ndua rekonstruksi',1210,287,301,83,29,C.ink,true,'center');
const pp=[[1220,463],[1268,443],[1317,482],[1368,486],[1420,459],[1470,477],[1510,449]];pathLine(s,pp,C.ink,3);pathLine(s,pp.map(([x,y],i)=>[x,y+(i%2?5:-5)]),C.red,2);text(s,'Kurva ilustratif',1217,545,303,33,22,C.gray,false,'center');
text(s,'Tmin sebagai\nproksi titik embun',74,706,345,79,32,C.ink,true);await img(s,'dew-leaf',462,698,232,117);arrow(s,714,743,67);text(s,'Tekanan uap',817,710,255,48,31,C.ink,true);text(s,'RH = 100 × e / es(T)',1087,701,420,65,38,C.ink,false,'left',F.sans);text(s,'e: aktual   es(T): jenuh',1087,775,420,32,25);}

// 05: native mean chart and schematic irrigation records.
{
const s=await base(5,'KONDISI PADA PERIODE UJI BERUBAH','Sumber angka: laporan Heisenberg, Bagian II-E');await page(s,40,154,1520,360);await page(s,40,531,1520,188);await page(s,40,736,1520,100);
await img(s,'warm',65,220,194,226);await img(s,'cold',1350,220,183,226);text(s,'TRAIN',311,179,400,39,29,C.ink,true,'center');text(s,'TEST',869,179,400,39,29,C.ink,true,'center');text(s,'27,51 °C',306,227,417,92,78,C.ink,true,'center');text(s,'24,64 °C',864,227,417,92,78,C.ink,true,'center');
const x0=345,x1=1240,y=397;line(s,x0,y,x1,y);[20,25,30].forEach(t=>{const x=x0+(t-20)/10*(x1-x0);line(s,x,y-8,x,y+8);text(s,String(t),x-26,y+14,52,30,24,C.ink,false,'center');});dot(s,x0+.751*(x1-x0),y,12,C.ink);dot(s,x0+.464*(x1-x0),y,12,C.red);text(s,'Suhu rata-rata (°C)',548,453,510,40,29,C.red,true,'center');
text(s,'Irigasi: bervariasi',92,552,629,38,29,C.ink,true);text(s,'Irigasi: konstan',872,552,618,38,29,C.ink,true);const p=Array.from({length:22},(_,i)=>[95+i*28,650-([2,3,7,4,6,3,8,5,4,7,3][i%11])*5]);pathLine(s,p,C.ink,3);line(s,873,625,1479,625,C.red,3);text(s,'Skema perubahan catatan irigasi',492,674,622,30,22,C.gray,false,'center');
text(s,'Distribution Shift',72,755,375,60,35,C.red,true);text(s,'Fitur tanah',505,754,294,49,29,C.ink,true);line(s,505,781,768,781,C.red,4);text(s,'Fitur irigasi',842,754,296,49,29,C.ink,true);line(s,842,781,1120,781,C.red,4);text(s,'Dikeluarkan dari\nkonfigurasi akhir',1205,751,300,68,27,C.ink,true);}

// 06: native team dossiers and attached connectors.
{
const s=await base(6,'LIMA MODEL MEMBACA JEJAK YANG BERBEDA','Peran mengikuti pipeline final Heisenberg · diagram ilustratif');const names=['LightGBM\nHuber','CatBoost\nHuber','ElasticNet','Ridge','LightGBM L2'];const roles=['Batasi pengaruh\ngalat ekstrem','Pola dan galat\nberbeda','Hubungan linear\nteratur','Hubungan fisika\nkelembapan','Peka terhadap\ngalat besar'];const tools=['tool-huber','tool-cat','tool-enet','tool-ridge','tool-l2'];let boxes=[];
for(let i=0;i<5;i++){let x=40+i*307;await page(s,x,154,292,515);text(s,names[i],x+15,183,260,87,i===4?34:38,C.ink,true,'center');if(i===0)text(s,'MODEL UTAMA',x+15,278,260,32,22,C.red,true,'center');if(i===3)text(s,'berbasis tekanan uap',x+15,267,260,35,23,C.ink,false,'center');await img(s,tools[i],x+20,318,250,230);if(i===2)text(s,'L1 + L2',x+15,543,260,33,27,C.red,true,'center');boxes.push(text(s,roles[i],x+17,591,258,65,26,C.ink,true,'center'));}
await page(s,456,725,725,112);const out=text(s,'Prediksi yang saling melengkapi',477,752,684,43,32,C.ink,true,'center');boxes.forEach(b=>connect(s,b,out,C.red));text(s,'Model Diversity',65,750,334,47,32,C.paper,true);text(s,'Skema penggabungan',551,801,533,26,20,C.gray,false,'center');}

// 07: nine expanding-origin folds, RMSE and OOF.
{
const s=await base(7,'MODEL DIUJI PADA WAKTU BERIKUTNYA','Sumber protokol: laporan Heisenberg, Bagian II-F');await page(s,40,154,1050,579);await page(s,1110,154,450,579);await page(s,40,751,1520,85);text(s,'Rolling-Origin Cross-Validation',72,183,956,56,39,C.ink,true);text(s,'Training',198,255,400,40,27,C.ink,true);text(s,'Validation: 15 hari',760,255,300,40,27,C.red,true);
for(let i=0;i<9;i++){let y=318+i*37,train=490+i*23;text(s,'Fold '+(i+1),77,y-4,107,31,23,C.ink,true);shape(s,'training-fold-'+(i+1),195,y,train,24,C.ink);shape(s,'validation-fold-'+(i+1),195+train,y,155,24,C.red);}
line(s,195,665,1010,665);text(s,'Waktu',858,672,144,32,24);text(s,'Jendela validasi tumpang tindih',236,692,780,28,23,C.red,true,'center');
text(s,'15',1150,185,365,97,91,C.red,true,'center');text(s,'hari per jendela',1149,287,370,44,28,C.ink,true,'center');text(s,'9 titik awal',1149,363,370,61,51,C.red,true,'center');text(s,'RMSE',1150,454,360,49,37,C.ink,true);text(s,'√mean((prediksi − aktual)²)',1150,514,360,65,28,C.ink,false,'left',F.sans);text(s,'Semakin kecil,\nsemakin baik',1150,614,360,73,29,C.ink,true);
text(s,'OOF',70,773,150,43,36,C.red,true);arrow(s,230,786,60);text(s,'Mempelajari penggabungan',312,773,567,43,29,C.ink,true);text(s,'9 jendela bukan 9 eksperimen independen',918,765,578,62,27,C.red,true);}

// 08: separate NNLS weights per three time bands and native control chart.
{
const s=await base(8,'WAKTU MEMBANTU PENGGABUNGAN MODEL','Sumber angka: laporan Heisenberg, bobot per pita waktu-hari');await page(s,40,154,1012,682);await page(s,1073,154,487,682);text(s,'Time-Banded Ensemble',72,179,929,55,40,C.ink,true);const labels=['LightGBM Huber','CatBoost Huber','ElasticNet','Ridge-e','LightGBM L2'];const colors=[C.red,C.blue,C.green,'#76538A','#B27025'];const models=[];labels.forEach((t,i)=>models.push(text(s,t,73,307+i*72,255,46,24,C.ink,true)));
models.forEach((m,j)=>line(s,328,330+j*72,352,330+j*72,colors[j],3));line(s,352,330,352,618,C.ink,3);line(s,352,426,965,426,C.ink,3);for(let i=0;i<3;i++){const x=370+i*216;await img(s,'sky'+(i+1),x,258,183,95);text(s,'Pita '+(i+1),x,358,183,42,28,C.ink,true,'center');const mixer=shape(s,'NNLS-time-band-'+(i+1),x+38,458,110,69,C.paper,C.red,2,'ellipse');text(s,'NNLS',x+37,472,111,40,29,C.ink,true,'center');line(s,x+93,426,x+93,458,C.ink,3);text(s,'bobot ≥ 0',x,556,183,41,27,C.ink,true,'center');}
await img(s,'spring',490,636,311,53);text(s,'Shrinkage',492,690,310,45,35,C.ink,true,'center');text(s,'Menahan bobot terlalu mengikuti validasi',194,752,829,40,27,C.ink,false,'center');text(s,'Skema mekanisme',76,805,550,25,20,C.gray);
bars(s,'Penurunan RMSE',['Berdasarkan\nwaktu','Pembagian\nacak'],[.080,.007],1087,208,441,375,{digits:3,max:.14,colors:[C.red,C.ink]});text(s,'Kompleksitas setara',1105,618,414,49,28,C.ink,true,'center');text(s,'Audit validasi bersarang',1105,680,414,67,29,C.red,true,'center');text(s,'Equal-Parameter\nRandom Control',1115,763,392,57,25,C.ink,false,'center');}

// 09: native residual pattern and increment horizons.
{
const s=await base(9,'KESALAHAN MASIH MEMILIKI POLA WAKTU','Sumber angka: laporan Heisenberg, analisis galat model level');await page(s,40,154,1030,503);await page(s,1090,154,470,503);await page(s,40,675,1520,161);text(s,'Residual bertetangga cenderung searah',77,177,940,56,34,C.ink,true);text(s,'Residual = prediksi − aktual',205,241,694,42,28);line(s,130,399,1005,399,C.gray,2,true);text(s,'0',83,379,35,38,26);const xs=[157,225,293,361,429,497,565,633,701,769,837,905,973],ys=[327,337,368,397,436,452,464,452,428,400,365,348,328];pathLine(s,xs.map((x,i)=>[x,ys[i]]));xs.forEach((x,i)=>dot(s,x,ys[i],9,i>=4&&i<=7?C.red:C.gray));text(s,'Meleset terlalu rendah',397,495,516,45,29,C.red,true);line(s,130,565,1008,565);text(s,'Waktu',720,575,280,33,25);text(s,'Ilustrasi pola residual, bukan deret pengukuran',99,615,936,28,21,C.gray,false,'center');
text(s,'Autokorelasi residual',1123,184,393,58,31,C.ink,true,'center');text(s,'≈0,93',1122,290,392,112,100,C.red,true,'center');text(s,'lag-1',1124,416,388,54,39,C.ink,true,'center');text(s,'Galat model level',1122,487,392,47,29,C.ink,true,'center');text(s,'Kesalahan menyimpan\nstruktur waktu',1123,568,391,68,27,C.ink,true,'center');text(s,'DARI NILAI KE PERUBAHAN',72,692,654,43,32,C.red,true);text(s,'Level: nilai pada satu waktu',72,751,612,43,28,C.ink,true);
const nodes=[];for(let i=0;i<5;i++)nodes.push(dot(s,848+i*155,767,10,C.blue));line(s,848,744,1003,744,C.red,3);text(s,'30 menit',860,701,185,33,25,C.red,true);line(s,848,809,1468,809,C.red,3);text(s,'2 jam',1107,773,209,33,25,C.red,true,'center');text(s,'Increment',1310,691,210,43,31,C.ink,true);}

// 10: editable dual-predictor reconciliation mechanism, static fallback.
{
const s=await base(10,'NILAI DAN PERUBAHAN DISELARASKAN BERSAMA','Mekanisme: laporan Heisenberg, Bagian V-D');await page(s,40,154,1520,682);text(s,'Data sensor',73,177,248,41,28,C.ink,true);
const level=text(s,'Level Prediction\nPosisi tiap titik',105,239,349,100,32,C.ink,true);const inc=text(s,'Increment Prediction\nPerubahan antartitik',105,493,349,100,28,C.ink,true);const lv=[[120,402],[186,368],[252,394],[318,418],[384,383]];pathLine(s,lv,C.ink);lv.forEach(p=>dot(s,...p,9));for(let i=0;i<5;i++)dot(s,122+i*67,646,9);line(s,122,621,189,621,C.red);text(s,'30 menit',120,590,202,31,22,C.red);line(s,122,691,390,691,C.red);text(s,'2 jam',204,696,122,30,22,C.red);text(s,'Belum tentu cocok',109,444,362,38,25,C.red,true);
text(s,'Temporal\nReconciliation',525,187,419,106,37,C.ink,true,'center');text(s,'Weighted Least Squares',525,308,419,53,29,C.ink,true,'center');await img(s,'balance',536,385,380,319);const opt=text(s,'Kompromi berbobot',533,721,386,40,29,C.ink,true,'center');pathLine(s,[[461,283],[496,283],[496,432],[534,432]],C.ink,3);pathLine(s,[[461,545],[496,545],[496,593],[534,593]],C.ink,3);arrow(s,929,451,49,C.ink);
text(s,'Satu lintasan rekonsiliasi',987,187,517,61,35,C.ink,true);const sx=[1018,1131,1244,1357,1470],fy=[452,378,428,464,390],py=[414,334,470,505,343];pathLine(s,sx.map((x,i)=>[x,fy[i]]),C.red,4);sx.forEach((x,i)=>{line(s,x,py[i],x,fy[i],C.gray,2,true);dot(s,x,py[i],8,C.gray,true);dot(s,x,fy[i],10,C.red);});line(s,994,572,1507,572);text(s,'Waktu',1196,581,230,30,24);legend(s,'Level awal',1007,284,C.gray,true);legend(s,'Rekonsiliasi',1266,284,C.red);line(s,1018,324,1131,324,C.red,2);text(s,'30 menit',1019,337,151,29,22,C.red);line(s,1018,268,1470,268,C.red,2);text(s,'2 jam',1190,240,143,26,22,C.red,false,'center');
text(s,'734',1004,663,209,110,96,C.red,true);text(s,'titik saling\nterhubung',1240,671,275,81,32,C.ink,true);text(s,'Ilustrasi mekanisme, bukan prediksi aktual',975,782,538,30,20,C.gray,false,'center');}

// 11: native OOF comparison and separate public result.
{
const s=await base(11,'REKONSILIASI MEMPERBAIKI HASIL PENGUJIAN','Sumber: laporan Heisenberg, rekonsiliasi dan Tabel A.IV');await page(s,40,154,686,567);await page(s,747,154,813,567);await page(s,40,740,1520,95);text(s,'BUKTI 1',73,181,246,38,30,C.red,true);text(s,'Validasi OOF · 30 menit',75,232,605,47,30,C.ink,true);bars(s,'RMSE perubahan',['Selisih\nprediksi level','Model\nincrement'],[1.91,1.81],74,314,607,246,{max:2.4,colors:[C.ink,C.red]});text(s,'30 menit diberi bobot\nrelatif lebih besar',109,611,524,73,29,C.ink,true,'center');text(s,'BUKTI 2',780,181,246,38,30,C.red,true);text(s,'RMSE PUBLIK',782,232,685,47,37,C.ink,true);text(s,'Sebelum rekonsiliasi',782,319,690,42,29);text(s,'3,02586',782,369,680,91,79,C.ink,true);text(s,'Sesudah rekonsiliasi',1024,464,482,42,29);text(s,'2,86595',1024,514,482,88,79,C.red,true);text(s,'≈0,160 penurunan RMSE',789,637,714,49,36,C.red,true);text(s,'Arah perbaikan konsisten pada 3 blok audit maju',69,764,1064,47,31,C.ink,true);text(s,'RMSE lebih kecil\nberarti lebih baik',1190,756,324,69,27,C.red,true);}

// 12: native bias comparison and OOF-based partial correction.
{
const s=await base(12,'BIAS MUNCUL PADA AUDIT MAJU','Sumber: laporan Heisenberg, Bagian V-C');await page(s,40,154,827,548);await page(s,887,154,673,548);await page(s,40,721,1520,114);text(s,'CatBoost: bias residual',78,181,741,55,37,C.ink,true);text(s,'Residual = prediksi − aktual',78,250,725,42,28);line(s,133,363,780,363);text(s,'0',86,344,34,39,28);dot(s,299,364,9,C.ink,true);shape(s,'audit-forward-bias',589,363,115,217,C.red);text(s,'−0,006 %RH',190,401,323,46,35,C.ink,true);text(s,'−2,89 %RH',527,589,279,48,35,C.red,true);text(s,'In-sample',205,642,253,39,28,C.ink,true);text(s,'Audit maju',536,642,265,39,28,C.ink,true);
text(s,'Partial Bias Correction',920,181,595,56,37,C.ink,true);const oof=text(s,'Estimasi dari prediksi OOF',919,282,598,47,29,C.ink,true);text(s,'50%',1061,371,330,85,78,C.red,true,'center');text(s,'estimasi koreksi',1061,469,330,42,29,C.ink,true,'center');const cb=text(s,'Koreksi parsial CatBoost',920,549,595,43,30,C.ink,true,'center');shape(s,'OOF-to-half',1210,338,24,25,C.ink,'none',0,'downArrow');shape(s,'half-to-CatBoost',1210,515,24,25,C.ink,'none',0,'downArrow');text(s,'Angka audit bukan besar koreksi.',920,630,599,43,27,C.red,true,'center');text(s,'NEGATIVE CONTROL',77,747,390,58,34,C.red,false,'left',F.title);text(s,'Arah salah: tidak membaik',516,746,478,63,29,C.ink,true);text(s,'Model hampir tidak bias:\ntidak membaik',1074,737,431,77,27,C.ink,true);}

// 13: rejected extra package and bounded use.
{
const s=await base(13,'BUKTI TAMBAHAN TIDAK SELALU MEMBANTU','Sumber skor: laporan Heisenberg, Tabel A.IV');await page(s,40,154,930,566);await page(s,990,154,570,566);await page(s,40,738,1520,98);text(s,'Paket tambahan increment',78,179,820,60,38,C.ink,true);text(s,'Pipeline rekonsiliasi tetap diterapkan',78,265,816,54,30,C.ink,true);text(s,'RMSE PUBLIK',79,340,808,49,34,C.ink,true);text(s,'2,86595',83,416,372,86,70,C.ink,true);arrow(s,476,450,77);text(s,'2,93028',575,416,348,86,70,C.red,true);text(s,'Sebelum tambahan',83,518,387,42,27);text(s,'Sesudah tambahan',575,518,348,42,27);text(s,'RMSE meningkat',80,590,444,47,32,C.red,true);const stamp=text(s,'REJECTED',566,591,357,67,55,C.red,false,'center',F.title);shape(s,'rejected-stamp-border',555,582,380,83,'none',C.red,3);text(s,'BATAS PENERAPAN',1028,183,483,56,36,C.ink,true);text(s,'Sensor pendamping tersedia\npada periode prediksi kompetisi',1030,280,473,96,29,C.ink,true);text(s,'Real-time perlu evaluasi tersendiri\nInformasi pada saat keputusan',1030,414,473,99,28,C.ink,true);text(s,'Dampak panen dan\nkesehatan tanaman belum diuji',1030,558,473,100,29,C.ink,true);text(s,'Kesimpulan dibatasi pada rekonstruksi kelembapan',72,764,1440,48,35,C.ink,true,'center');}

// 14: public result distinct from same-protocol validation.
{
const s=await base(14,'CASE CLOSED: BERKAS 734','Sumber angka: laporan dan hasil evaluasi final Heisenberg');await page(s,40,154,811,527);await page(s,870,154,690,527);await page(s,40,700,1520,136);text(s,'RMSE PUBLIK AKHIR',77,188,733,55,41,C.ink,true,'center');text(s,'2,82744',68,301,744,143,127,C.red,true,'center');text(s,'734 nilai kelembapan direkonstruksi',77,500,733,69,34,C.ink,true,'center');text(s,'Rekonstruksi yang dapat diuji\ndan dipertanggungjawabkan',102,600,680,59,27,C.ink,false,'center');
bars(s,'RMSE validasi rolling-origin',['Baseline\nLightGBM','Pipeline\nlengkap'],[5.71,4.81],893,174,624,266,{max:7,colors:[C.ink,C.red]});text(s,'≈15,8%',913,467,299,78,66,C.red,true,'center');text(s,'perbaikan validasi',906,548,312,37,26,C.ink,true,'center');text(s,'9/9 fold',1240,467,280,78,57,C.red,true,'center');text(s,'hasil lebih baik',1240,548,280,37,26,C.ink,true,'center');for(let i=0;i<9;i++)text(s,'✓',930+i*65,596,47,38,35,C.red,true,'center',F.sans);text(s,'Jendela validasi tumpang tindih',909,640,604,30,22,C.gray,false,'center');processRibbon(s,['Sensor','Fisika','Shift','Ensemble','Lintasan'],729);text(s,'Rekonstruksi yang dapat diuji dan dipertanggungjawabkan.',123,786,1350,32,26,C.ink,true,'center');}

const draft=path.join(DIR,'candidate.pptx');
await (await PresentationFile.exportPptx(P)).save(draft);
await fs.writeFile(path.join(DIR,'editable-counts.json'),JSON.stringify(P.slides.items.map((s,i)=>({slide:i+1,shapes:s.shapes.items.length,images:s.images.items.length,charts:s.charts.items.length})),null,2));
for(let i=0;i<P.slides.items.length;i++){const png=await P.export({slide:P.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(DIR,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await png.arrayBuffer()));console.log('RENDER',i+1);}
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:draft,finalPath:OUT,pythonExecutable:PY,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','15240000,8572500','--validate-heading-fit'],explicitTotalSlideCount:14,requiredNativeChartOwnerSlides:[3,8,11,14],requiredNativeTableOwnerSlides:[],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[F.title,F.body,F.sans]},verifyArtifactToolImport:true,receiptPath:path.join(DIR,'validation.json')});console.log('FINAL',JSON.stringify(result));
