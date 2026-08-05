import { useEffect, useState } from "react";


const LOADING_STAGES = [
  "Checking memory database...",
  "Matching known bug patterns...",
  "Analyzing stack evidence...",
  "Finding root cause...",
  "Generating production fix..."
];


function useLoadingStage(active) {

  const [index,setIndex] = useState(0);


  useEffect(()=>{

    if(!active){
      setIndex(0);
      return;
    }


    const timer=setInterval(()=>{

      setIndex(i =>
        i < LOADING_STAGES.length-1
        ? i+1
        : i
      );

    },900);


    return ()=>clearInterval(timer);


  },[active]);


  return LOADING_STAGES[index];

}




function confidenceTier(score){

  if(score>=80)
    return "HIGH";

  if(score>=50)
    return "MEDIUM";

  return "LOW";

}


// Maps a confidence tier to the existing color tokens (ai / amber / redAccent)
// so the stamp never introduces a color that isn't already in the palette.
function tierStyles(tier){

  if(tier==="HIGH")
    return {
      border: "border-ai/60",
      text: "text-ai",
      bg: "bg-aiSoft",
      label: "ROOT CAUSE CONFIRMED"
    };

  if(tier==="MEDIUM")
    return {
      border: "border-amber/60",
      text: "text-amber",
      bg: "bg-amber/10",
      label: "LIKELY ROOT CAUSE"
    };

  return {
    border: "border-redAccent/60",
    text: "text-redAccent",
    bg: "bg-redAccent/10",
    label: "NEEDS HUMAN REVIEW"
  };

}




function ConfidenceCard({score=0}){


return (

<div
className="
rounded-2xl
border
border-white/10
bg-white/5
p-4
text-center
"
>

<p
className="
text-xs
font-mono
text-textSecondary
"
>
CONFIDENCE
</p>


<p
className="
mt-2
text-4xl
font-bold
text-ai
"
>
{score}%
</p>


<p
className="
font-mono
text-xs
text-textDim
"
>
{confidenceTier(score)}
</p>


</div>

);

}


// The signature moment: a rotated stamp that "lands" on the report once
// the investigation resolves. Tier drives both the label and the color,
// so a low-confidence result visibly reads as "needs review", not a fake win.
function CaseStamp({score=0}){

  const tier = confidenceTier(score);
  const styles = tierStyles(tier);

  return (

    <div
      className={`
      trace-stamp-in
      pointer-events-none
      select-none
      inline-flex
      items-center
      gap-2
      rounded-lg
      border-2
      border-dashed
      ${styles.border}
      ${styles.bg}
      px-3
      py-1.5
      -rotate-6
      `}
    >
      <span className={`font-mono text-[10px] tracking-widest font-bold ${styles.text}`}>
        {styles.label}
      </span>
    </div>

  );

}




function Section({
title,
children
}){

if(!children)
return null;


return (

<div
className="
rounded-2xl
border
border-white/10
bg-black/20
p-5
"
>

<p
className="
mb-3
font-mono
text-xs
tracking-widest
text-textDim
"
>
{title}
</p>


<div
className="
text-sm
leading-relaxed
text-textPrimary
"
>
{children}
</div>


</div>

);

}





function Badge({children}){

return (

<span
className="
rounded-full
border
border-ai/30
bg-aiSoft
px-3
py-1
font-mono
text-xs
text-ai
"
>
{children}
</span>

);

}





