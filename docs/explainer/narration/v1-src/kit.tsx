import React, {createContext, useContext} from 'react';
import {interpolate, random, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {loadFont} from '@remotion/google-fonts/Fredoka';
import {loadFont as loadMono} from '@remotion/google-fonts/JetBrainsMono';
import timings from './timings.json';

export const {fontFamily: FONT} = loadFont('normal', {weights: ['400', '500', '600', '700'], subsets: ['latin']});
export const {fontFamily: MONO} = loadMono('normal', {weights: ['500', '700'], subsets: ['latin']});

export const C = {
  cream: '#FFF4E0',
  ink: '#1F1B2E',
  coral: '#FF6B6B',
  sun: '#FFC845',
  mint: '#3DDC97',
  sky: '#4D96FF',
  grape: '#9B5DE5',
  teal: '#2EC4B6',
  pink: '#FF8FB1',
  skin: '#F6C9A0',
  white: '#FFFFFF',
  paper: '#FFFDF7',
};

// ---------- timing ----------

export const FPS = 30;
export const LEAD = 14; // frames before a scene's narration starts
export const TAIL = 20; // frames after it ends
export type SceneId = keyof typeof timings;

export const sceneFrames = (id: SceneId, tail = TAIL) => LEAD + Math.ceil(timings[id].duration * FPS) + tail;

const SceneCtx = createContext<SceneId>('intro');
export const SceneProvider: React.FC<{id: SceneId; children: React.ReactNode}> = ({id, children}) => (
  <SceneCtx.Provider value={id}>{children}</SceneCtx.Provider>
);

const norm = (w: string) => w.toLowerCase().replace(/[^a-z0-9]/g, '');

/** Returns at(phrase) → the scene-relative frame where that phrase is spoken. */
export const useAt = () => {
  const id = useContext(SceneCtx);
  const words = timings[id].words;
  return (phrase: string, offset = 0) => {
    const target = phrase.split(/\s+/).map(norm).filter(Boolean);
    for (let i = 0; i + target.length <= words.length; i++) {
      if (target.every((t, k) => norm(words[i + k].w) === t)) {
        return LEAD + Math.round(words[i].s * FPS) + offset;
      }
    }
    throw new Error(`phrase not found in ${id}: "${phrase}"`);
  };
};

export const useSceneId = () => useContext(SceneCtx);

export const usePop = (at: number, config = {damping: 9, stiffness: 170, mass: 0.7}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - at, fps, config});
};

export const useSmooth = (at: number, dur = 15) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - at, fps, config: {damping: 200}, durationInFrames: dur});
};

// ---------- motion wrappers ----------

type Box = {x: number; y: number; w?: number; h?: number};

export const Pop: React.FC<{at: number; children: React.ReactNode; style?: React.CSSProperties; rotate?: number} & Box> = ({
  at, children, style, x, y, w, h, rotate = 0,
}) => {
  const s = usePop(at);
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, transform: `scale(${s}) rotate(${rotate * s}deg)`, opacity: Math.min(1, s * 4), ...style}}>
      {children}
    </div>
  );
};

export const Enter: React.FC<{at: number; from?: 'left' | 'right' | 'top' | 'bottom'; dist?: number; children: React.ReactNode; style?: React.CSSProperties} & Box> = ({
  at, from = 'bottom', dist = 260, children, style, x, y, w, h,
}) => {
  const s = usePop(at, {damping: 13, stiffness: 120, mass: 0.8});
  const d = (1 - s) * dist;
  const [dx, dy] = from === 'left' ? [-d, 0] : from === 'right' ? [d, 0] : from === 'top' ? [0, -d] : [0, d];
  return (
    <div style={{position: 'absolute', left: x, top: y, width: w, height: h, transform: `translate(${dx}px, ${dy}px)`, opacity: Math.min(1, s * 3), ...style}}>
      {children}
    </div>
  );
};

