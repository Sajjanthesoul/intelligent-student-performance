"use client";
import {useEffect,useState} from "react";
import {Activity,ArrowUpRight,BookOpen,BrainCircuit,ChartNoAxesCombined,ChevronRight,Database,GraduationCap,Layers3,Menu,Microscope,ShieldCheck,Target,Users,X} from "lucide-react";

type Section="overview"|"models"|"methodology"|"responsible";
const models=[
 {name:"Logistic Regression",accuracy:59.62,f1:54.48,color:"cyan"},
 {name:"Decision Tree",accuracy:58.81,f1:56.25,color:"violet"},
 {name:"Random Forest",accuracy:59.90,f1:55.35,color:"blue"}
];
const signals=[
 {title:"Learning engagement",detail:"Early VLE clicks, active days, unique resources and activity records.",icon:Activity},
 {title:"Assessment signals",detail:"Early assessment averages, score range and submission counts.",icon:Target},
 {title:"Student context",detail:"Course, presentation and selected OULAD demographic attributes.",icon:Users},
 {title:"Study background",detail:"Previous attempts, studied credits and registration timing.",icon:BookOpen}
];
function pct(n:number){return n.toFixed(2)+"%";}
function PageTitle({kicker,title,description}:{kicker:string,title:string,description:string}){return <div className="page-heading"><div className="eyebrow">{kicker}</div><h1>{title}</h1><p>{description}</p></div>;}

