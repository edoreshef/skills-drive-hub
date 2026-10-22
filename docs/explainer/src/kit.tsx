import React, {createContext, useContext} from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/google-fonts/IBMPlexSans';
import {loadFont as loadMono} from '@remotion/google-fonts/IBMPlexMono';
import timings from './timings.json';

export const {fontFamily: SANS} = loadFont('normal', {weights: ['400', '500', '600'], subsets: ['latin']});
export const {fontFamily: MONO} = loadMono('normal', {weights: ['400', '500'], subsets: ['latin']});

// Engineering graph paper: cool paper, graphite ink, one working blue, and
// green / amber / red only where they mean pass / warn / block.
export const C = {
  paper: '#F3F5F9',
  sheet: '#FFFFFF',
  grid: '#D6DEEC',
  ink: '#1B2430',
  ink2: '#4B5668',
  ink3: '#8A94A6',
  rule: '#C3CBD9',
  blue: '#2457D6',
  blueSoft: '#E3EAFB',
  green: '#1E8E4E',
  greenSoft: '#E1F3E8',
  amber: '#C98A0B',
  amberSoft: '#FBF0D5',
  red: '#C63B3B',
  redSoft: '#FAE3E3',
  violet: '#6B5BD2',
  violetSoft: '#EBE8FA',
};

// ---------- timing ----------

export const FPS = 30;
export const LEAD = 12;
export const TAIL = 18;
export type SceneId = keyof typeof timings;

export const sceneFrames = (id: SceneId, tail = TAIL) => LEAD + Math.ceil(timings[id].duration * FPS) + tail;

const SceneCtx = createContext<SceneId>('intro');
export const SceneProvider: React.FC<{id: SceneId; children: React.ReactNode}> = ({id, children}) => (
  <SceneCtx.Provider value={id}>{children}</SceneCtx.Provider>
);
export const useSceneId = () => useContext(SceneCtx);

const norm = (w: string) => w.toLowerCase().replace(/[^a-z0-9]/g, '');

/** at(phrase) → scene-relative frame where that phrase is spoken. */
export const useAt = () => {
  const id = useContext(SceneCtx);
  const words = timings[id].words;
  return (phrase: string, offset = 0) => {
    const target = phrase.split(/\s+/).map(norm).filter(Boolean);
    for (let i = 0; i + target.length <= words.length; i++) {
      if (target.every((t, k) => norm(words[i + k].w) === t)) return LEAD + Math.round(words[i].s * FPS) + offset;
    }
    throw new Error(`phrase not found in ${id}: "${phrase}"`);
  };
};

/** 0→1 eased progress starting at `at`, over `dur` frames. */
export const useReveal = (at: number, dur = 16) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - at, fps, config: {damping: 200}, durationInFrames: dur});
};

export const useAfter = (at: number) => useCurrentFrame() >= at;

// ---------- motion ----------

type Box = {x: number; y: number; w?: number; h?: number};

/** Fades in and rises 14px. The default entrance for everything. */
export const Rise: React.FC<{at: number; children: React.ReactNode; style?: React.CSSProperties; dur?: number} & Box> = ({at, children, style, x, y, w, h, dur = 16}) => {
  const p = useReveal(at, dur);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, opacity: p, transform: `translateY(${(1 - p) * 14}px)`, ...style}}>
      {children}
    </div>
  );
};

