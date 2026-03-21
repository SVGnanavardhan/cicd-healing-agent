import { useEffect, useRef, useCallback } from "react";
import { useAgent } from "./context/AgentContext.jsx";

// ─── Design tokens (mirrors CSS vars in preview.html) ─────────────────────────
const C = {
  bg:"#04060c", surface:"#080d18", panel:"#0c1220",
  border:"#1a2540", borderHi:"#243352",
  accent:"#00d4ff", green:"#00ff88", greenDim:"#007744",
  red:"#ff3b5c", redDim:"#8a1428",
  amber:"#ffaa00", amberDim:"#664400",
  purple:"#a855f7",
  text:"#e8f0fe", textSub:"#6b7fa8", textDim:"#2d3f5e",
};

// ─── Spec-critical: exact branch name format ──────────────────────────────────
function branchPart(s) {
  return s.toUpperCase().replace(/[^A-Z0-9]/g,"_").replace(/_+/g,"_").replace(/^_|_$/g,"");
}
export function buildBranch(team, leader) {
  return `${branchPart(team)}_${branchPart(leader)}_AI_Fix`;
}

// ─── Spec-critical: exact judge test-case output format ───────────────────────
const FIX_DESC = {
  LINTING:     "remove the import statement",
  SYNTAX:      "add the colon at the correct position",
  LOGIC:       "implement proper exception handling",
  TYPE_ERROR:  "use identity comparison",
  IMPORT:      "use explicit imports",
  INDENTATION: "replace tabs with 4 spaces",
};
export function dashboardOutput(bugType, file, line) {
  return `${bugType} error in ${file} line ${line} → Fix: ${FIX_DESC[bugType]}`;
}

// ─── Bug type styles ──────────────────────────────────────────────────────────
const BUG_STYLE = {
  LINTING:     { c:"#60a5fa", bg:"#1e3a5f" },
  SYNTAX:      { c:"#ffaa00", bg:"#3d2800" },
  LOGIC:       { c:"#c084fc", bg:"#2e1a4a" },
  TYPE_ERROR:  { c:"#f472b6", bg:"#3d1530" },
  IMPORT:      { c:"#34d399", bg:"#0d3324" },
  INDENTATION: { c:"#fb923c", bg:"#3d1f0a" },
};
const BUG_TYPES = ["ALL","LINTING","SYNTAX","LOGIC","TYPE_ERROR","IMPORT","INDENTATION"];
const PHASE_COLORS = {
  CLONING:C.accent, ANALYZING:C.amber, FIXING:C.purple,
  COMMITTING:C.green, MONITORING:"#ff8844", COMPLETE:C.green,
};

// ─── Agent simulation (mirrors backend pipeline) ──────────────────────────────
function simulateAgentRun(repo, team, leader, maxIter, onUpdate) {
  const br = buildBranch(team, leader);

  const FAILS = [
    { file:"src/utils.py",     line:15, bug_type:"LINTING",     description:"Unused import 'os'",                     dashboard_output:dashboardOutput("LINTING",    "src/utils.py",     15) },
    { file:"src/validator.py", line:8,  bug_type:"SYNTAX",      description:"Missing colon after function definition", dashboard_output:dashboardOutput("SYNTAX",     "src/validator.py", 8)  },
    { file:"src/processor.py", line:34, bug_type:"LOGIC",       description:"Bare except clause — too broad",          dashboard_output:dashboardOutput("LOGIC",      "src/processor.py", 34) },
    { file:"src/models.py",    line:22, bug_type:"TYPE_ERROR",  description:"Use 'is None' not '== None'",             dashboard_output:dashboardOutput("TYPE_ERROR", "src/models.py",    22) },
    { file:"src/helpers.py",   line:5,  bug_type:"IMPORT",      description:"Wildcard import detected",                dashboard_output:dashboardOutput("IMPORT",     "src/helpers.py",   5)  },
    { file:"src/config.py",    line:11, bug_type:"INDENTATION", description:"Tabs detected (use 4 spaces)",            dashboard_output:dashboardOutput("INDENTATION","src/config.py",    11) },
  ];
  const FIXES = FAILS.map(f => ({
    ...f,
    commit_message: `[AI-AGENT] Fix ${f.bug_type} in ${f.file} line ${f.line}`,
    status: Math.random() > 0.12 ? "Fixed" : "Failed",
  }));
  const CI = [
    { iteration:1, timestamp:new Date().toISOString(),                  status:"FAILED", passed:2, failed:4, output:"flake8: 6 issues found\npytest: 3 FAILED, 2 passed" },
    { iteration:2, timestamp:new Date(Date.now()+52000).toISOString(),  status:"FAILED", passed:4, failed:2, output:"flake8: 2 issues found\npytest: 1 FAILED, 4 passed" },
    { iteration:3, timestamp:new Date(Date.now()+98000).toISOString(),  status:"PASSED", passed:6, failed:0, output:"flake8: 0 issues\npytest: 6 passed in 1.24s ✓"      },
  ];
  const PHASES = [
    { ph:"CLONING",    msg:`Cloning ${repo}...`,                                              d:500   },
    { ph:"CLONING",    msg:`Branch created: ${br}`,                                           d:1300  },
    { ph:"ANALYZING",  msg:"ClonerAgent → AnalyzerAgent handoff complete",                    d:2100  },
    { ph:"ANALYZING",  msg:`Scanning ${new Set(FAILS.map(f=>f.file)).size} source files...`,  d:2800  },
    { ph:"ANALYZING",  msg:`AnalyzerAgent: Found ${FAILS.length} issues`,                     d:3500  },
    { ph:"FIXING",     msg:"AnalyzerAgent → FixerAgent handoff",                              d:4200  },
    { ph:"FIXING",     msg:"FixerAgent: Applying targeted patches...",                        d:5000  },
    { ph:"FIXING",     msg:`FixerAgent: ${FIXES.filter(f=>f.status==="Fixed").length} fixes applied`, d:5800 },
    { ph:"COMMITTING", msg:"FixerAgent → CommitterAgent handoff",                             d:6400  },
    { ph:"COMMITTING", msg:`[AI-AGENT] Commit #1 pushed to ${br}`,                           d:7100  },
    { ph:"MONITORING", msg:"CommitterAgent → MonitorAgent handoff",                           d:7800  },
    { ph:"MONITORING", msg:"MonitorAgent: CI/CD Run #1 — running flake8 + pytest...",         d:8600  },
    { ph:"MONITORING", msg:"MonitorAgent: Run #1 FAILED — 4 checks still failing",            d:9400  },
    { ph:"FIXING",     msg:"Re-analyzing remaining failures...",                              d:10200 },
    { ph:"COMMITTING", msg:"[AI-AGENT] Commit #2 pushed",                                     d:11400 },
    { ph:"MONITORING", msg:"MonitorAgent: Run #2 FAILED — 2 checks remaining",               d:12600 },
    { ph:"FIXING",     msg:"Final pass — applying remaining patches...",                      d:13400 },
    { ph:"COMMITTING", msg:"[AI-AGENT] Commit #3 pushed",                                     d:14200 },
    { ph:"MONITORING", msg:"MonitorAgent: Run #3 — ALL CHECKS PASSED ✓",                     d:15600 },
    { ph:"COMPLETE",   msg:`Done. results.json written. Branch: ${br}`,                       d:16400 },
  ];

  let cancelled = false;
  const T = [];
  PHASES.forEach(({ ph, msg, d }) => T.push(setTimeout(() => { if (!cancelled) onUpdate({ type:"log", phase:ph, msg }); }, d)));
  FAILS.forEach((f, i) => T.push(setTimeout(() => { if (!cancelled) onUpdate({ type:"failure", failure:f }); }, 3600 + i * 130)));
  FIXES.forEach((f, i) => T.push(setTimeout(() => { if (!cancelled) onUpdate({ type:"fixes", fixes:FIXES.slice(0, i + 1) }); }, 5900 + i * 200)));
  CI.forEach((run, i) => T.push(setTimeout(() => { if (!cancelled) onUpdate({ type:"cirun", run }); }, 9500 + i * 3800)));

  const t0 = Date.now();
  T.push(setTimeout(() => {
    if (cancelled) return;
    const elapsed = Math.round((Date.now() - t0) / 1000);
    const bonus = elapsed < 300 ? 10 : 0;
    const pen = 0;
    onUpdate({
      type: "complete",
      result: {
        final_status:"PASSED", branch_name:br,
        total_failures:FAILS.length,
        total_fixes:FIXES.filter(f=>f.status==="Fixed").length,
        commit_count:3,
        total_time_seconds:elapsed,
        total_time_display:`${Math.floor(elapsed/60)}m ${elapsed%60}s`,
        score:{ base:100, speed_bonus:bonus, efficiency_penalty:pen, total:100+bonus-pen },
        failures:FAILS, fixes:FIXES, ci_runs:CI,
      },
    });
  }, 16700));

  return () => { cancelled = true; T.forEach(clearTimeout); };
}