export default function ResultPanel({

status,
result,
mode,
elapsedMs,
onCopyFix,
copied

}){


const stage =
useLoadingStage(status==="loading");


const stampStyles = (
  <style>{`
    @keyframes traceStampIn {
      0%   { transform: scale(1.6) rotate(-6deg); opacity: 0; }
      55%  { transform: scale(0.92) rotate(-6deg); opacity: 1; }
      100% { transform: scale(1) rotate(-6deg); opacity: 1; }
    }
    .trace-stamp-in { animation: traceStampIn 0.4s ease-out both; }
    @media (prefers-reduced-motion: reduce) {
      .trace-stamp-in { animation: none; }
    }
  `}</style>
);




if(status==="idle"){


return (

<div
className="
flex
min-h-[420px]
items-center
justify-center
rounded-3xl
border
border-dashed
border-white/10
bg-tracePanel/50
p-10
text-center
"
>

<div>

<div
className="
mx-auto
mb-5
h-16
w-16
rounded-full
bg-aiSoft
flex
items-center
justify-center
text-3xl
"
>
🤖
</div>


<h3
className="
text-xl
font-semibold
"
>
Waiting for evidence
</h3>


<p
className="
mt-3
max-w-sm
text-sm
text-textSecondary
"
>
Paste a stack trace and Trace AI will investigate the failure.
</p>


</div>


</div>

);

}





if(status==="loading"){


return (

<div
className="
rounded-3xl
border
border-ai/20
bg-tracePanel
p-8
shadow-aiGlow
"
>


<div
className="
flex
items-center
gap-4
"
>

<div
className="
h-12
w-12
rounded-full
border-4
border-white/10
border-t-ai
animate-spin
"
/>


<div>

<p
className="
font-mono
text-ai
"
>
TRACE ENGINE RUNNING
</p>


<p
className="
mt-1
text-sm
text-textSecondary
"
>
{stage}
</p>


</div>


</div>



<div
className="
mt-8
space-y-3
"
>

{
LOADING_STAGES.map((item,i)=>(

<div
key={item}
className={`
flex
gap-3
font-mono
text-sm
${i <= LOADING_STAGES.indexOf(stage)
? "text-ai"
: "text-textDim"}
`}
>

<span>
{i <= LOADING_STAGES.indexOf(stage)
?"●"
:"○"}
</span>

{item}

</div>

))
}


</div>


</div>

);

}





if(status==="error"){


return (

<div
className="
rounded-3xl
border
border-redAccent/30
bg-redAccent/10
p-8
"
>

<h3
className="
font-semibold
text-redAccent
"
>
Investigation failed
</h3>


<p
className="
mt-3
text-sm
text-textSecondary
"
>
The AI engine could not complete the analysis. Try again.
</p>


</div>

);

}





if(!result)
return null;





return (

<div
className="
space-y-5
rounded-3xl
border
border-white/10
bg-tracePanel/80
p-6
shadow-glass
animate-fadeUp
"
>

{stampStyles}


{/* Header */}

<div
className="
flex
items-center
justify-between
"
>

<div>

<p
className="
font-mono
text-xs
tracking-widest
text-ai
"
>
AI INVESTIGATION REPORT
</p>


<h2
className="
mt-2
text-2xl
font-bold
"
>
{
mode==="quick"
?"Instant Fix"
:"Full Analysis"
}
</h2>


<div className="mt-3 flex flex-wrap items-center gap-2">

<Badge>
{result.source || "AI analysis"}
</Badge>


{elapsedMs && (

<Badge>
{(elapsedMs/1000).toFixed(1)}s
</Badge>

)}

<CaseStamp score={result.confidence_score ?? 0} />


</div>


</div>


<ConfidenceCard
score={result.confidence_score ?? 0}
/>


</div>





{/* Fix */}

<Section title="RECOMMENDED FIX">


<p
className="
rounded-xl
border
border-ai/20
bg-aiSoft
p-4
font-mono
text-ai
"
>

{result.fix_recommendation}

</p>


<button

onClick={onCopyFix}

className="
mt-4
rounded-xl
border
border-white/10
px-4
py-2
font-mono
text-xs
hover:border-ai
hover:text-ai
transition-colors
"

>

{
copied
?"Copied ✓"
:"Copy fix"
}


</button>


</Section>





<Section title="ROOT CAUSE">

{result.root_cause}

</Section>





{result.investigation_steps?.length>0 && (

<Section title="INVESTIGATION TIMELINE">

<div className="space-y-3">

{
result.investigation_steps.map((step,i)=>(

<div
key={i}
className="
flex
gap-3
"
>

<span
className="
text-ai
font-mono
"
>
0{i+1}
</span>

<span>
{step}
</span>


</div>

))
}


</div>


</Section>

)}





{result.evidence?.length>0 && (

<Section title="EVIDENCE">

<ul className="space-y-3">

{
result.evidence.map((item,i)=>(

<li
key={i}
className="
border-l-2
border-amber
pl-3
"
>
<span className="mr-2 font-mono text-[10px] tracking-widest text-amber">
EVIDENCE #{String(i+1).padStart(2,"0")}
</span>
<span className="block mt-1">{item}</span>
</li>

))
}

</ul>


</Section>

)}





<button

onClick={()=>navigator.clipboard.writeText(
JSON.stringify(result,null,2)
)}

className="
w-full
rounded-xl
border
border-white/10
py-3
font-mono
text-sm
hover:border-ai
hover:text-ai
transition-colors
"

>

Copy full investigation report

</button>



</div>

);


}