/** Fades out from `at`. */
export const Fade: React.FC<{at: number; children: React.ReactNode; dur?: number}> = ({at, children, dur = 10}) => {
  const frame = useCurrentFrame();
  const o = interpolate(frame, [at, at + dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (o <= 0) return null;
  return <div style={{position: 'absolute', inset: 0, opacity: o}}>{children}</div>;
};

/** Clips its content to a growing width: a line "drawing" itself. */
export const Wipe: React.FC<{at: number; children: React.ReactNode; dur?: number; style?: React.CSSProperties}> = ({at, children, dur = 14, style}) => {
  const p = useReveal(at, dur);
  return <div style={{clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`, ...style}}>{children}</div>;
};

/** Marker underline sweeping under a phrase. */
export const Mark: React.FC<{at: number; children: React.ReactNode; color?: string}> = ({at, children, color = C.blue}) => {
  const p = useReveal(at, 12);
  return (
    <span style={{position: 'relative', display: 'inline-block'}}>
      <span style={{position: 'absolute', left: -2, right: -2, bottom: 2, height: '0.38em', background: color, opacity: 0.22, transform: `scaleX(${p})`, transformOrigin: 'left'}} />
      <span style={{position: 'relative'}}>{children}</span>
    </span>
  );
};

/** Counts characters in: typing. */
export const Typed: React.FC<{at: number; text: string; cps?: number; style?: React.CSSProperties; cursor?: boolean}> = ({at, text, cps = 40, style, cursor = true}) => {
  const frame = useCurrentFrame();
  if (frame < at) return null;
  const n = Math.min(text.length, Math.floor(((frame - at) / FPS) * cps));
  const done = n >= text.length;
  return <span style={{whiteSpace: 'pre', ...style}}>{text.slice(0, n)}{cursor && !done ? '▏' : ''}</span>;
};

/** Moves a child along a straight path between frames a and b. */
export const Travel: React.FC<{a: number; b: number; x1: number; y1: number; x2: number; y2: number; children: React.ReactNode; hideAfter?: boolean}> = ({a, b, x1, y1, x2, y2, children, hideAfter = false}) => {
  const frame = useCurrentFrame();
  if (frame < a || (hideAfter && frame > b)) return null;
  const t = interpolate(frame, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  return <div style={{position: 'absolute', left: x1 + (x2 - x1) * e, top: y1 + (y2 - y1) * e, transform: 'translate(-50%, -50%)'}}>{children}</div>;
};

/** A connector that draws itself, optionally with a dot at the end. */
export const Line: React.FC<{at: number; points: [number, number][]; color?: string; width?: number; dur?: number; dashed?: boolean; arrow?: boolean}> = ({at, points, color = C.ink2, width = 3, dur = 16, dashed = false, arrow = false}) => {
  const p = useReveal(at, dur);
  if (p <= 0) return null;
  const d = points.map(([x, y], i) => `${i ? 'L' : 'M'}${x} ${y}`).join(' ');
  let len = 0;
  for (let i = 1; i < points.length; i++) len += Math.hypot(points[i][0] - points[i - 1][0], points[i][1] - points[i - 1][1]);
  const [x2, y2] = points[points.length - 1];
  const [x1, y1] = points[points.length - 2];
  const ang = Math.atan2(y2 - y1, x2 - x1);
  const h = 12;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      <path d={d} fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round"
        strokeDasharray={dashed ? `${len} ${len}` : len} strokeDashoffset={len * (1 - p)} />
      {dashed && <path d={d} fill="none" stroke={color} strokeWidth={width} strokeDasharray="8 10" strokeLinecap="round" opacity={p} />}
      {arrow && p > 0.97 && (
        <path d={`M${x2 - h * Math.cos(ang - 0.55)} ${y2 - h * Math.sin(ang - 0.55)} L${x2} ${y2} L${x2 - h * Math.cos(ang + 0.55)} ${y2 - h * Math.sin(ang + 0.55)}`}
          fill="none" stroke={color} strokeWidth={width} strokeLinecap="round" strokeLinejoin="round" />
      )}
    </svg>
  );
};

// ---------- surfaces ----------

/** A flat panel with a thin graphite rule. `tab` is a small title on its top edge. */
export const Sheet: React.FC<{children?: React.ReactNode; style?: React.CSSProperties; tab?: string; tabColor?: string; pad?: number; tone?: string}> = ({children, style, tab, tabColor = C.ink2, pad = 24, tone = C.sheet}) => (
  <div style={{position: 'relative', background: tone, border: `1.5px solid ${C.ink}`, borderRadius: 8, padding: pad, fontFamily: SANS, color: C.ink, boxSizing: 'border-box', boxShadow: '0 6px 18px rgba(27,36,48,0.08)', ...style}}>
    {tab && (
      <div style={{position: 'absolute', top: -15, left: 18, background: tone, padding: '2px 10px', fontFamily: MONO, fontSize: 20, color: tabColor, border: `1.5px solid ${C.ink}`, borderRadius: 5}}>{tab}</div>
    )}
    {children}
  </div>
);

export const H: React.FC<{children: React.ReactNode; size?: number; color?: string; style?: React.CSSProperties; weight?: number}> = ({children, size = 64, color = C.ink, style, weight = 600}) => (
  <div style={{fontFamily: SANS, fontWeight: weight, fontSize: size, color, lineHeight: 1.15, letterSpacing: size > 50 ? -1 : 0, ...style}}>{children}</div>
);

export const P: React.FC<{children: React.ReactNode; size?: number; color?: string; style?: React.CSSProperties; mono?: boolean}> = ({children, size = 28, color = C.ink2, style, mono}) => (
  <div style={{fontFamily: mono ? MONO : SANS, fontWeight: 400, fontSize: size, color, lineHeight: 1.4, ...style}}>{children}</div>
);

export const Tag: React.FC<{children: React.ReactNode; color?: string; bg?: string; size?: number; mono?: boolean; style?: React.CSSProperties}> = ({children, color = C.ink, bg = C.blueSoft, size = 22, mono = false, style}) => (
  <span style={{display: 'inline-flex', alignItems: 'center', gap: 8, background: bg, color, fontFamily: mono ? MONO : SANS, fontWeight: 500, fontSize: size, padding: `${size * 0.18}px ${size * 0.5}px`, borderRadius: 6, whiteSpace: 'nowrap', lineHeight: 1.3, ...style}}>{children}</span>
);

/** Pass / warn / block marks. */
export const Status: React.FC<{kind: 'ok' | 'warn' | 'block' | 'off'; size?: number}> = ({kind, size = 28}) => {
  const color = kind === 'ok' ? C.green : kind === 'warn' ? C.amber : kind === 'block' ? C.red : C.ink3;
  return (
    <svg width={size} height={size} viewBox="0 0 28 28" style={{display: 'block', flexShrink: 0}}>
      <circle cx={14} cy={14} r={12} fill={color} />
      {kind === 'ok' && <path d="M8 14.5 L12.2 18.5 L20 10" fill="none" stroke="#fff" strokeWidth={2.6} strokeLinecap="round" strokeLinejoin="round" />}
      {kind === 'warn' && <><path d="M14 8 V16" stroke="#fff" strokeWidth={2.8} strokeLinecap="round" /><circle cx={14} cy={20} r={1.6} fill="#fff" /></>}
      {kind === 'block' && <path d="M9 14 H19" stroke="#fff" strokeWidth={2.8} strokeLinecap="round" />}
    </svg>
  );
};

// ---------- technical panels ----------

export type TreeRow = {d: number; name: string; note?: string; dir?: boolean; hi?: string; at?: number};

/** A file tree whose rows appear in order from `at`, `step` frames apart. Rows with their own `at` use it instead. */
export const FileTree: React.FC<{rows: TreeRow[]; at: number; step?: number; size?: number; width?: number}> = ({rows, at, step = 3, size = 24, width}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{fontFamily: MONO, fontSize: size, lineHeight: 1.65, color: C.ink, width}}>
      {rows.map((r, i) => {
        const t = r.at ?? at + i * step;
        const o = interpolate(frame, [t, t + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        const hiOn = r.hi ? frame >= (r.at ?? t) : false;
        return (
          <div key={i} style={{display: 'flex', alignItems: 'baseline', opacity: o, transform: `translateX(${(1 - o) * -6}px)`, paddingLeft: r.d * size * 1.3, background: hiOn ? r.hi : 'transparent', borderRadius: 4, paddingRight: 8}}>
            <span style={{color: C.ink3, marginRight: size * 0.5}}>{r.d > 0 ? '├─' : ''}</span>
            <span style={{color: r.dir ? C.blue : C.ink, fontWeight: r.dir ? 500 : 400}}>{r.name}{r.dir ? '/' : ''}</span>
            {r.note && <span style={{color: C.ink3, marginLeft: size * 0.9, fontFamily: SANS, fontSize: size * 0.85}}>{r.note}</span>}
          </div>
        );
      })}
    </div>
  );
};

export type CodeLine = {text: string; color?: string; at?: number; hi?: string};

/** Code or JSON whose lines appear in order. */
export const Code: React.FC<{lines: CodeLine[]; at: number; step?: number; size?: number}> = ({lines, at, step = 3, size = 24}) => {
  const frame = useCurrentFrame();
  return (
    <div style={{fontFamily: MONO, fontSize: size, lineHeight: 1.6, color: C.ink}}>
      {lines.map((l, i) => {
        const t = l.at ?? at + i * step;
        const o = interpolate(frame, [t, t + 6], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return (
          <div key={i} style={{opacity: o, whiteSpace: 'pre', color: l.color, background: l.hi && frame >= t ? l.hi : 'transparent', borderRadius: 4, margin: '0 -8px', padding: '0 8px'}}>{l.text || '\u00a0'}</div>
        );
      })}
    </div>
  );
};

/** A terminal: a typed command, then output lines appearing in order. */
// Commands type at 90 cps: fast enough that a long command is on screen within a second or two,
// so the output lines land while the narration is still describing them.
const TYPE_CPS = 90;

export const Terminal: React.FC<{at: number; command: string; output?: CodeLine[]; outAt?: number; width?: number; height?: number; size?: number; title?: string}> = ({at, command, output = [], outAt, width = 900, height, size = 23, title = 'agent shell'}) => {
  const cmdFrames = Math.ceil((command.length / TYPE_CPS) * FPS);
  // output waits for the typed command
  const start = outAt ?? at + cmdFrames + 8;
  return (
    <div style={{width, height, background: C.ink, borderRadius: 10, overflow: 'hidden', boxSizing: 'border-box', fontFamily: MONO, fontSize: size, color: '#E6EAF2', lineHeight: 1.6, boxShadow: '0 12px 30px rgba(27,36,48,0.18)'}}>
      <div style={{background: '#2A3545', color: '#9AA6B8', fontFamily: SANS, fontSize: size * 0.8, padding: '6px 16px', display: 'flex', alignItems: 'center', gap: 10}}>
        <span style={{display: 'inline-flex', gap: 6}}>{['#5B6B80', '#5B6B80', '#5B6B80'].map((c, i) => <span key={i} style={{width: 10, height: 10, borderRadius: '50%', background: c, display: 'inline-block'}} />)}</span>
        {title}
      </div>
      <div style={{padding: '14px 20px'}}>
        <div style={{whiteSpace: 'pre-wrap', wordBreak: 'break-all'}}><span style={{color: '#7FB0FF'}}>$ </span><Typed at={at} text={command} cps={TYPE_CPS} style={{whiteSpace: 'pre-wrap'}} /></div>
        {output.map((l, i) => (
          <OutLine key={i} at={l.at ?? start + i * 4} text={l.text} color={l.color} />
        ))}
      </div>
    </div>
  );
};

const OutLine: React.FC<{at: number; text: string; color?: string}> = ({at, text, color}) => {
  const frame = useCurrentFrame();
  if (frame < at) return null;
  return <div style={{whiteSpace: 'pre', color: color ?? '#E6EAF2'}}>{text}</div>;
};

// ---------- people ----------

/** A persona: initials in a circle, name, role. */
export const Persona: React.FC<{initials: string; name: string; role?: string; color?: string; size?: number; badge?: string; badgeAt?: number}> = ({initials, name, role, color = C.blue, size = 120, badge, badgeAt = 0}) => {
  const b = useReveal(badgeAt, 14);
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: size * 0.22, fontFamily: SANS}}>
      <div style={{position: 'relative', width: size, height: size, flexShrink: 0}}>
        <div style={{width: size, height: size, borderRadius: '50%', background: color, color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600, fontSize: size * 0.38, letterSpacing: 1, boxShadow: `0 0 0 ${Math.max(3, size * 0.05)}px ${C.sheet}, 0 0 0 ${Math.max(4.5, size * 0.065)}px ${color}33`}}>{initials}</div>
        {badge && (
          <div style={{position: 'absolute', right: -size * 0.12, bottom: -size * 0.04, background: C.amber, color: '#fff', fontSize: size * 0.15, fontWeight: 600, padding: `${size * 0.03}px ${size * 0.09}px`, borderRadius: 5, border: `2px solid ${C.paper}`, opacity: b, transform: `scale(${0.6 + 0.4 * b})`}}>{badge}</div>
        )}
      </div>
      <div>
        <div style={{fontWeight: 600, fontSize: size * 0.3, color: C.ink, lineHeight: 1.1}}>{name}</div>
        {role && <div style={{fontSize: size * 0.21, color: C.ink2, marginTop: size * 0.05, lineHeight: 1.2}}>{role}</div>}
      </div>
    </div>
  );
};

/** The agent: a rounded square with a simple face. */
export const Agent: React.FC<{size?: number; label?: string}> = ({size = 110, label = 'agent'}) => {
  const frame = useCurrentFrame();
  const blink = (frame % 110) < 4 ? 0.15 : 1;
  return (
    <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: size * 0.1, fontFamily: SANS}}>
      <svg width={size} height={size} viewBox="0 0 100 100">
        <rect x={6} y={10} width={88} height={80} rx={22} fill={C.ink} />
        <rect x={30} y={40} width={12} height={16 * blink} rx={4} fill="#7FB0FF" transform={`translate(0 ${8 * (1 - blink)})`} />
        <rect x={58} y={40} width={12} height={16 * blink} rx={4} fill="#7FB0FF" transform={`translate(0 ${8 * (1 - blink)})`} />
        <path d="M38 68 Q50 76 62 68" stroke="#7FB0FF" strokeWidth={4} fill="none" strokeLinecap="round" />
        <circle cx={50} cy={6} r={4} fill={C.blue} />
      </svg>
      {label && <div style={{fontSize: size * 0.2, color: C.ink2}}>{label}</div>}
    </div>
  );
};

/** A chat line from a person or the agent. */
export const Say: React.FC<{who: 'person' | 'agent'; children: React.ReactNode; size?: number; width?: number}> = ({who, children, size = 28, width}) => (
  <div style={{display: 'inline-block', maxWidth: width, background: who === 'person' ? C.blueSoft : C.sheet, border: who === 'person' ? 'none' : `1.5px solid ${C.rule}`, color: C.ink, fontFamily: SANS, fontSize: size, lineHeight: 1.35, padding: `${size * 0.45}px ${size * 0.7}px`, borderRadius: 14, borderTopLeftRadius: who === 'agent' ? 4 : 14, borderTopRightRadius: who === 'person' ? 4 : 14}}>{children}</div>
);

// ---------- stage ----------

export const Stage: React.FC<{children: React.ReactNode}> = ({children}) => (
  <div style={{position: 'absolute', inset: 0, background: C.paper, fontFamily: SANS, color: C.ink, overflow: 'hidden'}}>
    {/* Quiet graph paper: the fine grid is barely there, the coarse one is a hint. Text sits on top without competing. */}
    <div style={{position: 'absolute', inset: 0, backgroundImage: `linear-gradient(${C.grid} 1px, transparent 1px), linear-gradient(90deg, ${C.grid} 1px, transparent 1px)`, backgroundSize: '40px 40px', opacity: 0.3}} />
    <div style={{position: 'absolute', inset: 0, backgroundImage: `linear-gradient(${C.grid} 1.5px, transparent 1.5px), linear-gradient(90deg, ${C.grid} 1.5px, transparent 1.5px)`, backgroundSize: '200px 200px', opacity: 0.5}} />
    <div style={{position: 'absolute', inset: 0, background: `radial-gradient(ellipse at 50% 40%, transparent 55%, ${C.paper} 100%)`}} />
    {children}
  </div>
);

/** Scene heading, top-left, with a section index because the scenes are a sequence. */
export const Heading: React.FC<{n: number; title: string; at?: number}> = ({n, title, at = LEAD - 8}) => {
  const p = useReveal(at, 18);
  return (
    <div style={{position: 'absolute', left: 80, top: 56, display: 'flex', alignItems: 'baseline', gap: 22, opacity: p, transform: `translateY(${(1 - p) * 10}px)`}}>
      <span style={{fontFamily: MONO, fontSize: 26, color: C.blue}}>{String(n).padStart(2, '0')}</span>
      <H size={44} weight={600}>{title}</H>
    </div>
  );
};

/** Left-aligned, 80px gutter: the content column. */
export const Col: React.FC<{x?: number; y?: number; w?: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x = 80, y = 150, w = 1760, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y, width: w, ...style}}>{children}</div>
);