// ─── Shared UI ────────────────────────────────────────────────────────────────
const s = {
  panel: { background:C.panel, border:`1px solid ${C.border}`, borderRadius:10, overflow:"hidden", boxShadow:"0 2px 12px #00000040", marginBottom:18 },
  ph:    { padding:"13px 20px", borderBottom:`1px solid ${C.border}`, background:C.surface, display:"flex", justifyContent:"space-between", alignItems:"center" },
  phl:   { display:"flex", alignItems:"center", gap:8 },
  pt:    { fontFamily:"monospace", fontSize:10, letterSpacing:2, color:C.textSub, textTransform:"uppercase" },
  icard: { background:C.surface, border:`1px solid ${C.border}`, borderRadius:8, padding:"13px 15px" },
};

function Panel({ children, style = {} }) {
  return <div style={{ ...s.panel, ...style }}>{children}</div>;
}
function PH({ icon, title, right }) {
  return (
    <div style={s.ph}>
      <div style={s.phl}><span>{icon}</span><span style={s.pt}>{title}</span></div>
      {right}
    </div>
  );
}
function Badge({ label, color, large = false, pulse = false }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10, background:`${color}12`, border:`1.5px solid ${color}`, borderRadius:7, padding:large?"7px 18px":"3px 10px", boxShadow:`0 0 14px ${color}25` }}>
      <div style={{ width:large?9:6, height:large?9:6, borderRadius:"50%", background:color, boxShadow:`0 0 7px ${color}`, animation:pulse?"pulse 1s infinite":"none" }}/>
      <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:large?20:10, letterSpacing:3, color }}>{label}</span>
    </div>
  );
}
function BugBadge({ type }) {
  const s2 = BUG_STYLE[type] || { c:C.accent, bg:"#1a2540" };
  return <span style={{ background:s2.bg, color:s2.c, padding:"3px 8px", borderRadius:4, fontSize:9, fontWeight:700, letterSpacing:0.8, border:`1px solid ${s2.c}44`, boxShadow:`0 0 5px ${s2.c}20` }}>{type}</span>;
}
function BCode({ children, style = {} }) {
  return <code style={{ color:C.green, fontSize:11, background:"#00ff8810", padding:"2px 10px", borderRadius:4, border:"1px solid #00ff8830", fontFamily:"monospace", ...style }}>{children}</code>;
}

// ─── Panel 1: Input Section ───────────────────────────────────────────────────
function InputPanel({ form, running, onRun, onChange }) {
  const preview = form.team || form.leader ? buildBranch(form.team || "TEAM", form.leader || "LEADER") : null;
  const canRun  = !running && form.repo && form.team && form.leader;
  return (
    <Panel>
      <PH icon="⌨️" title="Repository Configuration"/>
      <div style={{ padding:"18px 20px" }}>
        <div className="igrid">
          <div>
            <label>GitHub Repository URL</label>
            <input value={form.repo} onChange={e=>onChange("repo",e.target.value)} placeholder="https://github.com/org/repository"/>
          </div>
          <div>
            <label>Team Name</label>
            <input value={form.team} onChange={e=>onChange("team",e.target.value)} placeholder="RIFT ORGANISERS"/>
          </div>
          <div>
            <label>Team Leader Name</label>
            <input value={form.leader} onChange={e=>onChange("leader",e.target.value)} placeholder="Saiyam Kumar"/>
          </div>
          <div className="rbtnw" style={{ display:"flex", alignItems:"flex-end" }}>
            <button className="rbtn" onClick={onRun} disabled={!canRun}>
              {running
                ? <><span style={{ display:"inline-block", animation:"spin 1s linear infinite" }}>⟳</span> RUNNING...</>
                : "▶\u00a0 RUN AGENT"}
            </button>
          </div>
        </div>
        {preview && (
          <div style={{ marginTop:12, display:"flex", alignItems:"center", gap:8 }}>
            <span style={{ color:C.textDim, fontSize:9, letterSpacing:1.5 }}>BRANCH →</span>
            <BCode>{preview}</BCode>
          </div>
        )}
      </div>
    </Panel>
  );
}