/** Fades and shrinks its children away from frame `at`. */
export const Exit: React.FC<{at: number; children: React.ReactNode; dur?: number}> = ({at, children, dur = 12}) => {
  const frame = useCurrentFrame();
  const t = interpolate(frame, [at, at + dur], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (t <= 0) return null;
  return <div style={{position: 'absolute', inset: 0, opacity: t, transform: `scale(${0.85 + 0.15 * t})`}}>{children}</div>;
};

export const Float: React.FC<{children: React.ReactNode; amp?: number; speed?: number; phase?: number; rot?: number}> = ({
  children, amp = 8, speed = 1, phase = 0, rot = 0,
}) => {
  const frame = useCurrentFrame();
  const t = (frame / 30) * speed + phase;
  return <div style={{transform: `translateY(${Math.sin(t * 2) * amp}px) rotate(${Math.sin(t * 1.3) * rot}deg)`}}>{children}</div>;
};

/** A quick jiggle starting at `at`. */
export const useWiggle = (at: number, amount = 8, dur = 24) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > dur) return 0;
  return Math.sin(t * 1.2) * amount * (1 - t / dur);
};

// ---------- surfaces ----------

export const Card: React.FC<{color?: string; children?: React.ReactNode; style?: React.CSSProperties; pad?: number; radius?: number; shadow?: number}> = ({
  color = C.white, children, style, pad = 28, radius = 28, shadow = 10,
}) => (
  <div
    style={{
      background: color,
      border: `6px solid ${C.ink}`,
      borderRadius: radius,
      boxShadow: `${shadow}px ${shadow}px 0 ${C.ink}`,
      padding: pad,
      fontFamily: FONT,
      color: C.ink,
      boxSizing: 'border-box',
      ...style,
    }}
  >
    {children}
  </div>
);

export const Chip: React.FC<{color?: string; children: React.ReactNode; size?: number; style?: React.CSSProperties}> = ({color = C.sun, children, size = 40, style}) => (
  <div
    style={{
      display: 'inline-flex', alignItems: 'center', gap: 14,
      background: color, border: `5px solid ${C.ink}`, borderRadius: 999,
      boxShadow: `6px 6px 0 ${C.ink}`, padding: `${size * 0.25}px ${size * 0.65}px`,
      fontFamily: FONT, fontWeight: 600, fontSize: size, color: C.ink, whiteSpace: 'nowrap', ...style,
    }}
  >
    {children}
  </div>
);

export const Bubble: React.FC<{children: React.ReactNode; tail?: 'left' | 'right' | 'none'; color?: string; size?: number; style?: React.CSSProperties}> = ({
  children, tail = 'left', color = C.white, size = 44, style,
}) => (
  <div style={{position: 'relative', display: 'inline-block', ...style}}>
    <Card color={color} pad={0} radius={36} shadow={8} style={{padding: '22px 34px', fontSize: size, fontWeight: 600, lineHeight: 1.2}}>
      {children}
    </Card>
    {tail !== 'none' && (
      <svg width="60" height="50" viewBox="0 0 60 50" style={{position: 'absolute', bottom: -40, [tail]: 50}}>
        <path d={tail === 'left' ? 'M6 0 L18 46 L50 0' : 'M54 0 L42 46 L10 0'} fill={color} stroke={C.ink} strokeWidth={6} strokeLinejoin="round" />
        <rect x="4" y="-8" width="52" height="12" fill={color} />
      </svg>
    )}
  </div>
);

export const Title: React.FC<{children: React.ReactNode; size?: number; color?: string; style?: React.CSSProperties}> = ({children, size = 84, color = C.ink, style}) => (
  <div style={{fontFamily: FONT, fontWeight: 700, fontSize: size, color, lineHeight: 1.05, letterSpacing: -1, ...style}}>{children}</div>
);

/** A rubber stamp that slams down at `at`. */
export const Stamp: React.FC<{at: number; text: string; color?: string; x: number; y: number; rotate?: number; size?: number}> = ({
  at, text, color = C.coral, x, y, rotate = -12, size = 90,
}) => {
  const frame = useCurrentFrame();
  const s = usePop(at, {damping: 12, stiffness: 260, mass: 0.6});
  if (frame < at) return null;
  const scale = interpolate(s, [0, 1], [3, 1]);
  return (
    <div
      style={{
        position: 'absolute', left: x, top: y, transform: `translate(-50%, -50%) scale(${scale}) rotate(${rotate}deg)`,
        opacity: Math.min(1, s * 2), border: `10px solid ${color}`, borderRadius: 24, padding: '6px 34px',
        color, fontFamily: FONT, fontWeight: 700, fontSize: size, letterSpacing: 4, whiteSpace: 'nowrap', background: 'rgba(255,255,255,0.85)',
      }}
    >
      {text}
    </div>
  );
};

