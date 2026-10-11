import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {
  Arrow, Bot, Bubble, C, Card, Chip, Confetti, Dana, Enter, Exit, Float, FONT, Hop, ICalendar, ICheck, ICross, IGear,
  ILaptop, IPerson, ISparkle, IValve, MONO, Pop, SceneTag, Stage, Stamp, Title, useAt, usePop, useSmooth, useWiggle,
} from './kit';

const Abs: React.FC<{x: number; y: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y, ...style}}>{children}</div>
);

export const SkillCard: React.FC<{name: string; color?: string; scale?: number}> = ({name, color = C.mint, scale = 1}) => (
  <Card color={color} pad={0} radius={18} shadow={6} style={{padding: '12px 22px', fontSize: 30 * scale, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 12, whiteSpace: 'nowrap'}}>
    <svg width={28 * scale} height={28 * scale} viewBox="0 0 100 100"><path d="M50 4 Q56 44 96 50 Q56 56 50 96 Q44 56 4 50 Q44 44 50 4 Z" fill={C.white} stroke={C.ink} strokeWidth={8} /></svg>
    {name}
  </Card>
);

const Soil = ({size = 120}: {size?: number}) => (
  <svg width={size} height={size} viewBox="0 0 100 100" style={{display: 'block'}}>
    <path d="M6 86 Q50 50 94 86 Z" fill="#9C6B43" stroke={C.ink} strokeWidth={6} strokeLinejoin="round" />
    <path d="M50 70 V40" stroke={C.ink} strokeWidth={6} strokeLinecap="round" />
    <path d="M50 46 Q30 44 26 26 Q46 26 50 46" fill={C.mint} stroke={C.ink} strokeWidth={5} strokeLinejoin="round" />
    <path d="M50 40 Q66 34 74 18 Q54 18 50 40" fill={C.mint} stroke={C.ink} strokeWidth={5} strokeLinejoin="round" />
  </svg>
);

const Labeled: React.FC<{icon: React.ReactNode; label: string}> = ({icon, label}) => (
  <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}>
    {icon}
    <Chip color={C.white} size={28}>{label}</Chip>
  </div>
);

// ---------------------------------------------------------------- title

export const TitleScene: React.FC = () => {
  const words = ['Skills,', 'without', 'the', 'terminal'];
  return (
    <Stage tint={C.sun}>
      <div style={{position: 'absolute', top: 250, width: 1920, textAlign: 'center'}}>
        {words.map((w, i) => {
          const s = usePop(6 + i * 6);
          return (
            <span key={w} style={{display: 'inline-block', margin: '0 18px', transform: `scale(${s}) rotate(${(i % 2 ? 4 : -4) * s}deg)`, opacity: Math.min(1, s * 3)}}>
              <Title size={150} color={i === 3 ? C.coral : C.ink}>{w}</Title>
            </span>
          );
        })}
        <Pop at={34} x={0} y={210} w={1920}>
          <div style={{display: 'flex', justifyContent: 'center'}}>
            <Chip color={C.mint} size={42}>How our AI skill framework works</Chip>
          </div>
        </Pop>
      </div>
      <Enter at={20} from="left" x={180} y={560} dist={500}><Dana size={300} wave /></Enter>
      <Enter at={26} from="right" x={1450} y={580} dist={500}><Bot size={290} /></Enter>
      <Confetti at={30} y={380} />
    </Stage>
  );
};

// ---------------------------------------------------------------- 01 intro