// ─── Panel 2: Run Summary Card ────────────────────────────────────────────────
function SummaryPanel({ result, running, form, failures, fixes, elapsed }) {
  const has    = !!result;
  const color  = has ? (result.final_status === "PASSED" ? C.green : C.red) : C.amber;
  const label  = has ? result.final_status : "RUNNING";
  const repo   = has ? result.repo_url       : form.repo;
  const team   = has ? result.team_name      : form.team;
  const leader = has ? result.leader_name    : form.leader;
  const br     = has ? result.branch_name    : buildBranch(form.team||"TEAM",form.leader||"LEADER");
  const nFail  = has ? result.total_failures : failures.length;
  const nFix   = has ? result.total_fixes    : fixes.filter(f=>f.status==="Fixed").length;
  const time   = has ? result.total_time_display : `${Math.floor(elapsed/60)}m ${elapsed%60}s`;

  return (
    <Panel style={{ border:`1px solid ${color}44` }}>
      <PH icon="📋" title="Run Summary" right={<Badge label={label} color={color} large pulse={!has && running}/>}/>
      <div style={{ padding:"16px 20px 0" }} className="sgrid">
        <div style={s.icard}>
          <div style={{ color:C.textSub, fontSize:9, letterSpacing:2, marginBottom:7, textTransform:"uppercase" }}>🔗 Repository URL</div>
          <div style={{ color:C.accent, fontSize:11, fontFamily:"monospace", fontWeight:700, wordBreak:"break-all", lineHeight:1.5 }}>{repo||"—"}</div>
        </div>
        <div style={s.icard}>
          <div style={{ color:C.textSub, fontSize:9, letterSpacing:2, marginBottom:7, textTransform:"uppercase" }}>👥 Team Details</div>
          <div style={{ marginBottom:5 }}>
            <div style={{ color:C.textDim, fontSize:8, letterSpacing:1, textTransform:"uppercase", marginBottom:2 }}>Team Name</div>
            <div style={{ color:C.text, fontSize:13, fontWeight:700 }}>{team||"—"}</div>
          </div>
          <div>
            <div style={{ color:C.textDim, fontSize:8, letterSpacing:1, textTransform:"uppercase", marginBottom:2 }}>Team Leader</div>
            <div style={{ color:C.text, fontSize:13, fontWeight:700 }}>{leader||"—"}</div>
          </div>
        </div>
        <div style={s.icard}>
          <div style={{ color:C.textSub, fontSize:9, letterSpacing:2, marginBottom:7, textTransform:"uppercase" }}>🌿 Branch Created</div>
          <BCode style={{ fontSize:10, display:"inline-block", wordBreak:"break-all", lineHeight:1.7 }}>{br}</BCode>
          <div style={{ marginTop:6, color:C.textDim, fontSize:8, fontFamily:"monospace" }}>TEAM_LEADER_AI_Fix format</div>
        </div>
      </div>
      <div style={{ padding:"12px 20px 18px" }} className="sgrid">
        {[
          { icon:"🐛", label:"Failures Detected", val:nFail, color:C.red,   bg:"#ff3b5c" },
          { icon:"🔧", label:"Fixes Applied",     val:nFix,  color:C.green, bg:"#00ff88" },
          { icon:"⏱",  label:"Total Time Taken",  val:time,  color:C.accent,bg:"#00d4ff" },
        ].map(({ icon, label: lbl, val, color: c, bg }) => (
          <div key={lbl} style={{ background:`${bg}0c`, border:`1px solid ${bg}33`, borderRadius:8, padding:"15px 16px", display:"flex", alignItems:"center", gap:13 }}>
            <div style={{ width:42, height:42, borderRadius:9, background:`${bg}18`, border:`1px solid ${bg}44`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:19, flexShrink:0 }}>{icon}</div>
            <div>
              <div style={{ color:C.textSub, fontSize:8, letterSpacing:2, textTransform:"uppercase", marginBottom:3 }}>{lbl}</div>
              <div style={{ color:c, fontFamily:"'Bebas Neue',sans-serif", fontSize:30, letterSpacing:1, lineHeight:1 }}>{val}</div>
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

// ─── Panel 3: Score Breakdown ─────────────────────────────────────────────────
function ScorePanel({ result }) {
  const sc    = result.score;
  const el    = result.total_time_seconds || 0;
  const pen   = sc.efficiency_penalty || 0;
  const tc    = sc.total >= 100 ? C.green : sc.total >= 80 ? C.amber : C.red;
  const bPct  = (100/110)*100;
  const bnPct = (sc.speed_bonus/110)*100;

  function Bar({ label, sub, pct, display, color, active = true }) {
    return (
      <div style={{ marginBottom:18 }}>
        <div style={{ display:"flex", justifyContent:"space-between", alignItems:"flex-start", marginBottom:7 }}>
          <div>
            <div style={{ color:active?C.text:C.textSub, fontSize:13, fontFamily:"monospace", fontWeight:700 }}>{label}</div>
            {sub && <div style={{ color:C.textDim, fontSize:10, marginTop:2 }}>{sub}</div>}
          </div>
          <div style={{ color:active?color:C.textDim, fontFamily:"'Bebas Neue',sans-serif", fontSize:26, letterSpacing:1, lineHeight:1 }}>{display}</div>
        </div>
        <div style={{ height:9, background:C.border, borderRadius:5, overflow:"hidden" }}>
          <div style={{ height:"100%", width:active?`${Math.max(0,Math.min(100,pct))}%`:"0%", background:`linear-gradient(90deg,${color}88,${color})`, borderRadius:5, boxShadow:`0 0 8px ${color}60`, transition:"width 1.2s ease" }}/>
        </div>
      </div>
    );
  }

  return (
    <Panel>
      <PH icon="🏆" title="Score Breakdown"
        right={
          <div style={{ display:"flex", alignItems:"baseline", gap:5 }}>
            <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:42, color:tc, letterSpacing:2, textShadow:`0 0 24px ${tc}60` }}>{sc.total}</span>
            <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:20, color:C.textDim }}>/ 110</span>
          </div>
        }
      />
      <div className="scgrid" style={{ padding:"20px 22px" }}>
        <div>
          <Bar label="Base Score"         sub="Starting score for all submissions" pct={bPct}  display="+100"                              color={C.accent}/>
          <Bar label="Speed Bonus"        sub={`+10 if under 5 min · Actual: ${Math.floor(el/60)}m ${Math.floor(el%60)}s`} pct={bnPct} display={sc.speed_bonus>0?"+10":"+0"} color={C.green}  active={sc.speed_bonus>0}/>
          <Bar label="Efficiency Penalty" sub={`−2 per commit over 20 · ${result.commit_count} commits`} pct={0} display={`−${pen}`} color={C.red} active={pen>0}/>
          <div style={{ borderTop:`1px solid ${C.borderHi}`, paddingTop:14, marginTop:4, display:"flex", justifyContent:"space-between", alignItems:"center" }}>
            <div>
              <div style={{ color:C.textSub, fontSize:9, letterSpacing:2, textTransform:"uppercase" }}>Final Total Score</div>
              <div style={{ color:C.textDim, fontSize:10, marginTop:2 }}>100 + {sc.speed_bonus} − {pen} = {sc.total}</div>
            </div>
            <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:40, color:tc, textShadow:`0 0 18px ${tc}50` }}>{sc.total}</span>
          </div>
        </div>

        {/* Right: visual chart */}
        <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
          {/* Stacked bar */}
          <div>
            <div style={{ color:C.textSub, fontSize:9, letterSpacing:2, textTransform:"uppercase", marginBottom:9 }}>Score Composition</div>
            <div style={{ height:26, background:C.border, borderRadius:6, overflow:"hidden", display:"flex" }}>
              <div style={{ width:`${bPct}%`, background:`linear-gradient(90deg,#004466,${C.accent})`, display:"flex", alignItems:"center", justifyContent:"center", overflow:"hidden" }}>
                <span style={{ color:"#fff", fontSize:9, fontFamily:"monospace", fontWeight:700, whiteSpace:"nowrap" }}>BASE 100</span>
              </div>
              <div style={{ width:`${bnPct}%`, background:`linear-gradient(90deg,${C.greenDim},${C.green})`, display:"flex", alignItems:"center", justifyContent:"center", overflow:"hidden", transition:"width 1.2s ease .2s" }}>
                {sc.speed_bonus > 0 && <span style={{ color:"#fff", fontSize:9, fontFamily:"monospace", fontWeight:700 }}>+10</span>}
              </div>
            </div>
            <div style={{ display:"flex", gap:14, marginTop:9, flexWrap:"wrap" }}>
              {[{l:"Base (100)",c:C.accent},{l:"Speed Bonus",c:C.green}].map(({ l, c }) => (
                <div key={l} style={{ display:"flex", alignItems:"center", gap:5, fontSize:10, color:C.textSub }}>
                  <div style={{ width:9, height:9, borderRadius:2, background:c, boxShadow:`0 0 4px ${c}` }}/>{l}
                </div>
              ))}
            </div>
          </div>
          {/* Circular gauge */}
          <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:10 }}>
            <div style={{ position:"relative", width:150, height:150 }}>
              <svg viewBox="0 0 36 36" style={{ width:"100%", height:"100%", transform:"rotate(-90deg)" }}>
                <circle cx="18" cy="18" r="15.9" fill="none" stroke={C.border} strokeWidth="3"/>
                <circle cx="18" cy="18" r="15.9" fill="none" stroke={C.accent} strokeWidth="3"
                  strokeDasharray={`${bPct} 100`} strokeLinecap="butt" style={{ filter:`drop-shadow(0 0 2px ${C.accent})` }}/>
                {sc.speed_bonus > 0 && (
                  <circle cx="18" cy="18" r="15.9" fill="none" stroke={C.green} strokeWidth="3"
                    strokeDasharray={`${bnPct} 100`} strokeDashoffset={`${-bPct}`}
                    strokeLinecap="butt" style={{ filter:`drop-shadow(0 0 2px ${C.green})` }}/>
                )}
              </svg>
              <div style={{ position:"absolute", inset:0, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center" }}>
                <div style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:32, color:tc, lineHeight:1, textShadow:`0 0 14px ${tc}` }}>{sc.total}</div>
                <div style={{ fontSize:8, color:C.textSub, letterSpacing:2 }}>POINTS</div>
              </div>
            </div>
            <div style={{ display:"flex", gap:8, justifyContent:"center" }}>
              {[{l:"Base",v:"100",c:C.accent},{l:"Bonus",v:`+${sc.speed_bonus}`,c:C.green},{l:"Penalty",v:`−${pen}`,c:pen>0?C.red:C.textDim}].map(({ l, v, c }) => (
                <div key={l} style={{ background:`${c}10`, border:`1px solid ${c}33`, borderRadius:5, padding:"4px 10px", textAlign:"center" }}>
                  <div style={{ color:C.textDim, fontSize:7, letterSpacing:1, textTransform:"uppercase" }}>{l}</div>
                  <div style={{ color:c, fontFamily:"'Bebas Neue',sans-serif", fontSize:17, letterSpacing:1 }}>{v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </Panel>
  );
}

// ─── Panel 4: Fixes Table ─────────────────────────────────────────────────────
function FixesTab({ fixes, activeFilter, onFilter }) {
  const shown  = activeFilter === "ALL" ? fixes : fixes.filter(f => f.bug_type === activeFilter);
  const fixed  = fixes.filter(f => f.status === "Fixed").length;
  const rate   = fixes.length > 0 ? Math.round(fixed / fixes.length * 100) : 0;

  return (
    <div>
      {/* Stats bar */}
      {fixes.length > 0 && (
        <div style={{ padding:"11px 18px", borderBottom:`1px solid ${C.border}`, background:C.surface, display:"flex", alignItems:"center", gap:20, flexWrap:"wrap" }}>
          <div style={{ display:"flex", alignItems:"center", gap:14 }}>
            {[{icon:"✓",lbl:"FIXED",val:fixed,c:C.green},{icon:"✗",lbl:"FAILED",val:fixes.length-fixed,c:C.red}].map(({ icon, lbl, val, c }) => (
              <div key={lbl} style={{ display:"flex", alignItems:"center", gap:6 }}>
                <span style={{ color:c, fontSize:15, fontWeight:700 }}>{icon}</span>
                <div>
                  <div style={{ color:c, fontFamily:"'Bebas Neue',sans-serif", fontSize:20, lineHeight:1 }}>{val}</div>
                  <div style={{ color:C.textDim, fontSize:8, letterSpacing:1 }}>{lbl}</div>
                </div>
              </div>
            ))}
          </div>
          <div style={{ flex:1, minWidth:120 }}>
            <div style={{ display:"flex", justifyContent:"space-between", marginBottom:4 }}>
              <span style={{ color:C.textDim, fontSize:9, letterSpacing:1 }}>SUCCESS RATE</span>
              <span style={{ color:rate===100?C.green:C.amber, fontSize:9, fontFamily:"monospace", fontWeight:700 }}>{rate}%</span>
            </div>
            <div style={{ height:5, background:C.border, borderRadius:3, overflow:"hidden" }}>
              <div style={{ height:"100%", width:`${rate}%`, background:rate===100?`linear-gradient(90deg,${C.greenDim},${C.green})`:`linear-gradient(90deg,${C.amberDim},${C.amber})`, transition:"width 1s ease" }}/>
            </div>
          </div>
          <span style={{ color:C.textDim, fontSize:10, fontFamily:"monospace" }}>{fixes.length} total</span>
        </div>
      )}

      {/* Filter row — all 6 bug types */}
      <div style={{ padding:"9px 18px", borderBottom:`1px solid ${C.border}`, display:"flex", gap:5, flexWrap:"wrap", background:"#050b14" }}>
        {BUG_TYPES.map(bt => {
          const bs = BUG_STYLE[bt];
          const cnt = bt === "ALL" ? fixes.length : fixes.filter(f => f.bug_type === bt).length;
          const on  = activeFilter === bt;
          return (
            <button key={bt} onClick={() => onFilter(bt)} style={{
              background: on ? (bs ? bs.bg : C.surface) : "transparent",
              border: `1px solid ${on ? (bs?bs.c:C.accent) : C.border}`,
              color:  on ? (bs ? bs.c : C.accent) : C.textDim,
              padding:"3px 10px", borderRadius:4, fontSize:10,
              fontFamily:"monospace", fontWeight:700, cursor:"pointer",
              display:"flex", alignItems:"center", gap:5, transition:"all .15s",
            }}>
              {bt}
              {cnt > 0 && <span style={{ background:on?`${bs?bs.c:C.accent}28`:C.border, color:on?(bs?bs.c:C.accent):C.textDim, borderRadius:8, padding:"0 5px", fontSize:9 }}>{cnt}</span>}
            </button>
          );
        })}
      </div>

      {/* Table */}
      {fixes.length === 0
        ? <div style={{ padding:34, textAlign:"center", color:C.textDim, fontSize:12, fontFamily:"monospace" }}>Fixes will appear as the agent runs...</div>
        : shown.length === 0
          ? <div style={{ padding:22, textAlign:"center", color:C.textDim, fontSize:12, fontFamily:"monospace" }}>No {activeFilter} fixes found.</div>
          : (
            <div style={{ overflowX:"auto" }}>
              <table style={{ width:"100%", borderCollapse:"collapse", fontFamily:"monospace", fontSize:12 }}>
                <thead>
                  <tr style={{ background:"#04080f", borderBottom:`2px solid ${C.border}` }}>
                    {[["File","22%"],["Bug Type","13%"],["Line #","8%"],["Commit Message","42%"],["Status","15%"]].map(([l,w]) => (
                      <th key={l} style={{ padding:"10px 15px", textAlign:"left", color:C.textSub, fontSize:9, letterSpacing:2, textTransform:"uppercase", fontWeight:700, width:w }}>{l}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {shown.map((fix, i) => {
                    const ok  = fix.status === "Fixed";
                    const bs  = BUG_STYLE[fix.bug_type] || { c:C.accent, bg:"#1a2540" };
                    const pp  = fix.file.includes("/") ? fix.file.substring(0, fix.file.lastIndexOf("/")+1) : "";
                    const fp  = fix.file.includes("/") ? fix.file.substring(fix.file.lastIndexOf("/")+1) : fix.file;
                    return (
                      <tr key={i} style={{ borderBottom:`1px solid ${C.border}`, background:ok?"#00ff8804":"#ff3b5c04", borderLeft:`3px solid ${ok?C.green:C.red}` }}>
                        <td style={{ padding:"10px 15px" }}><span style={{ color:C.textDim, fontSize:10 }}>{pp}</span><span style={{ color:C.text }}>{fp}</span></td>
                        <td style={{ padding:"10px 15px" }}><BugBadge type={fix.bug_type}/></td>
                        <td style={{ padding:"10px 15px" }}><span style={{ color:C.amber, fontFamily:"monospace", fontSize:12, fontWeight:700 }}>:{fix.line}</span></td>
                        <td style={{ padding:"10px 15px", maxWidth:0 }}>
                          <div style={{ overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
                            <span style={{ color:C.green, fontSize:10 }}>[AI-AGENT] </span>
                            <span style={{ color:C.textSub, fontSize:11 }}>{fix.commit_message.replace("[AI-AGENT] ","")}</span>
                          </div>
                        </td>
                        <td style={{ padding:"10px 15px" }}>
                          <span style={{ display:"inline-flex", alignItems:"center", gap:5, background:ok?"#00ff8815":"#ff3b5c15", border:`1px solid ${ok?"#00ff8844":"#ff3b5c44"}`, color:ok?C.green:C.red, padding:"3px 10px", borderRadius:4, fontSize:11, fontWeight:700, boxShadow:`0 0 7px ${ok?"#00ff8820":"#ff3b5c20"}` }}>
                            {ok?"✓":"✗"} {ok?"Fixed":"Failed"}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
      }
    </div>
  );
}

// ─── Panel 5: CI/CD Status Timeline ──────────────────────────────────────────
function CITimeline({ ciRuns, maxIter }) {
  const last = ciRuns[ciRuns.length - 1];
  return (
    <div>
      {/* Summary bar: "3/5" counter + dot track + final badge */}
      {ciRuns.length > 0 && (
        <div style={{ padding:"11px 20px", borderBottom:`1px solid ${C.border}`, background:C.surface, display:"flex", alignItems:"center", gap:16, flexWrap:"wrap" }}>
          {/* X/Y iterations counter */}
          <div style={{ display:"flex", alignItems:"center", gap:7, flexShrink:0 }}>
            <span style={{ color:C.textDim, fontSize:9, letterSpacing:2, textTransform:"uppercase" }}>Iterations</span>
            <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:26, color:C.amber, lineHeight:1 }}>{ciRuns.length}</span>
            <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:16, color:C.textDim }}>/ {maxIter}</span>
          </div>
          <div style={{ width:1, height:28, background:C.border }}/>
          {/* Dot track showing all iteration slots */}
          <div style={{ display:"flex", alignItems:"center", gap:5 }}>
            {Array.from({ length:maxIter }).map((_,i) => {
              const run = ciRuns[i];
              const dc  = !run ? C.border : run.status==="PASSED" ? C.green : C.red;
              return (
                <div key={i} style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:2 }}>
                  <div style={{ width:18, height:18, borderRadius:"50%", background:run?dc:"transparent", border:`2px solid ${dc}`, boxShadow:run?`0 0 7px ${dc}`:"none", display:"flex", alignItems:"center", justifyContent:"center", fontSize:8, color:"#fff", fontWeight:700 }}>
                    {run ? (run.status==="PASSED" ? "✓" : "✗") : ""}
                  </div>
                  <span style={{ color:C.textDim, fontSize:7, fontFamily:"monospace" }}>#{i+1}</span>
                </div>
              );
            })}
          </div>
          {/* Final result badge */}
          {last && (
            <div style={{ display:"flex", alignItems:"center", gap:8, marginLeft:"auto" }}>
              <span style={{ color:C.textDim, fontSize:9, letterSpacing:2, textTransform:"uppercase" }}>Final</span>
              <Badge label={last.status} color={last.status==="PASSED"?C.green:C.red} large/>
            </div>
          )}
        </div>
      )}

      {/* Timeline entries */}
      <div style={{ padding:"18px 22px" }}>
        {ciRuns.length === 0
          ? <div style={{ textAlign:"center", color:C.textDim, fontSize:12, fontFamily:"monospace", padding:"26px 0" }}>CI/CD runs will appear here as the agent iterates...</div>
          : (
            <div style={{ position:"relative" }}>
              {ciRuns.length > 1 && (
                <div style={{ position:"absolute", left:21, top:22, width:2, height:"calc(100% - 44px)", background:`linear-gradient(to bottom,${C.accent}80,${last?.status==="PASSED"?C.green:C.red}80)` }}/>
              )}
              {ciRuns.map((run, i) => {
                const ok  = run.status === "PASSED";
                const col = ok ? C.green : C.red;
                const ts  = new Date(run.timestamp);
                const tot = run.passed + run.failed;
                const pct = tot > 0 ? Math.round(run.passed/tot*100) : 0;
                const isLast = i === ciRuns.length - 1;
                return (
                  <div key={i} style={{ display:"flex", gap:16, marginBottom:i<ciRuns.length-1?22:0, alignItems:"flex-start" }}>
                    {/* Circle node */}
                    <div style={{ width:44, height:44, borderRadius:"50%", flexShrink:0, zIndex:1, background:ok?C.greenDim:C.redDim, border:`2.5px solid ${col}`, display:"flex", alignItems:"center", justifyContent:"center", fontSize:18, fontWeight:700, color:col, boxShadow:`0 0 18px ${col}50` }}>
                      {ok?"✓":"✗"}
                    </div>
                    {/* Run card */}
                    <div style={{ flex:1, background:ok?"#00ff8806":"#ff3b5c06", border:`1px solid ${ok?"#00ff8833":"#ff3b5c33"}`, borderRadius:10, overflow:"hidden", boxShadow:isLast?`0 0 18px ${ok?"#00ff8818":"#ff3b5c18"}`:"none" }}>
                      <div style={{ padding:"11px 15px", borderBottom:`1px solid ${ok?"#00ff8822":"#ff3b5c22"}`, background:ok?"#00ff8808":"#ff3b5c08", display:"flex", justifyContent:"space-between", alignItems:"center" }}>
                        <div style={{ display:"flex", alignItems:"center", gap:10, flexWrap:"wrap" }}>
                          <span style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:19, color:col, letterSpacing:1 }}>RUN #{run.iteration}</span>
                          {/* Pass/fail badge per iteration */}
                          <span style={{ display:"inline-flex", alignItems:"center", gap:6, background:`${col}18`, border:`1.5px solid ${col}`, borderRadius:6, fontFamily:"monospace", fontWeight:700, letterSpacing:1.5, padding:"3px 10px", fontSize:10, boxShadow:`0 0 10px ${col}28`, color:col }}>
                            <span style={{ width:6, height:6, borderRadius:"50%", background:col, boxShadow:`0 0 5px ${col}` }}/>
                            {run.status}
                          </span>
                          {/* "X/Y" label on each card */}
                          <span style={{ color:C.textDim, fontSize:9, fontFamily:"monospace", background:C.surface, padding:"2px 8px", borderRadius:4, border:`1px solid ${C.border}` }}>
                            {run.iteration}/{maxIter}
                          </span>
                        </div>
                        {/* Timestamp */}
                        <div style={{ textAlign:"right", flexShrink:0 }}>
                          <div style={{ color:C.text, fontSize:12, fontFamily:"monospace", fontWeight:700 }}>{ts.toLocaleTimeString([],{hour:"2-digit",minute:"2-digit",second:"2-digit"})}</div>
                          <div style={{ color:C.textDim, fontSize:9, fontFamily:"monospace" }}>{ts.toLocaleDateString([],{month:"short",day:"numeric"})}</div>
                        </div>
                      </div>
                      <div style={{ padding:"11px 15px" }}>
                        <div style={{ display:"flex", gap:18, alignItems:"center", marginBottom:10, flexWrap:"wrap" }}>
                          <span style={{ color:C.green, fontSize:12, fontFamily:"monospace" }}>✓ {run.passed} passed</span>
                          <span style={{ color:C.red,   fontSize:12, fontFamily:"monospace" }}>✗ {run.failed} failed</span>
                          <div style={{ flex:1, minWidth:80 }}>
                            <div style={{ height:5, background:C.border, borderRadius:3, overflow:"hidden" }}>
                              <div style={{ height:"100%", width:`${pct}%`, background:ok?`linear-gradient(90deg,${C.greenDim},${C.green})`:`linear-gradient(90deg,${C.redDim},${C.red})`, transition:"width 1s ease" }}/>
                            </div>
                          </div>
                          <span style={{ color:col, fontSize:10, fontFamily:"monospace", fontWeight:700 }}>{pct}%</span>
                        </div>
                        <pre style={{ background:"#01030a", border:`1px solid ${C.border}`, borderRadius:5, padding:"9px 11px", color:C.textSub, fontSize:10, fontFamily:"monospace", margin:0, lineHeight:1.7, whiteSpace:"pre-wrap" }}>{run.output}</pre>
                        {isLast && (
                          <div style={{ marginTop:9, display:"flex", justifyContent:"flex-end" }}>
                            <span style={{ background:`${col}14`, border:`1px solid ${col}33`, color:col, fontSize:9, fontFamily:"monospace", letterSpacing:1.5, padding:"3px 9px", borderRadius:4 }}>← FINAL RESULT</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )
        }
      </div>
    </div>
  );
}

// ─── Terminal ─────────────────────────────────────────────────────────────────
function Terminal({ logs }) {
  const ref = useRef();
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [logs]);
  return (
    <div ref={ref} style={{ padding:"14px 16px", fontFamily:"monospace", fontSize:11, lineHeight:1.8, overflowY:"auto", height:260, background:"#01030a" }}>
      {logs.length === 0 && <span style={{ color:C.textDim }}>Waiting for agent to start...</span>}
      {logs.map((l, i) => (
        <div key={i} style={{ display:"flex", gap:10, marginBottom:1 }}>
          <span style={{ color:PHASE_COLORS[l.phase]||C.textSub, minWidth:96, opacity:.9, flexShrink:0 }}>[{l.phase}]</span>
          <span style={{ color:i===logs.length-1?C.text:C.textSub }}>{l.msg}</span>
        </div>
      ))}
      {logs.length > 0 && <span style={{ color:C.accent, animation:"blink 1s infinite" }}>█</span>}
    </div>
  );
}

// ─── Issues Tab ───────────────────────────────────────────────────────────────
function IssuesTab({ failures }) {
  if (!failures.length) return <div style={{ padding:28, textAlign:"center", color:C.textDim, fontSize:12 }}>No issues detected yet...</div>;
  return (
    <div style={{ padding:16 }}>
      {failures.map((f, i) => {
        const bs = BUG_STYLE[f.bug_type] || { c:C.accent, bg:"#1a2540" };
        return (
          <div key={i} style={{ background:C.surface, border:`1px solid ${C.border}`, borderLeft:`3px solid ${C.red}`, borderRadius:6, padding:"10px 14px", marginBottom:8 }}>
            <div style={{ display:"flex", justifyContent:"space-between", alignItems:"center", marginBottom:4 }}>
              <code style={{ color:C.amber, fontSize:11 }}>{f.file}:{f.line}</code>
              <span style={{ background:bs.bg, color:bs.c, fontSize:9, padding:"2px 8px", borderRadius:3, fontWeight:700, border:`1px solid ${bs.c}44` }}>{f.bug_type}</span>
            </div>
            <div style={{ color:C.text, fontSize:12, marginBottom:5 }}>{f.description}</div>
            <code style={{ color:C.textSub, fontSize:10 }}>{f.dashboard_output}</code>
          </div>
        );
      })}
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const { state, actions } = useAgent();
  const { form, running, elapsed, logs, failures, fixes, ciRuns, result, activeTab, activeFilter, maxIterations } = state;

  const cancelRef = useRef(null);
  const timerRef  = useRef(null);

  // Elapsed timer
  useEffect(() => {
    if (running) { timerRef.current = setInterval(() => actions.tick(), 1000); }
    else         { clearInterval(timerRef.current); }
    return () => clearInterval(timerRef.current);
  }, [running]);

  const handleRun = useCallback(() => {
    if (!form.repo || !form.team || !form.leader) return;
    if (cancelRef.current) cancelRef.current();
    actions.start();
    cancelRef.current = simulateAgentRun(form.repo, form.team, form.leader, maxIterations, ev => {
      if (ev.type === "log")      actions.addLog({ phase:ev.phase, msg:ev.msg });
      if (ev.type === "failure")  actions.addFailure(ev.failure);
      if (ev.type === "fixes")    actions.setFixes(ev.fixes);
      if (ev.type === "cirun")    actions.addCiRun(ev.run);
      if (ev.type === "complete") actions.complete(ev.result);
    });
  }, [form, maxIterations, actions]);

  const TABS = [
    { id:"terminal", label:"⬛ Terminal" },
    { id:"issues",   label:`🔍 Issues${failures.length>0?` (${failures.length})`:""}` },
    { id:"fixes",    label:`🔧 Fixes${fixes.length>0?` (${fixes.length})`:""}` },
    { id:"pipeline", label:`🔄 CI/CD${ciRuns.length>0?` (${ciRuns.length})`:""}` },
  ];

  const hasRun = running || !!result || logs.length > 0;

  return (
    <div style={{ minHeight:"100vh", background:C.bg, color:C.text, fontFamily:"'Space Mono','Courier New',monospace" }}>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Bebas+Neue&display=swap');
        *{box-sizing:border-box;margin:0;padding:0}
        ::-webkit-scrollbar{width:5px;height:5px}
        ::-webkit-scrollbar-track{background:#04060c}
        ::-webkit-scrollbar-thumb{background:#1a2540;border-radius:3px}
        @keyframes fadeIn{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:translateY(0)}}
        @keyframes blink{0%,100%{opacity:1}50%{opacity:0}}
        @keyframes pulse{0%,100%{opacity:1}50%{opacity:.35}}
        @keyframes spin{from{transform:rotate(0deg)}to{transform:rotate(360deg)}}
        label{color:#6b7fa8;font-size:9px;letter-spacing:2px;text-transform:uppercase;display:block;margin-bottom:6px}
        input{width:100%;background:#080d18;border:1px solid #1a2540;border-radius:6px;padding:10px 12px;color:#e8f0fe;font-size:12px;font-family:monospace;transition:border-color .2s,box-shadow .2s;outline:none}
        input:focus{border-color:#00d4ff;box-shadow:0 0 0 2px #00d4ff20}
        input::placeholder{color:#2d3f5e}
        .rbtn{background:transparent;border:1.5px solid #00d4ff;color:#00d4ff;padding:10px 20px;border-radius:6px;font-size:12px;font-family:monospace;font-weight:700;cursor:pointer;letter-spacing:1px;white-space:nowrap;transition:all .2s;display:flex;align-items:center;gap:7px;width:100%}
        .rbtn:hover:not(:disabled){background:#00d4ff;color:#04060c}
        .rbtn:disabled{opacity:.45;cursor:not-allowed}
        .igrid{display:grid;grid-template-columns:2fr 1fr 1fr auto;gap:12px;align-items:end}
        .sgrid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:13px}
        .scgrid{display:grid;grid-template-columns:1fr 1fr;gap:26px}
        @media(max-width:900px){
          .igrid{grid-template-columns:1fr 1fr}
          .igrid>*:first-child{grid-column:1/-1}
          .igrid>.rbtnw{grid-column:1/-1}
          .sgrid{grid-template-columns:1fr 1fr}
          .scgrid{grid-template-columns:1fr}
        }
        @media(max-width:600px){
          .igrid,.sgrid,.scgrid{grid-template-columns:1fr}
        }
      `}</style>

      <div style={{ maxWidth:1300, margin:"0 auto", padding:"0 18px 60px" }}>

        {/* Header */}
        <div style={{ padding:"26px 0 22px", borderBottom:`1px solid ${C.border}`, marginBottom:20, display:"flex", justifyContent:"space-between", alignItems:"flex-end", flexWrap:"wrap", gap:12 }}>
          <div>
            <div style={{ display:"flex", alignItems:"center", gap:11, marginBottom:4 }}>
              <div style={{ width:34, height:34, background:"linear-gradient(135deg,#00d4ff,#0055ff)", borderRadius:8, display:"flex", alignItems:"center", justifyContent:"center", fontSize:17, boxShadow:"0 0 18px #00d4ff50", flexShrink:0 }}>⚡</div>
              <h1 style={{ fontFamily:"'Bebas Neue',sans-serif", fontSize:34, letterSpacing:3, color:C.text, lineHeight:1 }}>CI/CD HEALING AGENT</h1>
            </div>
            <div style={{ color:C.textSub, fontSize:10, letterSpacing:2, marginLeft:45 }}>AUTONOMOUS DEVOPS • RIFT 2026 HACKATHON</div>
          </div>
          <div style={{ textAlign:"right" }}>
            <div style={{ display:"flex", alignItems:"center", gap:7, justifyContent:"flex-end", marginBottom:4 }}>
              <div style={{ width:8, height:8, borderRadius:"50%", background:running?C.amber:C.green, boxShadow:`0 0 7px ${running?C.amber:C.green}`, animation:running?"pulse 1s infinite":"none" }}/>
              <span style={{ fontSize:10, color:running?C.amber:C.green, letterSpacing:1 }}>{running?"AGENT RUNNING":"STANDBY"}</span>
            </div>
            {running && <div style={{ color:C.textDim, fontSize:10 }}>Elapsed: {Math.floor(elapsed/60)}m {elapsed%60}s</div>}
          </div>
        </div>

        {/* Panel 1: Input */}
        <InputPanel form={form} running={running} onRun={handleRun} onChange={(k,v) => actions.setForm({ [k]:v })}/>

        {/* Panel 2: Run Summary */}
        {hasRun && <SummaryPanel result={result} running={running} form={form} failures={failures} fixes={fixes} elapsed={elapsed}/>}

        {/* Panel 3: Score */}
        {result && result.score && <ScorePanel result={result}/>}

        {/* Panels 4+5: Tabbed */}
        {hasRun && (
          <Panel>
            <div style={{ display:"flex", borderBottom:`1px solid ${C.border}`, background:C.surface, overflowX:"auto" }}>
              {TABS.map(tab => (
                <button key={tab.id} onClick={() => actions.setTab(tab.id)} style={{
                  padding:"11px 18px", background:"transparent", border:"none",
                  borderBottom:`2px solid ${activeTab===tab.id?C.accent:"transparent"}`,
                  color:activeTab===tab.id?C.text:C.textSub,
                  fontSize:10, cursor:"pointer", fontFamily:"monospace", letterSpacing:1,
                  transition:"all .15s", display:"flex", gap:5, alignItems:"center", whiteSpace:"nowrap",
                }}>{tab.label}</button>
              ))}
            </div>
            {activeTab === "terminal" && <Terminal logs={logs}/>}
            {activeTab === "issues"   && <IssuesTab failures={failures}/>}
            {activeTab === "fixes"    && <FixesTab fixes={fixes} activeFilter={activeFilter} onFilter={actions.setFilter}/>}
            {activeTab === "pipeline" && <CITimeline ciRuns={ciRuns} maxIter={maxIterations}/>}
          </Panel>
        )}

        {/* Empty state */}
        {!hasRun && (
          <div style={{ textAlign:"center", padding:"54px 20px", color:C.textDim }}>
            <div style={{ fontSize:42, marginBottom:14, opacity:.22 }}>⚡</div>
            <div style={{ fontSize:12, letterSpacing:2, marginBottom:8 }}>AUTONOMOUS CI/CD HEALING AGENT</div>
            <div style={{ fontSize:11, maxWidth:380, margin:"0 auto", lineHeight:1.9 }}>
              Enter a GitHub repository URL, team name, and leader name above.<br/>
              The agent will autonomously clone, analyze, fix, and verify your code.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