export const Confetti: React.FC<{at: number; x?: number; y?: number; count?: number; spread?: number}> = ({at, x = 960, y = 450, count = 60, spread = 900}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > 75) return null;
  const colors = [C.coral, C.sun, C.mint, C.sky, C.grape, C.pink];
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      {Array.from({length: count}).map((_, i) => {
        const a = random(`a${i}${at}`) * Math.PI * 2;
        const v = 0.4 + random(`v${i}${at}`) * 0.6;
        const px = x + Math.cos(a) * v * spread * (1 - Math.exp(-t / 12));
        const py = y + Math.sin(a) * v * spread * 0.6 * (1 - Math.exp(-t / 12)) + t * t * 0.06;
        const r = t * 12 * (random(`r${i}`) - 0.5);
        return (
          <rect key={i} x={px} y={py} width={14} height={24} rx={4} fill={colors[i % colors.length]}
            stroke={C.ink} strokeWidth={3} transform={`rotate(${r} ${px + 7} ${py + 12})`} opacity={interpolate(t, [55, 75], [1, 0], {extrapolateLeft: 'clamp'})} />
        );
      })}
    </svg>
  );
};

/** An arrow that draws itself from (x1,y1) to (x2,y2). */
export const Arrow: React.FC<{at: number; x1: number; y1: number; x2: number; y2: number; color?: string; bend?: number; dur?: number}> = ({
  at, x1, y1, x2, y2, color = C.ink, bend = 0, dur = 18,
}) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [at, at + dur], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  if (p <= 0) return null;
  const mx = (x1 + x2) / 2 - (y2 - y1) * bend;
  const my = (y1 + y2) / 2 + (x2 - x1) * bend;
  const len = Math.hypot(x2 - x1, y2 - y1) * (1 + Math.abs(bend));
  const ang = Math.atan2(y2 - my, x2 - mx);
  const head = 26;
  return (
    <svg width={1920} height={1080} style={{position: 'absolute', left: 0, top: 0, pointerEvents: 'none'}}>
      <path d={`M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`} fill="none" stroke={color} strokeWidth={8} strokeLinecap="round"
        strokeDasharray={len} strokeDashoffset={len * (1 - p)} />
      {p > 0.95 && (
        <path d={`M${x2 - head * Math.cos(ang - 0.5)} ${y2 - head * Math.sin(ang - 0.5)} L${x2} ${y2} L${x2 - head * Math.cos(ang + 0.5)} ${y2 - head * Math.sin(ang + 0.5)}`}
          fill="none" stroke={color} strokeWidth={8} strokeLinecap="round" strokeLinejoin="round" />
      )}
    </svg>
  );
};

