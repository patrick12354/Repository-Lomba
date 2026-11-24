import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
const dir=path.dirname(fileURLToPath(import.meta.url));
const P=Presentation.create({slideSize:{width:1920,height:1080}});
const C={ink:'#272727',paper:'#F3EFDF',red:'#A71916',green:'#2B695E',gray:'#6F6A61',beige:'#C2AA80'};
const fonts={title:'Rustic Printed Stamp',body:'Poppins Light',bold:'Poppins Bold',hand:'Gloria Hallelujah'};
const notes=JSON.parse(await fs.readFile(path.join(dir,'notes.json'),'utf8'));
const assets={};
async function img(s,file,x,y,w,h){if(!assets[file])assets[file]=await fs.readFile(path.join(dir,'assets',file));const b=assets[file];s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:file.endsWith('jpeg')?'image/jpeg':'image/png',position:{left:x,top:y,width:w,height:h},fit:'fill'});}
function box(s,x,y,w,h,fill=C.paper,stroke='none',sw=0,geom='rect'){return s.shapes.add({geometry:geom,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:sw,style:'solid'}});}
function txt(s,t,x,y,w,h,size=32,color=C.ink,font=fonts.body,align='left'){const a=box(s,x,y,w,h,'none');a.text=t;a.text.style={typeface:font,fontSize:size,color,insets:0,alignment:align,verticalAlignment:'middle',autoFit:'none',wrap:'square'};return a;}
function line(s,x,y,w,h=2,color=C.ink){box(s,x,y,w,Math.max(h,2),color);}
function dot(s,x,y,r,color){box(s,x-r,y-r,r*2,r*2,color,'none',0,'ellipse');}
function arrow(s,x,y,w=85,color=C.red){box(s,x,y,w,24,color,'none',0,'rightArrow');}
async function paper(s,x=105,y=265,w=1710,h=665){await img(s,'image48.png',x,y,w,h);}
async function base(n,title,{layout='paper',tag,foot='Data/angka: laporan submission Heisenberg · NSC 2026'}={}){
 const s=P.slides.add();await img(s,'image1.jpeg',0,0,1920,1080);await img(s,'image10.png',0,0,160,180);await img(s,'image9.png',1735,914,185,166);
 if([1,10,14].includes(n)){s.speakerNotes.text=notes[n-1]+'\n\nSlide video: background saja sesuai permintaan pengguna.';return s;}
 txt(s,tag||`BERKAS 734 / ${n<15?'EXHIBIT '+String(n).padStart(2,'0'):'EXHIBIT A'+(n-14)}`,220,54,1300,40,27,C.beige,fonts.hand);
 txt(s,title,112,108,1680,135,72,C.paper,fonts.title);
 txt(s,String(n).padStart(2,'0'),1745,62,90,45,29,C.paper,fonts.bold,'right');
 if(layout==='paper')await paper(s);
 txt(s,foot,130,992,1680,52,23,C.paper);
 s.speakerNotes.text=(n<=14?notes[n-1]:'Appendix '+title)+'\n\nSumber: BLUEPRINT_VISUAL_BERKAS_734_FINAL.md; laporan submission paper/output/NSC26-DS042_Heisenberg_Data Science.pdf. Diagram tanpa sumbu nilai merupakan skema.';
 return s;
}
function label(s,t,x,y,w=500){txt(s,t,x,y,w,50,29,C.gray,fonts.bold);}
function metric(s,v,l,x,y,w=480,color=C.ink,size=125){txt(s,v,x,y,w,165,size,color,fonts.bold);txt(s,l,x,y+160,w,80,30,C.ink,fonts.body);}
function flow(s,items,x,y,w=1500,h=140){const gap=65,bw=(w-gap*(items.length-1))/items.length;items.forEach((t,i)=>{box(s,x+i*(bw+gap),y,bw,h,C.beige);txt(s,t,x+i*(bw+gap)+18,y+12,bw-36,h-24,30,C.ink,fonts.bold,'center');if(i<items.length-1)arrow(s,x+(i+1)*bw+i*gap+12,y+h/2-12,42);});}
function table(s,vals,x,y,w,h,widths){const t=s.tables.add({rows:vals.length,columns:vals[0].length,left:x,top:y,width:w,height:h,values:vals,columnWidths:widths});t.borders.assign({fill:'#D2C8B0',width:1,style:'solid'});for(let r=0;r<vals.length;r++)for(let c=0;c<vals[0].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?C.ink:(r%2?C.paper:'#E7DFC9');cell.text.style={typeface:r===0?fonts.bold:fonts.body,fontSize:28,color:r===0?C.paper:C.ink,insets:15,verticalAlignment:'middle'};}return t;}
// 01: background for opening video.
await base(1,'');
// 02: availability schematic.
{
 const s=await base(2,'ENTERING THE CRIME SCENE');label(s,'TRAIN',465,300);label(s,'PREDICTION WINDOW',1200,300);
 const rows=['Humidity','Temperature','Pressure','Other sensors'];rows.forEach((t,i)=>{const y=390+i*80;txt(s,t,175,y-14,300,45,30,C.ink,fonts.bold);line(s,470,y+15,660,5,C.gray);if(i===0){txt(s,'734 ?',1200,y-32,440,82,58,C.red,fonts.bold,'center');}else line(s,1180,y+15,475,5,C.green);});
 line(s,1150,370,3,345,C.gray);txt(s,'2,933 TRAINING RECORDS     /     734 TARGET VALUES     /     24 CHANNELS',180,783,1550,67,34,C.ink,fonts.bold,'center');txt(s,'ONE TARGET MISSING. 24 CHANNELS REMAIN.',180,864,1540,48,32,C.red,fonts.title,'center');
 txt(s,'Availability schematic · 30-minute grid · 15.3-day prediction window',185,931,1450,42,23,C.paper);
}
// 03: LOO mechanism + population audit ratios.
{
 const s=await base(3,'CONTAMINATED EVIDENCE');label(s,'LEAVE ONE POINT OUT',175,303,920);const xs=[245,425,605,785,965],ys=[630,580,540,560,625];for(let i=0;i<4;i++){const a=xs[i],b=xs[i+1],ya=ys[i],yb=ys[i+1];for(let j=0;j<24;j++){dot(s,a+(b-a)*j/24,ya+(yb-ya)*j/24,3,C.gray);}}xs.forEach((x,i)=>dot(s,x,ys[i],12,C.ink));dot(s,605,403,18,C.red);line(s,603,425,4,100,C.red);txt(s,'residual',643,443,290,50,31,C.red,fonts.hand);txt(s,'Four neighbours → quadratic estimate',175,717,910,65,32,C.ink,fonts.bold);txt(s,'Ilustrasi prosedur; tidak berskala',175,800,910,40,25,C.gray);
 label(s,'EXTREME-RESIDUAL RATIO',1140,310,570);[['TEMP','5.75'],['PRESSURE','6.86'],['RH TARGET','1.20']].forEach(([l,v],i)=>{txt(s,l,1140,402+i*133,300,46,29,C.ink,fonts.bold);txt(s,v,1445,377+i*133,260,85,68,i===2?C.ink:C.red,fonts.bold);});txt(s,'Quadratic LOO  /  Robust MAD  /  Selective Hampel filter',180,856,1540,53,30,C.ink,fonts.bold);
}
// 04: physical feature reconstruction.
{
 const s=await base(4,'THE HIDDEN CLUE');label(s,'HIDDEN INSIDE DAILY INDICES',175,310,1450);flow(s,['Daily mean\n+ maximum','Reconstructed\nTmin'],175,405,700,135);flow(s,['Ontario CHU\ninverse','Reconstructed\nTmin'],175,590,700,135);metric(s,'0.047°C','SD difference · corr = 0.99986',980,380,650,C.red,105);flow(s,['Tmin','Dew-point\nproxy','Vapor\npressure','RH'],175,798,1520,102);txt(s,'Agreement of two formulas, not independent sensor measurements',175,727,1490,45,27,C.gray);
}
// 05: shift audit.
{
 const s=await base(5,'THE CRIME SCENE HAS CHANGED');label(s,'TRAIN CONDITION',230,320);label(s,'TEST CONDITION',1130,320);metric(s,'27.51°C','Mean temperature',230,385,620,C.ink,120);arrow(s,895,458,145);metric(s,'24.64°C','Mean temperature',1130,385,620,C.red,120);txt(s,'Irrigation records',230,665,600,55,33,C.ink,fonts.bold);txt(s,'Varying',230,730,550,55,38,C.gray,fonts.hand);txt(s,'Constant',1130,730,550,55,38,C.red,fonts.hand);txt(s,'SOIL + IRRIGATION FEATURES EXCLUDED',230,844,1400,60,42,C.red,fonts.title);txt(s,'Recorded constancy does not prove that irrigation stopped',230,923,1430,40,23,C.paper);
}
// 06: five specialists on dark ground.
{
 const s=await base(6,'ASSEMBLING THE INVESTIGATION TEAM',{layout:'dark'});const models=[['01','LightGBM\nHuber','ROBUST SIGNAL'],['02','CatBoost\nHuber','DIVERSE ERRORS'],['03','ElasticNet','LINEAR STRUCTURE'],['04','Ridge-e','VAPOR-PRESSURE VIEW'],['05','LightGBM\nL2','LARGE-ERROR SENSITIVITY']];for(let i=0;i<5;i++){let x=112+i*342;await img(s,'image5.png',x,300,325,555);txt(s,models[i][0],x+40,362,235,70,52,C.red,fonts.title);txt(s,models[i][1],x+38,465,249,150,40,C.ink,fonts.bold);txt(s,models[i][2],x+38,665,249,110,26,C.gray,fonts.body);}txt(s,'Ridge (plain): eliminated',130,891,760,50,30,C.beige,fonts.hand);txt(s,'FIVE COMPLEMENTARY MODELS',985,885,815,70,43,C.paper,fonts.title,'right');
}
// 07: rolling origins with proportional 2/15 shift.
{
 const s=await base(7,'TESTING THEIR ALIBIS');label(s,'PAST / TRAIN',220,310);label(s,'FUTURE / VALIDATE 15 DAYS',1110,310,650);box(s,220,380,850,65,C.gray);box(s,1070,380,530,65,C.green);txt(s,'≥ 30 DAYS',245,383,730,60,30,C.paper,fonts.bold);txt(s,'15 DAYS',1090,383,465,60,30,C.paper,fonts.bold);for(let i=0;i<9;i++){const x=770+i*48,y=495+i*36;txt(s,String(i+1).padStart(2,'0'),220,y-10,80,30,23,C.gray);box(s,330,y,x-330,19,'#BBB5A6');box(s,x,y,360,19,C.green);}txt(s,'9 rolling origins   /   2-day step   /   Overlapping folds',220,844,1400,65,34,C.ink,fonts.bold);txt(s,'Not nine independent tests · Meta-model and corrections separately audited',220,915,1440,45,24,C.paper);
}
// 08: NNLS plus equal parameter control.
{
 const s=await base(8,'COMBINING THE EVIDENCE');flow(s,['Five model\npredictions','Time-banded\nNNLS','25% weight\nshrinkage'],205,325,1480,145);label(s,'NESTED VALIDATION · ΔRMSE',205,510,1300);const x0=1470;line(s,x0,589,3,210,C.ink);box(s,x0-800,597,800,62,C.green);box(s,x0-70,724,70,62,C.gray);txt(s,'Time-based',225,600,400,56,32,C.ink,fonts.bold);txt(s,'Random control',225,728,400,56,32,C.ink,fonts.bold);txt(s,'−0.080',1510,590,230,75,46,C.green,fonts.bold);txt(s,'−0.007',1510,716,230,75,46,C.gray,fonts.bold);txt(s,'Equal number of parameters',225,841,1450,58,34,C.red,fonts.hand);txt(s,'Bars are linear from zero; random grouping applies to the OOF control',225,919,1440,43,24,C.paper);
}
// 09: schematic residual pattern.
{
 const s=await base(9,'THE PATTERN NOBODY NOTICED');label(s,'NEARBY ERRORS DRIFT TOGETHER',185,305,980);line(s,210,500,790,3,C.gray);const ys=[590,610,625,605,580,565,590];ys.forEach((y,i)=>{let x=235+i*115;line(s,x,500,3,y-500,C.red);dot(s,x,y,13,C.red);dot(s,x,500,8,C.gray);});txt(s,'Prediction',205,694,400,55,30,C.red,fonts.bold);txt(s,'Reference',640,694,400,55,30,C.gray,fonts.bold);metric(s,'0.93','Lag-1 autocorrelation\nof level-model errors',1125,386,570,C.red,152);txt(s,'NEW LEAD: MOTION',185,820,1500,72,56,C.red,fonts.title);txt(s,'Ilustrasi pola residual; statistik dari laporan §V-D',185,915,1520,44,24,C.paper);
}
await base(10,'');
// 11: public reconciliation improvement.
{
 const s=await base(11,'THE BREAKTHROUGH IS REAL');label(s,'BEFORE RECONCILIATION',210,330,720);label(s,'AFTER RECONCILIATION',1110,330,690);metric(s,'3.02586','Public RMSE',210,400,720,C.ink,117);arrow(s,935,490,135);metric(s,'2.86595','Public RMSE',1110,400,660,C.green,117);txt(s,'ΔRMSE = −0.15991',210,707,1500,90,65,C.green,fonts.bold,'center');txt(s,'FORWARD AUDIT: B1 −0.043   /   B2 −0.154   /   B3 −0.112',210,833,1500,64,29,C.ink,fonts.bold,'center');txt(s,'Forward audit and public scores are separate evaluations',210,923,1470,40,24,C.paper);
}
// 12: bias sign and partial correction.
{
 const s=await base(12,'THE HIDDEN BIAS');label(s,'CATBOOST · BIAS = PREDICTION − ACTUAL',205,310,1520);const x0=1570,xmin=365;line(s,xmin,530,x0-xmin,4,C.gray);[-3,-2,-1,0].forEach(v=>{const x=x0+v*400;line(s,x,514,3,34,C.ink);txt(s,String(v),x-40,565,80,48,28,C.gray,fonts.body,'center');});dot(s,x0-2.89*400,530,17,C.red);dot(s,x0-.006*400,530,14,C.ink);txt(s,'FORWARD AUDIT\n−2.89 %RH',245,388,580,110,40,C.red,fonts.bold);txt(s,'IN-SAMPLE\n−0.006 %RH',1120,388,590,110,40,C.ink,fonts.bold);flow(s,['OOF estimate\n−1.86 %RH','50% partial\ncorrection','Negative\ncontrols'],215,694,1470,143);txt(s,'Targeted, partial correction',215,864,1470,50,33,C.red,fonts.hand,'center');
}
// 13: rejected experiment, linear dumbbell.
{
 const s=await base(13,'THE REJECTED EVIDENCE');label(s,'PUBLIC RMSE · LOWER IS BETTER',200,309,1490);const xx=v=>280+(v-2.84)/.11*1350;line(s,280,562,1350,4,C.gray);[2.84,2.86,2.88,2.90,2.92,2.94].forEach(v=>{let x=xx(v);line(s,x,546,2,34,C.gray);txt(s,v.toFixed(2),x-54,587,108,40,26,C.gray,fonts.body,'center');});line(s,xx(2.86595),562,xx(2.93028)-xx(2.86595),6,C.red);dot(s,xx(2.86595),564,17,C.green);dot(s,xx(2.93028),564,17,C.red);txt(s,'2.86595\nRetained configuration',215,400,720,116,44,C.green,fonts.bold);txt(s,'2.93028\nAdded increment package',1060,400,730,116,44,C.red,fonts.bold);txt(s,'REJECTED / +0.06433 WORSE',230,679,1450,80,60,C.red,fonts.title);txt(s,'REAL-TIME NEEDS CAUSAL DATA',230,792,1490,50,32,C.ink,fonts.bold);txt(s,'NO CROP-OUTCOME CLAIM',230,855,1480,50,32,C.ink,fonts.bold);
}
await base(14,'');
// A1: actual audit image and metrics.
{
 const s=await base(15,'ANATOMY OF THE EVIDENCE',{foot:'Source: submission · data audit / Hampel exhibit · Figure 11'});label(s,'2,933 TRAIN / 734 TEST / 24 CHANNELS',195,305,1460);const b=await fs.readFile(path.join(dir,'../../paper/figures/11-despiking.png'));s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',position:{left:190,top:394,width:1020,height:560},fit:'contain'});txt(s,'30-minute grid\nOne 7-hour train gap',1260,379,440,105,31,C.ink,fonts.bold);metric(s,'0.49%','Temperature points changed\nin the stated audit population',1260,508,440,C.red,76);txt(s,'SD: 2.715 → 0.515\nRobust SD: 0.472 → 0.408',1260,777,440,120,29,C.ink,fonts.bold);
}
// A2: evaluation boundaries.
{
 const s=await base(16,'FAIR TIME-SERIES EVALUATION');const lanes=[['BASE MODEL OOF','Past labels → next 15-day predictions'],['META FITTING','OOF predictions → NNLS / shrinkage'],['NESTED-FORWARD AUDIT','Past meta fitting → later held-out block']];lanes.forEach(([a,b],i)=>{const y=340+i*166;box(s,195,y,500,120,C.beige);txt(s,a,220,y+20,450,80,31,C.ink,fonts.bold);arrow(s,735,y+46,110);txt(s,b,895,y+20,820,90,34,C.ink,fonts.body);});txt(s,'9 origins / 15-day horizon / ≥30-day train / 2-day step',195,844,1490,58,32,C.red,fonts.bold);txt(s,'OOF alone does not make every stack estimate unbiased',195,922,1460,40,24,C.paper);
}
// A3: native model table.
{
 const s=await base(17,'WHY THESE FIVE MODELS?');table(s,[['Model','Role / loss','Overall weight'],['LightGBM Huber','Robust level signal','0.489'],['CatBoost Huber','Diverse errors / Huber','0.217'],['ElasticNet','Linear / L1 + L2','0.194'],['Ridge-e','Vapor-pressure / L2','0.050'],['LightGBM L2','Large-error sensitivity','0.050']],190,325,1520,475,[520,710,290]);txt(s,'CatBoost residual corr. = 0.64 (audit)  /  Shrinkage = 25%',190,838,1520,55,31,C.red,fonts.bold);txt(s,'Overall weights shown; time-band weights vary',190,920,1490,44,24,C.paper);
}
// A4: physics equations and caveat.
{
 const s=await base(18,'PHYSICS OF RELATIVE HUMIDITY');txt(s,'RH = 100 × e / es(T)',205,316,1500,100,76,C.red,fonts.bold);flow(s,['Daily mean + max\nOR Ontario CHU','Reconstructed\nTmin','Dew-point\nproxy'],205,475,1470,145);txt(s,'76 days  /  corr = 0.99986  /  SD difference = 0.047°C',205,667,1480,67,38,C.ink,fonts.bold);txt(s,'Magnus–Bolton saturation vapor pressure',205,755,1460,63,37,C.ink,fonts.body);txt(s,'Daily indices may require information unavailable in real time',205,852,1480,58,29,C.red,fonts.hand);
}
// A5: reconciliation objective and native evidence table.
{
 const s=await base(19,'TEMPORAL RECONCILIATION MATH');txt(s,'min z  ‖z − p‖² + 4‖D1z − d1‖² + ‖D4z − d4‖²',185,324,1550,92,49,C.red,fonts.bold);txt(s,'D1: 30 minutes   /   D4: 2 hours   /   Relative weights 4 : 1',185,440,1540,56,30,C.ink,fonts.bold);table(s,[['Increment OOF · 6,471 rows','Level-derived RMSE','Increment-model RMSE'],['30 minutes','1.91','1.81'],['2 hours','3.57','3.52']],185,550,1530,258,[670,430,430]);txt(s,'Forward ΔRMSE: B1 −0.043 / B2 −0.154 / B3 −0.112',185,854,1520,60,31,C.green,fonts.bold);
}
// A6: falsification controls.
{
 const s=await base(20,'BIAS & FALSIFICATION CONTROLS');label(s,'CATBOOST BIAS (%RH)',190,310,1400);txt(s,'In-sample −0.006   /   Forward −2.89   /   OOF −1.86',190,380,1530,85,44,C.ink,fonts.bold);table(s,[['Correction control','ΔRMSE','Improved blocks'],['Half OOF correction','−0.077','5 / 6'],['Wrong direction','+0.162','0 / 6'],['Near-unbiased member','+0.017','No benefit reported']],190,527,1520,319,[820,300,400]);txt(s,'Related public comparison: 2.84953 → 2.82744',190,866,1500,50,35,C.green,fonts.bold);
}
// A7: native public ledger, no fake linear experiment history.
{
 const s=await base(21,'PUBLIC SUBMISSION LEDGER');table(s,[['Experiment branch','Before','After','Decision'],['Temporal reconciliation','3.02586','2.86595','Retained'],['Additional increment package','2.86595','2.93028','Rejected'],['Partial bias correction','2.84953','2.82744','Retained']],185,346,1550,435,[730,260,260,300]);txt(s,'Separate paired comparisons; not a single monotonic ladder',185,835,1540,60,32,C.ink,fonts.bold);txt(s,'Public feedback influenced some post-model correction choices',185,916,1540,43,25,C.paper);
}
// A8: reproducibility and information availability.
{
 const s=await base(22,'REPRODUCIBILITY & DEPLOYMENT LIMITS');flow(s,['Data\naudit','Physical\nfeatures','Level\nensemble','Temporal\nreconciliation','Bias\ncheck'],190,329,1515,132);label(s,'COMPETITION INFORMATION',190,528,690);label(s,'REAL-TIME DEPLOYMENT',1010,528,720);txt(s,'Full exogenous prediction window\nCentered / neighbouring features',190,603,695,142,34,C.ink,fonts.body);txt(s,'Only information available now\nCausal features must be retested',1010,603,710,142,34,C.red,fonts.body);txt(s,'Reproduce: dataset / splits / seeds / parameters / feature windows / solver',190,811,1520,83,29,C.ink,fonts.bold);txt(s,'Pooled OOF: 6,480 rows · Crop effects and causal full-stack performance untested',190,927,1540,45,23,C.paper);
}
// R: provenance and references drawn from the provided submission.
{
 const s=await base(23,'REFERENCES & DATA PROVENANCE',{tag:'BERKAS 734 / REFERENCE FILE',foot:'Bibliographic details follow the supplied study submission'});const refs=[['STUDY & DATA','Heisenberg — NSC 2026 Data Science submission; supplied train/test data.'],['ROBUST ESTIMATION','Huber (1964), Robust Estimation of a Location Parameter; Hampel (1974).'],['MODEL METHODS','Ke et al. (2017), LightGBM; Prokhorenkova et al. (2018), CatBoost.'],['ENSEMBLE & VALIDATION','Lawson & Hanson (1974), NNLS; Wolpert (1992), Stacked Generalization;\nBergmeir & Benítez (2012), cross-validation for time-series evaluation.'],['PHYSICS & AGRONOMY','Bolton (1980), thermodynamics; Allen et al. (1998), FAO Paper 56;\nOntario Ministry of Agriculture (1993), Crop Heat Units.']];refs.forEach(([a,b],i)=>{const y=310+i*124;txt(s,a,190,y,460,55,26,C.red,fonts.bold);txt(s,b,690,y-4,1020,104,29,C.ink,fonts.body);});s.speakerNotes.text+='\nFull bibliography: paper/script/content.py, PUSTAKA. Narrative character Pak Anton is fictional. Blueprint and script are creative sources, not independent statistical verification.';
}
await (await PresentationFile.exportPptx(P)).save(path.join(dir,'candidate.pptx'));
console.log('Authored',P.slides.items.length,'slides');