export const Intro: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const move = useSmooth(at('Dana has also'), 22);
  const danaX = interpolate(move, [0, 1], [780, 330]);
  const tricks = at('We call them');
  const puzzle = at("So here's the puzzle");
  const mood = frame >= puzzle ? 'wow' : frame >= at('the works') ? 'grin' : 'happy';
  const skills = ['watering-plan', 'valve-check', 'block-notes'];
  const colors = [C.mint, C.sun, C.pink];
  return (
    <Stage tint={C.mint}>
      <SceneTag n={1} label="Meet Dana" />
      <Abs x={danaX} y={260}><Dana size={360} mood={mood} /></Abs>
      <Pop at={at('Meet Dana')} x={danaX + 10} y={790} w={340}>
        <Chip color={C.sun} size={34}>Dana · irrigation expert</Chip>
      </Pop>
      <Exit at={at('Dana has also') - 4}>
        <Pop at={at('Soil')} x={380} y={230} rotate={-8}><Float phase={0}><Labeled icon={<Soil size={170} />} label="soil" /></Float></Pop>
        <Pop at={at('valves')} x={1340} y={210} rotate={8}><Float phase={1}><Labeled icon={<IValve size={170} />} label="valves" /></Float></Pop>
        <Pop at={at('schedules')} x={1380} y={560} rotate={-6}><Float phase={2}><Labeled icon={<ICalendar size={170} />} label="schedules" /></Float></Pop>
        <Pop at={at('the works')} x={340} y={580} rotate={10}><Float phase={3}><ISparkle size={180} /></Float></Pop>
      </Exit>
      <Exit at={puzzle - 4}>
        <Enter at={at('an AI agent')} from="right" x={1300} y={330} dist={700}><Bot size={300} /></Enter>
        <Pop at={at('clever tricks')} x={1290} y={200}><Float><ISparkle size={70} color={C.pink} /></Float></Pop>
        <Pop at={at('clever tricks', 6)} x={1560} y={250}><Float phase={2}><ISparkle size={56} /></Float></Pop>
        <Pop at={at('skills')} x={690} y={140}><Title size={110} color={C.grape}>skills!</Title></Pop>
        {skills.map((s, i) => (
          <Hop key={s} a={tricks + 20 + i * 14} b={tricks + 44 + i * 14} x1={danaX + 180} y1={420} x2={980} y2={420 + i * 110} height={120}>
            <SkillCard name={s} color={colors[i]} />
          </Hop>
        ))}
        <Pop at={at('know-how')} x={760} y={770}><Chip color={C.white} size={32}>know-how → great answers</Chip></Pop>
      </Exit>
      <Pop at={puzzle} x={1000} y={130} rotate={12}><Float amp={14} rot={8}><Title size={260} color={C.coral}>?</Title></Float></Pop>
      <Enter at={at('whole team')} from="right" x={1150} y={380} dist={500}>
        <div style={{display: 'flex', gap: 10}}>
          {[C.pink, C.sky, C.sun, C.grape].map((c, i) => <Float key={c} phase={i} amp={6}><IPerson size={140} color={c} /></Float>)}
        </div>
      </Enter>
      {[['git', 'git'], ['terminals', 'terminals'], ['pull requests', 'pull requests']].map(([word, label], i) => {
        const a = at(word);
        const strike = interpolate(frame, [a + 8, a + 16], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
        return (
          <Pop key={word} at={a} x={1000 + i * 290 - (i === 2 ? 20 : 0)} y={640} rotate={i % 2 ? 5 : -5}>
            <div style={{position: 'relative'}}>
              <Chip color={C.white} size={36}><span style={{fontFamily: MONO}}>{label}</span></Chip>
              <div style={{position: 'absolute', left: -10, top: '45%', height: 10, width: `${strike * 110}%`, background: C.coral, borderRadius: 6, transform: 'rotate(-6deg)'}} />
            </div>
          </Pop>
        );
      })}
    </Stage>
  );
};

// ---------------------------------------------------------------- 02 problem

const Typed: React.FC<{text: string; at: number; color?: string; cps?: number}> = ({text, at, color = C.mint, cps = 45}) => {
  const frame = useCurrentFrame();
  const n = Math.max(0, Math.floor(((frame - at) / 30) * cps));
  if (frame < at) return null;
  return <div style={{color, whiteSpace: 'pre'}}>{text.slice(0, n)}{n < text.length && frame % 16 < 8 ? '▌' : ''}</div>;
};