/** Moves its child along a hop from (x1,y1) to (x2,y2) between frames a and b. */
export const Hop: React.FC<{a: number; b: number; x1: number; y1: number; x2: number; y2: number; height?: number; children: React.ReactNode; hideBefore?: boolean}> = ({
  a, b, x1, y1, x2, y2, height = 160, children, hideBefore = true,
}) => {
  const frame = useCurrentFrame();
  if (hideBefore && frame < a) return null;
  const t = interpolate(frame, [a, b], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const e = t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2;
  const x = x1 + (x2 - x1) * e;
  const y = y1 + (y2 - y1) * e - Math.sin(Math.PI * e) * height;
  return <div style={{position: 'absolute', left: x, top: y, transform: 'translate(-50%, -50%)'}}>{children}</div>;
};

// ---------- characters ----------

const useBlink = (seed: number) => {
  const frame = useCurrentFrame();
  const period = 100 + (seed % 3) * 17;
  const k = (frame + seed * 31) % period;
  return k < 5 ? Math.abs(k - 2.5) / 2.5 : 1;
};

export type Mood = 'happy' | 'sad' | 'wow' | 'grin';

export const Dana: React.FC<{size?: number; mood?: Mood; badge?: string; wave?: boolean; flip?: boolean}> = ({size = 300, mood = 'happy', badge, wave = false, flip = false}) => {
  const frame = useCurrentFrame();
  const blink = useBlink(1);
  const bob = Math.sin(frame / 9) * 4;
  const armRot = wave ? -20 + Math.sin(frame / 4) * 25 : 112 + Math.sin(frame / 14) * 4;
  const tearY = ((frame % 40) / 40) * 40;
  return (
    <svg width={size} height={size * 1.3} viewBox="0 0 200 260" style={{overflow: 'visible', transform: flip ? 'scaleX(-1)' : undefined}}>
      <g transform={`translate(0 ${bob})`}>
        {/* arm */}
        <g transform={`rotate(${armRot} 150 200)`}>
          <path d="M150 200 Q185 175 182 140" stroke={C.ink} strokeWidth={22} strokeLinecap="round" fill="none" />
          <path d="M150 200 Q185 175 182 140" stroke={C.mint} strokeWidth={12} strokeLinecap="round" fill="none" />
          <circle cx={182} cy={136} r={13} fill={C.skin} stroke={C.ink} strokeWidth={5} />
        </g>
        <path d="M38 262 Q38 172 100 172 Q162 172 162 262 Z" fill={C.mint} stroke={C.ink} strokeWidth={6} strokeLinejoin="round" />
        <path d="M84 174 L100 196 L116 174" fill="none" stroke={C.ink} strokeWidth={5} strokeLinejoin="round" />
        <path d="M52 120 Q46 160 66 168 L134 168 Q154 160 148 120 Z" fill="#7A4A2A" stroke={C.ink} strokeWidth={5} />
        <circle cx={100} cy={115} r={52} fill={C.skin} stroke={C.ink} strokeWidth={6} />
        <circle cx={72} cy={133} r={9} fill={C.pink} opacity={0.6} />
        <circle cx={128} cy={133} r={9} fill={C.pink} opacity={0.6} />
        <ellipse cx={82} cy={114} rx={6.5} ry={9 * blink + 0.5} fill={C.ink} />
        <ellipse cx={118} cy={114} rx={6.5} ry={9 * blink + 0.5} fill={C.ink} />
        {mood === 'happy' && <path d="M84 136 Q100 152 116 136" stroke={C.ink} strokeWidth={5} fill="none" strokeLinecap="round" />}
        {mood === 'grin' && <path d="M80 133 Q100 162 120 133 Z" fill={C.ink} stroke={C.ink} strokeWidth={4} strokeLinejoin="round" />}
        {mood === 'sad' && <path d="M86 148 Q100 136 114 148" stroke={C.ink} strokeWidth={5} fill="none" strokeLinecap="round" />}
        {mood === 'wow' && <ellipse cx={100} cy={142} rx={8} ry={10} fill={C.ink} />}
        {mood === 'sad' && <path d={`M76 ${124 + tearY} q6 10 0 14 q-6 -4 0 -14`} fill={C.sky} stroke={C.ink} strokeWidth={3} />}
        {/* hat */}
        <ellipse cx={100} cy={74} rx={90} ry={17} fill={C.sun} stroke={C.ink} strokeWidth={6} />
        <path d="M58 74 Q58 24 100 24 Q142 24 142 74 Z" fill={C.sun} stroke={C.ink} strokeWidth={6} strokeLinejoin="round" />
        <path d="M60 60 Q100 68 140 60 L141 72 Q100 80 59 72 Z" fill={C.coral} stroke={C.ink} strokeWidth={4} />
        <path d="M100 42 q9 12 0 17 q-9 -5 0 -17" fill={C.sky} stroke={C.ink} strokeWidth={3} />
      </g>
      {badge && (
        <g transform={`translate(70 ${222 + bob}) rotate(-6)`}>
          <rect x={-4} y={-18} width={98} height={34} rx={10} fill={C.sun} stroke={C.ink} strokeWidth={4} />
          <text x={45} y={6} textAnchor="middle" fontFamily={FONT} fontWeight={700} fontSize={17} fill={C.ink}>{badge}</text>
        </g>
      )}
    </svg>
  );
};

export const Bot: React.FC<{size?: number; mood?: Mood; color?: string}> = ({size = 260, mood = 'happy', color = C.sky}) => {
  const frame = useCurrentFrame();
  const blink = useBlink(2);
  const float = Math.sin(frame / 11 + 1) * 7;
  const glow = 0.6 + 0.4 * Math.sin(frame / 6);
  return (
    <svg width={size} height={size * 1.2} viewBox="0 0 200 240" style={{overflow: 'visible'}}>
      <ellipse cx={100} cy={232} rx={50 - float} ry={7} fill={C.ink} opacity={0.15} />
      <g transform={`translate(0 ${float})`}>
        <line x1={100} y1={42} x2={100} y2={14} stroke={C.ink} strokeWidth={6} />
        <circle cx={100} cy={12} r={11} fill={C.coral} stroke={C.ink} strokeWidth={5} opacity={0.5 + glow * 0.5} />
        <rect x={20} y={80} width={18} height={40} rx={8} fill={color} stroke={C.ink} strokeWidth={5} />
        <rect x={162} y={80} width={18} height={40} rx={8} fill={color} stroke={C.ink} strokeWidth={5} />
        <rect x={32} y={40} width={136} height={112} rx={34} fill={color} stroke={C.ink} strokeWidth={6} />
        <rect x={50} y={58} width={100} height={76} rx={20} fill={C.ink} />
        <ellipse cx={80} cy={92} rx={9} ry={12 * blink + 0.5} fill={C.mint} />
        <ellipse cx={120} cy={92} rx={9} ry={12 * blink + 0.5} fill={C.mint} />
        {mood === 'wow' ? <circle cx={100} cy={116} r={7} fill={C.mint} /> : <path d="M86 112 Q100 124 114 112" stroke={C.mint} strokeWidth={5} fill="none" strokeLinecap="round" />}
        <rect x={62} y={158} width={76} height={58} rx={20} fill={C.grape} stroke={C.ink} strokeWidth={6} />
        <path d="M104 170 L92 190 L102 190 L96 206 L112 184 L102 184 Z" fill={C.sun} stroke={C.ink} strokeWidth={3} strokeLinejoin="round" />
      </g>
    </svg>
  );
};

// ---------- icons (100×100) ----------

const S = {stroke: C.ink, strokeWidth: 6, strokeLinejoin: 'round' as const, strokeLinecap: 'round' as const};
const Ico: React.FC<{size?: number; children: React.ReactNode}> = ({size = 120, children}) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={{overflow: 'visible', display: 'block'}}>{children}</svg>
);
type IP = {size?: number; color?: string};