export default function Home(){
 const [section,setSection]=useState<Section>("overview");
 const [mobile,setMobile]=useState(false);
 const [api,setApi]=useState("checking");
 useEffect(()=>{
  const url=process.env.NEXT_PUBLIC_API_URL;
  if(!url){setApi("not connected");return;}
  fetch(url.replace(/\/$/,"")+"/health",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error();return r.json();}).then(()=>setApi("connected")).catch(()=>setApi("unavailable"));
 },[]);
 const nav=[{id:"overview" as Section,label:"Overview",icon:ChartNoAxesCombined},{id:"models" as Section,label:"Model benchmark",icon:Target},{id:"methodology" as Section,label:"Methodology",icon:Microscope},{id:"responsible" as Section,label:"Responsible AI",icon:ShieldCheck}];
 const bestAcc=[...models].sort((a,b)=>b.accuracy-a.accuracy)[0];
 const bestF1=[...models].sort((a,b)=>b.f1-a.f1)[0];
 const change=(s:Section)=>{setSection(s);setMobile(false);};
 return <main className="shell">
  <aside className={"sidebar "+(mobile?"open":"")}>
   <div className="brand"><div className="brand-mark"><GraduationCap size={22}/></div><div><div className="brand-name">student<span>IQ</span></div><small>LEARNING INTELLIGENCE</small></div><button className="close mobile-only" onClick={()=>setMobile(false)}><X size={18}/></button></div>
   <div className="nav-caption">WORKSPACE</div>
   <nav>{nav.map(n=>{const I=n.icon;return <button key={n.id} className={"nav-item "+(section===n.id?"active":"")} onClick={()=>change(n.id)}><I size={17}/>{n.label}{section===n.id&&<ChevronRight size={14}/>}</button>;})}</nav>
   <div className="side-spacer"/>
   <div className="dataset"><div className="dataset-icon"><Database size={17}/></div><b>Research dataset</b><p>Open University Learning Analytics Dataset</p><small><i/> OULAD · 7 source tables</small></div>
   <div className="profile"><div className="avatar">SI</div><div><b>StudentIQ Research</b><small>Conference edition</small></div></div>
  </aside>
  {mobile&&<button className="backdrop" onClick={()=>setMobile(false)} aria-label="Close menu"/>}
  <section className="main">
   <header className="topbar"><div className="crumb"><button className="mobile-only menu" onClick={()=>setMobile(true)}><Menu size={19}/></button>Research workspace <span>/</span> <b>{nav.find(n=>n.id===section)?.label}</b></div><div className="top-right"><span className={"api-dot "+(api==="connected"?"good":api==="checking"?"wait":"bad")}/><small>{api==="connected"?"API connected":api==="checking"?"Checking API":"API not connected"}</small><span className="edition">✦ RESEARCH PREVIEW</span></div></header>
   <div className="content">
    {section==="overview"&&<>
     <div className="page-heading row-heading"><div><div className="eyebrow">INTELLIGENT LEARNING ANALYTICS</div><h1>Performance, <em>with perspective.</em></h1><p>An early-warning research prototype exploring how learning activity and assessment signals relate to student outcomes.</p></div><a className="outline" href="https://github.com/Sajjanthesoul/intelligent-student-performance/tree/conference-upgrade" target="_blank" rel="noreferrer">View research repository <ArrowUpRight size={14}/></a></div>
     <div className="hero"><div className="hero-copy"><div className="hero-kicker"><i/> RESEARCH SNAPSHOT <span/> OULAD · FOUR-CLASS CLASSIFICATION</div><h2>See the signals.<br/><em>Support the student.</em></h2><p>StudentIQ investigates early indicators of academic outcomes using a reproducible feature-engineering and machine-learning workflow.</p><button onClick={()=>change("methodology")}>Explore the methodology <ArrowUpRight size={15}/></button></div><div className="hero-graphic"><div className="orbit o1"/><div className="orbit o2"/><div className="core"><BrainCircuit size={43}/><b>AI</b></div><div className="chip c1">◈ Engagement</div><div className="chip c2">◎ Assessment</div><div className="chip c3">▦ Outcomes</div></div><div className="hero-foot"><span>01 / RESEARCH OVERVIEW</span><span>EARLY SIGNALS · HUMAN-CENTRED INSIGHT</span></div></div>
     <div className="section-head"><div><small>MODEL EVALUATION</small><h2>Benchmark at a glance</h2></div><button onClick={()=>change("models")}>Full comparison <ArrowUpRight size={14}/></button></div>
     <div className="metrics">
      <Metric label="HIGHEST ACCURACY" value={pct(bestAcc.accuracy)} note={bestAcc.name} tone="cyan"/>
      <Metric label="HIGHEST WEIGHTED F1" value={pct(bestF1.f1)} note={bestF1.name} tone="violet"/>
      <Metric label="PREDICTION TASK" value="4 classes" note="Pass · Distinction · Fail · Withdrawn" tone="blue"/>
      <Metric label="EARLY WINDOW" value="Day 60" note="Feature availability cutoff" tone="amber"/>
     </div>
     <div className="grid-two">
      <div className="panel"><div className="panel-title"><div><small>COMPARATIVE RESULTS</small><h3>Model performance</h3></div><span>SCORE (%)</span></div><div className="legend"><i className="a"/> Accuracy <i className="f"/> Weighted F1</div><div className="bars">{models.map(m=><div className="bar-row" key={m.name}><label>{m.name}</label><div className="bar-pair"><div className="track"><i className="bar accuracy" style={{width:m.accuracy+"%"}}/></div><div className="track"><i className="bar f1" style={{width:m.f1+"%"}}/></div></div><small>{pct(m.accuracy)} / {pct(m.f1)}</small></div>)}</div><div className="footnote">Preliminary experiment snapshot. Validation protocol needs strengthening before publication.</div></div>
      <div className="panel insight"><small>RESEARCH HIGHLIGHT</small><h3>Different metrics tell different stories.</h3><p>Random Forest has the highest recorded accuracy, while Decision Tree leads on weighted F1 in this experiment snapshot.</p><div className="insight-line"><span>ACCURACY LEADER</span><b>{bestAcc.name}</b><strong>{pct(bestAcc.accuracy)}</strong></div><div className="insight-line"><span>WEIGHTED F1 LEADER</span><b>{bestF1.name}</b><strong>{pct(bestF1.f1)}</strong></div><div className="insight-note">Add macro-F1, per-class recall, class-imbalance analysis and a course-presentation holdout.</div><button className="panel-link" onClick={()=>change("models")}>Review model results <ChevronRight size={14}/></button></div>
     </div>
     <div className="section-head"><div><small>FEATURE ENGINEERING</small><h2>Signals considered by the pipeline</h2></div></div>
     <div className="signals">{signals.map(s=>{const I=s.icon;return <div className="signal" key={s.title}><div><I size={18}/></div><b>{s.title}</b><p>{s.detail}</p></div>;})}</div>
     <Notice text="Decision-support research only. Model outputs must not be treated as definitive judgments about students or used as the sole basis for consequential academic decisions."/>
    </>}
    {section==="models"&&<>
     <PageTitle kicker="EXPERIMENTAL RESULTS" title="Model benchmark" description="A transparent view of the currently committed model-comparison metrics. Values are shown as recorded; this website has not executed a new evaluation."/>
     <div className="metrics"><Metric label="BEST ACCURACY" value={pct(bestAcc.accuracy)} note={bestAcc.name} tone="cyan"/><Metric label="BEST WEIGHTED F1" value={pct(bestF1.f1)} note={bestF1.name} tone="violet"/><Metric label="ALGORITHMS" value="03" note="Baseline model comparison" tone="blue"/><Metric label="TARGET" value="4 outcomes" note="Categorical classification" tone="amber"/></div>
     <div className="panel"><div className="panel-title"><div><small>MODEL COMPARISON</small><h3>Accuracy and weighted F1</h3></div><span>PERCENT</span></div><div className="legend"><i className="a"/> Accuracy <i className="f"/> Weighted F1</div><div className="bars large">{models.map(m=><div className="bar-row" key={m.name}><label>{m.name}</label><div className="bar-pair"><div className="track"><i className="bar accuracy" style={{width:m.accuracy+"%"}}/></div><div className="track"><i className="bar f1" style={{width:m.f1+"%"}}/></div></div><small>Accuracy {pct(m.accuracy)} · F1 {pct(m.f1)}</small></div>)}</div></div>
     <div className="panel table-panel"><div className="panel-title"><div><small>REPORTED METRICS</small><h3>Experiment results</h3></div><span>COMMITTED SNAPSHOT</span></div><div className="table-wrap"><table><thead><tr><th>MODEL</th><th>ACCURACY</th><th>WEIGHTED F1</th><th>TOP METRIC</th></tr></thead><tbody>{models.map(m=><tr key={m.name}><td>{m.name}</td><td>{pct(m.accuracy)}</td><td>{pct(m.f1)}</td><td>{m.name===bestAcc.name?"Accuracy leader":m.name===bestF1.name?"Weighted F1 leader":"—"}</td></tr>)}</tbody></table></div><p className="muted">The training script records a random 80/20 split. These figures are preliminary and do not establish generalization to unseen course presentations.</p></div>
     <Notice text="Next experiments: course-presentation holdout, repeated seeds, macro-F1, per-class precision and recall, confusion matrices and calibration checks."/>
    </>}
    {section==="methodology"&&<>
     <PageTitle kicker="RESEARCH DESIGN" title="Methodology" description="The project uses early-course activity to investigate a four-class outcome prediction task while explicitly guarding against future-information leakage."/>
     <div className="dataset-banner"><Database size={27}/><div><small>DATA SOURCE</small><h2>Open University Learning Analytics Dataset</h2><p>De-identified student records, assessments, registrations and virtual learning environment activity.</p><a href="https://analyse.kmi.open.ac.uk/open_dataset/" target="_blank" rel="noreferrer">Official dataset documentation <ArrowUpRight size={13}/></a></div></div>
     <div className="section-head"><div><small>PIPELINE</small><h2>From raw records to evaluation</h2></div></div>
     <div className="timeline">{[["01","Data ingestion","Seven OULAD CSV tables are ingested and joined using course, presentation and student keys.","Spark / PySpark"],["02","Early feature engineering","VLE and assessment features are restricted to information available by the configured day-60 cutoff.","Day 60 cutoff"],["03","Preprocessing","Categorical indexing, one-hot encoding, numeric imputation and feature vector assembly are applied in the model pipeline.","Spark ML Pipeline"],["04","Model training","Logistic Regression, Decision Tree and Random Forest are trained and compared.","3 algorithms"],["05","Evaluation","Accuracy and weighted F1 are recorded on a random holdout split.","80 / 20 split"]].map(s=><div className="step" key={s[0]}><b>{s[0]}</b><div><h3>{s[1]}</h3><p>{s[2]}</p><small>{s[3]}</small></div></div>)}</div>
     <div className="panel"><small>PREDICTION TARGET</small><h3>Four categorical outcomes</h3><div className="outcomes"><span>● Pass</span><span>● Distinction</span><span>● Fail</span><span>● Withdrawn</span></div><p className="muted">The target is categorical (final_result), not a continuous score. The early-warning risk grouping is a research interpretation, not a universal student-risk standard.</p></div>
    </>}
    {section==="responsible"&&<>
     <PageTitle kicker="HUMAN-CENTRED ANALYTICS" title="Responsible AI" description="Student performance analytics can influence real people. StudentIQ is a research and support aid, not an automated decision-maker."/>
     <div className="responsible-banner"><ShieldCheck size={31}/><div><h2>Insight should lead to support — never a label.</h2><p>Predictions are uncertain estimates based on historical patterns. They should be interpreted with context, care and human oversight.</p></div></div>
     <div className="principles">{[["Human oversight","Potential interventions should be reviewed by qualified staff and discussed with appropriate context."],["Privacy by design","Use only necessary data, protect access to records and report aggregate findings wherever possible."],["Fairness review","Evaluate error rates across relevant groups and investigate material performance differences."],["Transparent limitations","Document the dataset, prediction window, validation design, uncertainty and intended use."]].map(x=><div className="panel" key={x[0]}><ShieldCheck size={19}/><h3>{x[0]}</h3><p>{x[1]}</p></div>)}</div>
     <div className="panel"><small>CURRENT LIMITATIONS</small><h3>What the evidence does not establish</h3><ul className="limits"><li>Generalization to new institutions or unseen course presentations.</li><li>Calibration of predicted probabilities or individual-level certainty.</li><li>Fairness across demographic groups or causal explanations of outcomes.</li><li>That an intervention based on a prediction improves student outcomes.</li></ul></div>
     <Notice text="Not for high-stakes automated decisions. Do not use StudentIQ as the sole basis for grading, admissions, discipline, funding or access to educational opportunities."/>
    </>}
    <footer>STUDENTIQ · RESEARCH PROTOTYPE <span>Built for transparent learning analytics ✳</span></footer>
   </div>
  </section>
 </main>;
}
function Metric({label,value,note,tone}:{label:string,value:string,note:string,tone:string}){return <div className="metric"><span className={"metric-symbol "+tone}><Layers3 size={16}/></span><small>{label}</small><strong>{value}</strong><p>{note}</p></div>;}
function Notice({text}:{text:string}){return <div className="notice"><ShieldCheck size={17}/><p>{text}</p></div>;}