export const Problem: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const conflict = at('Fight a merge conflict');
  const shake = useWiggle(conflict + 6, 16, 30);
  const sad = frame >= at('Cry a little') && frame < at('much simpler');
  const simpler = at('much simpler');
  return (
    <Stage tint={C.coral}>
      <SceneTag n={2} label="The usual way" />
      <Exit at={simpler - 4}>
        <Enter at={at('looks something like this')} from="left" x={150} y={190} dist={600}>
          <div style={{transform: `translateX(${shake}px) rotate(${shake * 0.15}deg)`}}>
            <Card color={C.ink} pad={0} style={{width: 1060, height: 600, overflow: 'hidden'}}>
              <div style={{background: '#2E2944', padding: '18px 24px', display: 'flex', gap: 14}}>
                {[C.coral, C.sun, C.mint].map((c) => <div key={c} style={{width: 24, height: 24, borderRadius: 12, background: c}} />)}
              </div>
              <div style={{fontFamily: MONO, fontSize: 32, padding: '28px 36px', lineHeight: 1.6}}>
                <Typed at={at('Clone a repo')} text="$ git clone git@github:org/skills.git" />
                <Typed at={at('Open a terminal')} text="$ git checkout -b fix-watering" />
                <Typed at={conflict} text={'$ git pull --rebase origin main'} />
                <Typed at={conflict + 14} color={C.coral} text={'CONFLICT (content): Merge conflict\n  in skills/watering-plan/SKILL.md'} cps={90} />
                <Typed at={conflict + 34} color={C.sun} text={'<<<<<<< HEAD   >>>>>>> ???'} cps={90} />
              </div>
            </Card>
          </div>
        </Enter>
        <Stamp at={at("That's not Dana's job")} text="NOT DANA'S JOB" x={680} y={500} size={86} />
      </Exit>
      <Abs x={1330} y={300}><Dana size={360} mood={sad ? 'sad' : frame >= simpler ? 'grin' : 'wow'} /></Abs>
      <Pop at={simpler} x={260} y={330} rotate={-4}><Title size={150}>Something</Title></Pop>
      <Pop at={simpler + 8} x={330} y={500} rotate={3}><Title size={170} color={C.mint} style={{WebkitTextStroke: `5px ${C.ink}`}}>simpler.</Title></Pop>
      <Pop at={simpler + 4} x={200} y={250}><Float><ISparkle size={90} /></Float></Pop>
      <Pop at={simpler + 12} x={1050} y={720}><Float phase={2}><ISparkle size={70} color={C.pink} /></Float></Pop>
    </Stage>
  );
};

// ---------------------------------------------------------------- 03 idea

export const Idea: React.FC = () => {
  const at = useAt();
  const works = at('It works in');
  const asks = [
    ['Installing', 'Install the irrigation skills'],
    ['Updating', 'Anything new?'],
    ['Sharing an improvement', 'Publish my change'],
    ['Sending feedback', 'That answer looked off'],
  ];
  const rest = at('does the rest');
  return (
    <Stage tint={C.sky}>
      <SceneTag n={3} label="The big idea" />
      <Pop at={at('big idea')} x={0} y={110} w={1920} style={{textAlign: 'center'}}>
        <Title size={96}>Just <span style={{color: C.coral}}>talk</span> to your agent</Title>
      </Pop>
      <Exit at={works - 4}>
        <Enter at={at('talking')} from="left" x={90} y={400} dist={400}><Dana size={300} /></Enter>
        <Enter at={at('your agent')} from="right" x={1530} y={420} dist={400}><Bot size={290} /></Enter>
        {asks.map(([cue, text], i) => (
          <React.Fragment key={cue}>
            <Pop at={at(cue)} x={480} y={270 + i * 155} style={{transformOrigin: 'left center'}}>
              <Bubble tail="none" size={40} color={[C.mint, C.sun, C.pink, C.white][i]}>{text}</Bubble>
            </Pop>
            <Pop at={rest + i * 5} x={1310} y={276 + i * 155}><ICheck size={86} /></Pop>
          </React.Fragment>
        ))}
        <Pop at={at('plain words')} x={1440} y={260}><Chip color={C.white} size={30}>plain words</Chip></Pop>
      </Exit>
      {['Claude Code', 'Cursor', 'Claude Science'].map((h, i) => (
        <Pop key={h} at={at(h)} x={170 + i * 540} y={330} rotate={[-4, 3, -2][i]}>
          <Card color={[C.sun, C.mint, C.pink][i]} style={{width: 500, height: 170, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 54, fontWeight: 700, whiteSpace: 'nowrap'}}>{h}</Card>
        </Pop>
      ))}
      {['Mac', 'Windows', 'Linux'].map((os, i) => (
        <Pop key={os} at={at(os)} x={420 + i * 400} y={590}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}><ILaptop size={110} color={[C.sky, C.teal, C.grape][i]} /><Title size={52}>{os}</Title></div>
        </Pop>
      ))}
    </Stage>
  );
};

// ---------------------------------------------------------------- 04 layers