export const IDrop = ({size, color = C.sky}: IP) => <Ico size={size}><path d="M50 8 Q80 48 78 64 A28 28 0 0 1 22 64 Q20 48 50 8 Z" fill={color} {...S} /><path d="M36 64 a14 14 0 0 0 10 14" fill="none" stroke={C.white} strokeWidth={5} strokeLinecap="round" /></Ico>;
export const IValve = ({size, color = C.coral}: IP) => <Ico size={size}><circle cx={50} cy={50} r={36} fill={color} {...S} /><circle cx={50} cy={50} r={12} fill={C.white} {...S} />{[0, 60, 120].map((a) => <line key={a} x1={50} y1={14} x2={50} y2={86} {...S} transform={`rotate(${a} 50 50)`} />)}<circle cx={50} cy={50} r={10} fill={C.sun} {...S} /></Ico>;
export const ICalendar = ({size, color = C.white}: IP) => <Ico size={size}><rect x={12} y={18} width={76} height={70} rx={12} fill={color} {...S} /><path d="M12 38 H88" {...S} /><rect x={12} y={18} width={76} height={20} rx={10} fill={C.coral} {...S} /><line x1={32} y1={10} x2={32} y2={26} {...S} /><line x1={68} y1={10} x2={68} y2={26} {...S} />{[0, 1, 2].map((r) => [0, 1, 2].map((c) => <circle key={`${r}${c}`} cx={30 + c * 20} cy={52 + r * 13} r={4} fill={C.ink} />))}</Ico>;
export const IFolder = ({size, color = C.sun}: IP) => <Ico size={size}><path d="M8 26 Q8 18 16 18 H40 L48 28 H84 Q92 28 92 36 V78 Q92 86 84 86 H16 Q8 86 8 78 Z" fill={color} {...S} /><path d="M8 40 H92" {...S} /></Ico>;
export const ILock = ({size, color = C.sun}: IP) => <Ico size={size}><path d="M30 46 V32 A20 20 0 0 1 70 32 V46" fill="none" {...S} strokeWidth={9} /><rect x={18} y={44} width={64} height={46} rx={12} fill={color} {...S} /><circle cx={50} cy={62} r={7} fill={C.ink} /><rect x={47} y={62} width={6} height={14} rx={3} fill={C.ink} /></Ico>;
export const IServer = ({size, color = C.white}: IP) => <Ico size={size}>{[0, 1, 2].map((i) => <g key={i}><rect x={14} y={10 + i * 28} width={72} height={24} rx={8} fill={color} {...S} /><circle cx={28} cy={22 + i * 28} r={4} fill={C.mint} /><line x1={50} y1={22 + i * 28} x2={74} y2={22 + i * 28} {...S} strokeWidth={4} /></g>)}</Ico>;
export const IBucket = ({size, color = C.teal}: IP) => <Ico size={size}><path d="M24 30 Q50 -4 76 30" fill="none" {...S} /><path d="M14 30 H86 L76 88 H24 Z" fill={color} {...S} /><ellipse cx={50} cy={30} rx={36} ry={8} fill={C.white} {...S} /></Ico>;
export const IRepo = ({size, color = C.grape}: IP) => <Ico size={size}><path d="M30 20 V80 M30 60 Q30 44 70 40" fill="none" {...S} strokeWidth={7} /><circle cx={30} cy={20} r={11} fill={color} {...S} /><circle cx={30} cy={82} r={11} fill={color} {...S} /><circle cx={70} cy={36} r={11} fill={C.sun} {...S} /></Ico>;
export const IZip = ({size, color = C.sun}: IP) => <Ico size={size}><path d="M10 34 L50 16 L90 34 V74 L50 92 L10 74 Z" fill={color} {...S} /><path d="M10 34 L50 52 L90 34 M50 52 V92" fill="none" {...S} /><path d="M30 25 L70 43 V58" fill="none" stroke={C.coral} strokeWidth={8} strokeLinecap="round" /></Ico>;
export const IDoc = ({size, color = C.white}: IP) => <Ico size={size}><path d="M20 8 H62 L82 28 V92 H20 Z" fill={color} {...S} /><path d="M62 8 V28 H82" fill={C.sun} {...S} />{[44, 58, 72].map((y) => <line key={y} x1={32} y1={y} x2={70} y2={y} {...S} strokeWidth={5} />)}</Ico>;
export const IFinger = ({size, color = C.teal}: IP) => <Ico size={size}><circle cx={50} cy={50} r={44} fill={color} {...S} />{[10, 18, 26, 34].map((r) => <path key={r} d={`M${50 - r} ${56} A${r} ${r + 4} 0 0 1 ${50 + r} ${56} V${66 - r / 4}`} fill="none" stroke={C.ink} strokeWidth={5} strokeLinecap="round" />)}<line x1={50} y1={52} x2={50} y2={80} stroke={C.ink} strokeWidth={5} strokeLinecap="round" /></Ico>;
export const ICheck = ({size, color = C.mint}: IP) => <Ico size={size}><circle cx={50} cy={50} r={42} fill={color} {...S} /><path d="M30 52 L44 66 L72 36" fill="none" {...S} strokeWidth={10} /></Ico>;
export const ICross = ({size, color = C.coral}: IP) => <Ico size={size}><circle cx={50} cy={50} r={42} fill={color} {...S} /><path d="M34 34 L66 66 M66 34 L34 66" fill="none" {...S} strokeWidth={10} /></Ico>;
export const IWarn = ({size, color = C.sun}: IP) => <Ico size={size}><path d="M50 8 L94 88 H6 Z" fill={color} {...S} /><line x1={50} y1={38} x2={50} y2={62} {...S} strokeWidth={9} /><circle cx={50} cy={76} r={5} fill={C.ink} /></Ico>;
export const IStop = ({size, color = C.coral}: IP) => <Ico size={size}><path d="M32 6 H68 L94 32 V68 L68 94 H32 L6 68 V32 Z" fill={color} {...S} /><line x1={28} y1={50} x2={72} y2={50} stroke={C.white} strokeWidth={12} strokeLinecap="round" /></Ico>;
export const IInbox = ({size, color = C.sky}: IP) => <Ico size={size}><path d="M8 54 L22 20 H78 L92 54 V84 H8 Z" fill={color} {...S} /><path d="M8 54 H32 L38 66 H62 L68 54 H92" fill={C.white} {...S} /></Ico>;
export const ISheet = ({size, color = C.mint}: IP) => <Ico size={size}><rect x={10} y={12} width={80} height={76} rx={10} fill={C.white} {...S} /><rect x={10} y={12} width={80} height={18} rx={9} fill={color} {...S} />{[49, 68].map((y) => <line key={y} x1={10} y1={y} x2={90} y2={y} {...S} strokeWidth={4} />)}{[37, 63].map((x) => <line key={x} x1={x} y1={30} x2={x} y2={88} {...S} strokeWidth={4} />)}</Ico>;
export const ILaptop = ({size, color = C.sky}: IP) => <Ico size={size}><rect x={16} y={16} width={68} height={50} rx={8} fill={color} {...S} /><rect x={24} y={24} width={52} height={34} rx={4} fill={C.white} {...S} strokeWidth={3} /><path d="M4 74 H96 L88 86 H12 Z" fill={C.white} {...S} /></Ico>;
export const IKey = ({size, color = C.sun}: IP) => <Ico size={size}><circle cx={30} cy={50} r={20} fill={color} {...S} /><circle cx={30} cy={50} r={6} fill={C.white} {...S} strokeWidth={4} /><path d="M50 50 H92 M78 50 V64 M88 50 V60" fill="none" {...S} strokeWidth={9} /></Ico>;
export const IGlobe = ({size, color = C.sky}: IP) => <Ico size={size}><circle cx={50} cy={50} r={40} fill={color} {...S} /><ellipse cx={50} cy={50} rx={17} ry={40} fill="none" {...S} strokeWidth={5} /><path d="M12 38 H88 M12 62 H88" {...S} strokeWidth={5} /></Ico>;
export const IBell = ({size, color = C.sun}: IP) => <Ico size={size}><path d="M22 72 Q28 64 28 46 A22 22 0 0 1 72 46 Q72 64 78 72 Z" fill={color} {...S} /><circle cx={50} cy={80} r={8} fill={C.ink} /><circle cx={50} cy={20} r={5} fill={C.ink} /></Ico>;
export const IShield = ({size, color = C.mint}: IP) => <Ico size={size}><path d="M50 6 L88 20 V48 Q88 78 50 94 Q12 78 12 48 V20 Z" fill={color} {...S} /><path d="M34 50 L46 62 L68 38" fill="none" {...S} strokeWidth={9} /></Ico>;
export const IGear = ({size, color = C.grape}: IP) => <Ico size={size}>{Array.from({length: 8}).map((_, i) => <rect key={i} x={43} y={4} width={14} height={20} rx={4} fill={color} {...S} strokeWidth={5} transform={`rotate(${i * 45} 50 50)`} />)}<circle cx={50} cy={50} r={30} fill={color} {...S} /><circle cx={50} cy={50} r={11} fill={C.white} {...S} /></Ico>;
export const IPencil = ({size, color = C.sun}: IP) => <Ico size={size}><g transform="rotate(45 50 50)"><rect x={38} y={4} width={24} height={66} rx={4} fill={color} {...S} /><path d="M38 70 L50 94 L62 70 Z" fill={C.skin} {...S} /><rect x={38} y={4} width={24} height={14} rx={4} fill={C.pink} {...S} /></g></Ico>;
export const IMagnifier = ({size, color = C.white}: IP) => <Ico size={size}><line x1={64} y1={64} x2={90} y2={90} {...S} strokeWidth={14} /><circle cx={42} cy={42} r={30} fill={color} {...S} /><path d="M26 38 a16 16 0 0 1 14 -14" fill="none" stroke={C.sky} strokeWidth={5} strokeLinecap="round" /></Ico>;
export const IClock = ({size, color = C.white}: IP) => <Ico size={size}><circle cx={50} cy={50} r={42} fill={color} {...S} /><path d="M50 24 V50 L68 60" fill="none" {...S} strokeWidth={7} /></Ico>;
export const IEnvelope = ({size, color = C.white}: IP) => <Ico size={size}><rect x={8} y={22} width={84} height={58} rx={8} fill={color} {...S} /><path d="M8 28 L50 58 L92 28" fill="none" {...S} /></Ico>;
export const ISparkle = ({size, color = C.sun}: IP) => <Ico size={size}><path d="M50 4 Q56 44 96 50 Q56 56 50 96 Q44 56 4 50 Q44 44 50 4 Z" fill={color} {...S} strokeWidth={5} /></Ico>;
export const ITerminal = ({size, color = C.ink}: IP) => <Ico size={size}><rect x={6} y={14} width={88} height={72} rx={10} fill={color} {...S} /><path d="M22 38 L36 50 L22 62" fill="none" stroke={C.mint} strokeWidth={7} strokeLinecap="round" strokeLinejoin="round" /><line x1={44} y1={64} x2={66} y2={64} stroke={C.mint} strokeWidth={7} strokeLinecap="round" /></Ico>;
export const IPerson = ({size, color = C.pink}: IP) => <Ico size={size}><circle cx={50} cy={34} r={18} fill={C.skin} {...S} /><path d="M18 92 Q18 58 50 58 Q82 58 82 92 Z" fill={color} {...S} /></Ico>;

// ---------- backdrop ----------

export const Backdrop: React.FC<{tint?: string}> = ({tint = C.sun}) => {
  const frame = useCurrentFrame();
  const blobs = [
    {x: 180, y: 160, r: 220, c: tint, s: 0.7},
    {x: 1720, y: 260, r: 180, c: C.pink, s: 1.1},
    {x: 1600, y: 900, r: 260, c: tint, s: 0.9},
    {x: 260, y: 920, r: 160, c: C.sky, s: 1.3},
  ];
  return (
    <div style={{position: 'absolute', inset: 0, background: C.cream, overflow: 'hidden'}}>
      <div style={{position: 'absolute', inset: 0, backgroundImage: `radial-gradient(${C.ink}22 3px, transparent 3.5px)`, backgroundSize: '48px 48px', backgroundPosition: `${(frame * 0.4) % 48}px ${(frame * 0.4) % 48}px`}} />
      {blobs.map((b, i) => (
        <div key={i} style={{
          position: 'absolute', left: b.x - b.r + Math.sin(frame / 50 * b.s + i) * 30, top: b.y - b.r + Math.cos(frame / 60 * b.s + i) * 30,
          width: b.r * 2, height: b.r * 2, borderRadius: '50%', background: b.c, opacity: 0.22,
        }} />
      ))}
    </div>
  );
};

export const Stage: React.FC<{tint?: string; children: React.ReactNode}> = ({tint, children}) => (
  <div style={{position: 'absolute', inset: 0, fontFamily: FONT, color: C.ink}}>
    <Backdrop tint={tint} />
    {children}
  </div>
);

/** Scene label shown top-left, e.g. "02 · The problem". */
export const SceneTag: React.FC<{n: number; label: string; color?: string}> = ({n, label, color = C.white}) => {
  const s = useSmooth(LEAD - 6, 18);
  return (
    <div style={{position: 'absolute', left: 60, top: 48, transform: `translateX(${(1 - s) * -300}px)`}}>
      <Chip color={color} size={30}><span style={{opacity: 0.55}}>{String(n).padStart(2, '0')}</span>{label}</Chip>
    </div>
  );
};