const Block: React.FC<{title: string; sub?: string; color: string; w: number; h?: number; version: string; newVersion?: string; flipAt?: number; icon?: React.ReactNode; tagAt: number}> = ({
  title, sub, color, w, h = 160, version, newVersion, flipAt, icon, tagAt,
}) => {
  const frame = useCurrentFrame();
  const tagPop = usePop(tagAt);
  const flipPop = usePop(flipAt ?? 99999);
  const flipped = flipAt !== undefined && frame >= flipAt;
  return (
    <Card color={color} style={{width: w, height: h, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24, position: 'relative'}}>
      {icon}
      <div style={{textAlign: 'center'}}>
        <div style={{fontSize: w < 400 ? 42 : 54, fontWeight: 700, whiteSpace: 'nowrap'}}>{title}</div>
        {sub && <div style={{fontSize: 30, fontWeight: 500, opacity: 0.8}}>{sub}</div>}
      </div>
      <div style={{position: 'absolute', right: -24, top: -30, transform: `scale(${tagPop * (flipped ? 0.7 + 0.3 * flipPop : 1)})`}}>
        <VersionTag text={flipped && newVersion ? newVersion : version} hot={flipped} />
      </div>
    </Card>
  );
};

const VersionTag: React.FC<{text: string; hot?: boolean}> = ({text, hot}) => (
  <div style={{background: hot ? C.coral : C.white, color: hot ? C.white : C.ink, border: `5px solid ${C.ink}`, borderRadius: 14, padding: '4px 14px', fontFamily: MONO, fontWeight: 700, fontSize: 28, transform: 'rotate(8deg)'}}>{text}</div>
);

export const Layers: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const ver = at('own version');
  const sched = at('own schedule');
  const release = at('irrigation team releases');
  const rebuilt = at('nothing else');
  const bounce = (k: number) => {
    const t = frame - (sched + k * 7);
    return t > 0 && t < 18 ? -Math.sin((t / 18) * Math.PI) * 40 : 0;
  };
  const jump = frame - release;
  const jumpY = jump > 0 && jump < 22 ? -Math.sin((jump / 22) * Math.PI) * 90 : 0;
  const domains: [string, string, string, string][] = [
    ['irrigation', C.mint, 'v0.4.0', 'v0.5.0'],
    ['pest-control', C.coral, 'v1.1.0', ''],
    ['harvest', C.sun, 'v0.2.3', ''],
  ];
  return (
    <Stage tint={C.grape}>
      <SceneTag n={4} label="Three layers" />
      <Pop at={at('three layers')} x={1560} y={120} rotate={6}><Chip color={C.white} size={36}>3 layers</Chip></Pop>
      <Enter at={at('At the bottom')} from="top" dist={900} x={410} y={730}>
        <div style={{transform: `translateY(${bounce(0)}px)`}}>
          <Block title="Framework" sub="install · sync · publish · feedback" color={C.grape} w={1100} version="v1.4.0" tagAt={ver} icon={<IGear size={100} color={C.sun} />} />
        </div>
      </Enter>
      <Enter at={at('In the middle')} from="top" dist={900} x={470} y={540}>
        <div style={{transform: `translateY(${bounce(1)}px)`}}>
          <Block title="Foundation" sub="skills everyone shares" color={C.sky} w={980} version="v0.9.2" tagAt={ver + 5} />
        </div>
      </Enter>
      {domains.map(([name, color, v, nv], i) => (
        <Enter key={name} at={at('domain packages') + i * 10} from="top" dist={900} x={470 + i * 337} y={350}>
          <div style={{transform: `translateY(${bounce(2 + i) + (i === 0 ? jumpY : 0)}px)`}}>
            <Block title={name} color={color} w={306} h={160} version={v} tagAt={ver + 10 + i * 5} newVersion={nv || undefined} flipAt={i === 0 ? release + 10 : undefined} />
          </div>
          {i > 0 && <Pop at={rebuilt + (i - 1) * 6} x={60} y={-70}><Chip color={C.white} size={26}>untouched ✓</Chip></Pop>}
        </Enter>
      ))}
      <Pop at={at('like irrigation')} x={520} y={150}><Dana size={150} mood="grin" /></Pop>
      <Pop at={rebuilt + 12} x={1500} y={760}><Chip color={C.white} size={26}>untouched ✓</Chip></Pop>
      <Pop at={rebuilt + 16} x={1480} y={570}><Chip color={C.white} size={26}>untouched ✓</Chip></Pop>
      <Confetti at={release + 10} x={620} y={380} count={40} spread={500} />
    </Stage>
  );
};

export {Abs, Labeled, Typed};
