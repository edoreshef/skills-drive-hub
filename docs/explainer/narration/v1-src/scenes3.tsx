import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {
  Arrow, Bot, Bubble, C, Card, Chip, Confetti, Dana, Enter, Exit, Float, Hop, IBell, ICheck, ICross, IDoc, IEnvelope,
  IFinger, IFolder, IGear, IGlobe, IInbox, IKey, ILaptop, ILock, IMagnifier, IPencil, IPerson, ISheet, IShield, ISparkle,
  IStop, IWarn, IZip, MONO, Pop, SceneTag, Stage, Stamp, Title, useAt, usePop, useSmooth, useWiggle,
} from './kit';
import {Abs, SkillCard} from './scenes1';

// ---------------------------------------------------------------- 09 maintainer

export const Maintainer: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const twist = at("here's the twist");
  const maint = at('also a maintainer');
  const submits = at('teammate submits');
  const report = at('The review tool');
  const call = at("tools don't make the call");
  const danaDoes = at('Dana does');
  const spin = interpolate(frame, [maint - 4, maint + 10], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const toSide = useSmooth(submits, 20);
  const danaX = interpolate(toSide, [0, 1], [780, 70]);
  const rows: [string, string, React.ReactNode][] = [
    ['Who sent it', 'Sent by', <span key="a" style={{fontFamily: MONO}}>sam@team</span>],
    ['Who owns the skill', 'Owner', <span key="b" style={{fontFamily: MONO}}>dana@team</span>],
    ['Why it changed', 'Why', '“Adds frost alerts”'],
    ["Exactly what's different", 'Diff', (
      <div key="c" style={{fontFamily: MONO, fontSize: 26, lineHeight: 1.35}}>
        <div style={{color: '#1C8F5E'}}>+ Warn when frost is forecast</div>
        <div style={{color: '#D64545'}}>− Fixed 2°C threshold</div>
      </div>
    )],
    ['what the checks found', 'Checks', <span key="d"><b style={{color: '#D64545'}}>0 blocking</b> · <b style={{color: '#B7860B'}}>1 warning</b></span>],
  ];
  return (
    <Stage tint={C.sun}>
      <SceneTag n={9} label="You're a maintainer too" />
      <Exit at={submits - 4}><Pop at={twist} x={1300} y={130} rotate={8}><Chip color={C.coral} size={40}>plot twist!</Chip></Pop></Exit>
      <Exit at={call - 4}>
        <Abs x={danaX} y={300}>
          <div style={{transform: `scaleX(${Math.cos(spin * Math.PI * 2)})`}}>
            <Dana size={300} mood={frame >= maint ? 'grin' : 'happy'} badge={frame >= maint + 4 ? 'MAINTAINER' : undefined} />
          </div>
        </Abs>
        <Exit at={submits - 4}>
          <Pop at={at('just an author')} x={1180} y={360} rotate={-6}><Chip color={C.white} size={40}>author</Chip></Pop>
          <Pop at={maint + 6} x={1180} y={480} rotate={5}>
            <Chip color={C.sun} size={40}><ISparkle size={44} /> maintainer of irrigation</Chip>
          </Pop>
        </Exit>
        <Exit at={report}>
          <Enter at={submits} from="right" x={1660} y={380} dist={400}>
            <IPerson size={170} color={C.sky} />
            <div style={{textAlign: 'center'}}><Chip color={C.white} size={26}>Sam</Chip></div>
          </Enter>
          <Hop a={submits + 14} b={at("lands on Dana's desk")} x1={1700} y1={400} x2={430} y2={330} height={180}><IEnvelope size={120} /></Hop>
        </Exit>
        {frame >= report - 6 && (
          <Pop at={report} x={560} y={150} style={{transformOrigin: 'top center'}}>
            <Card color={C.paper} style={{width: 860, padding: 30}}>
              <div style={{display: 'flex', alignItems: 'center', gap: 14, fontSize: 40, fontWeight: 700, marginBottom: 14}}>
                <IMagnifier size={56} /> Review: frost-alerts
              </div>
              {rows.map(([cue, label, value]) => (
                <Pop key={cue} at={at(cue)} x={0} y={0} style={{position: 'relative', transformOrigin: 'left center'}}>
                  <div style={{display: 'flex', alignItems: 'center', gap: 20, borderTop: `3px dashed ${C.ink}33`, padding: '14px 0', fontSize: 32}}>
                    <div style={{width: 150, fontWeight: 700}}>{label}</div>
                    <div style={{fontWeight: 500}}>{value}</div>
                  </div>
                </Pop>
              ))}
            </Card>
          </Pop>
        )}
        <Pop at={at('Broken structure blocks')} x={1490} y={220}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}><IStop size={160} /><Chip color={C.white} size={30}>broken = blocks</Chip></div>
        </Pop>
        <Pop at={at('just a warning')} x={1490} y={520}>
          <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10}}><IWarn size={160} /><Chip color={C.white} size={30}>rest = warning</Chip></div>
        </Pop>
      </Exit>
      <Pop at={call} x={0} y={140} w={1920} style={{textAlign: 'center'}}>
        <Title size={90}>The tools don't decide.</Title>
      </Pop>
      <Enter at={call + 6} from="bottom" x={800} y={330} dist={500}><Dana size={300} mood={frame >= danaDoes ? 'grin' : 'happy'} badge="MAINTAINER" /></Enter>
      <Pop at={danaDoes} x={1180} y={420} rotate={-8}><Title size={120} color={C.coral} style={{WebkitTextStroke: `4px ${C.ink}`}}>Dana does.</Title></Pop>
      <Confetti at={danaDoes} x={960} y={500} count={50} />
    </Stage>
  );
};

// ---------------------------------------------------------------- 10 review

const Sticky: React.FC<{color: string; icon: React.ReactNode; text: string; sub: string; rotate: number}> = ({color, icon, text, sub, rotate}) => (
  <div style={{transform: `rotate(${rotate}deg)`}}>
    <Card color={color} radius={10} style={{width: 390, height: 360, display: 'flex', flexDirection: 'column', gap: 14}}>
      <div style={{width: 60, height: 22, background: `${C.white}AA`, border: `3px solid ${C.ink}`, borderRadius: 4, alignSelf: 'center', marginTop: -44}} />
      {icon}
      <div style={{fontSize: 38, fontWeight: 700, lineHeight: 1.1}}>{text}</div>
      <div style={{fontSize: 26, fontWeight: 500, lineHeight: 1.2}}>{sub}</div>
    </Card>
  </div>
);

const BigButton: React.FC<{at: number; color: string; label: string; icon: React.ReactNode}> = ({at, color, label, icon}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  const press = t > 0 && t < 10 ? Math.sin((t / 10) * Math.PI) : 0;
  return (
    <div style={{transform: `translate(${press * 8}px, ${press * 8}px)`}}>
      <Card color={color} radius={40} shadow={14 - press * 10} style={{width: 560, height: 190, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 24, fontSize: 80, fontWeight: 700}}>
        {icon}{label}
      </Card>
    </div>
  );
};

export const Review: React.FC = () => {
  const at = useAt();
  const decide = at('Then decide');
  const accept = at('Accept, and');
  const reject = at('Reject, and');
  const either = at('Either way');
  const tips: [string, string, string, string, React.ReactNode][] = [
    ['Read the words', 'Read the words, not just code', 'One sentence can change what the agent does', C.sun, <IMagnifier key="m" size={90} />],
    ['reach out to the internet', 'Scripts that go online', 'Skills work on local files only', C.pink, <IGlobe key="g" size={90} />],
    ['looks like a password', 'Anything like a password', 'No secrets in a package, ever', C.sky, <IKey key="k" size={90} />],
    ['give the owner a heads up', 'Not the owner? Tell them', 'Give the skill’s owner a heads up', C.mint, <IBell key="b" size={90} />],
  ];
  return (
    <Stage tint={C.mint}>
      <SceneTag n={10} label="Reviewing like a pro" />
      <Exit at={decide - 4}>
        <Pop at={at('A few tips')} x={0} y={110} w={1920} style={{textAlign: 'center'}}><Title size={84}>Reviewer tips</Title></Pop>
        {tips.map(([cue, text, sub, color, icon], i) => (
          <Enter key={cue} at={at(cue)} from="bottom" dist={700} x={100 + i * 440} y={300}>
            <Sticky color={color} icon={icon} text={text} sub={sub} rotate={[-3, 2, -2, 3][i]} />
          </Enter>
        ))}
        <Pop at={at('instructions for the agent')} x={130} y={720} rotate={-3}><Chip color={C.white} size={30}>skill text = instructions</Chip></Pop>
      </Exit>
      <Pop at={decide} x={0} y={110} w={1920} style={{textAlign: 'center'}}><Title size={90}>Your call</Title></Pop>
      <Exit at={either - 4}>
        <Pop at={decide + 4} x={300} y={280}><BigButton at={accept} color={C.mint} label="Accept" icon={<ICheck size={110} color={C.white} />} /></Pop>
        <Pop at={decide + 10} x={1060} y={280}><BigButton at={reject} color={C.coral} label="Reject" icon={<ICross size={110} color={C.white} />} /></Pop>
        <Hop a={accept + 6} b={accept + 30} x1={580} y1={500} x2={580} y2={680} height={90}><IZip size={120} /></Hop>
        <Pop at={accept + 26} x={380} y={760}><Chip color={C.white} size={32}>into the next release</Chip></Pop>
        <Pop at={reject + 6} x={1230} y={540}><IDoc size={140} /></Pop>
        <Pop at={reject + 14} x={1170} y={710}><Chip color={C.white} size={32}><span style={{fontFamily: MONO}}>REVIEW.md</span>&nbsp;says why</Chip></Pop>
      </Exit>
      <Enter at={either} from="bottom" x={480} y={340} dist={500}><Bot size={260} /></Enter>
      <Pop at={at("author's agent can read")} x={820} y={300} style={{transformOrigin: 'left bottom'}}>
        <Bubble tail="left" size={44} color={C.white}>Your change was reviewed.<br />Here’s the outcome!</Bubble>
      </Pop>
    </Stage>
  );
};

// ---------------------------------------------------------------- 11 feedback

export const Feedback: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const which = at('asks which skill');
  const perm = at('asks for permission');
  const files = at('files a little note');
  const collects = at('Dana collects');
  const better = at('next version gets better');
  return (
    <Stage tint={C.sky}>
      <SceneTag n={11} label="Feedback" />
      <Enter at={at('A user says')} from="left" x={90} y={440} dist={400}>
        <IPerson size={270} color={C.pink} />
      </Enter>
      <Pop at={at('this skill gave me')} x={90} y={200} style={{transformOrigin: 'left bottom'}}>
        <Bubble tail="left" size={40} color={C.white}>This skill gave me<br />a weird answer…</Bubble>
      </Pop>
      <Enter at={at('The agent asks')} from="bottom" x={560} y={440} dist={400}><Bot size={270} /></Enter>
      {frame < perm && <Pop at={which} x={560} y={250}><Bubble tail="left" size={38} color={C.sun}>Which skill?</Bubble></Pop>}
      <Pop at={perm} x={560} y={250}><Bubble tail="left" size={38} color={C.sun}>OK to send a note?</Bubble></Pop>
      <Pop at={perm + 14} x={380} y={720} rotate={-6}><Chip color={C.mint} size={32}>yes!</Chip></Pop>
      <Pop at={files - 8} x={960} y={400}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6}}><IFolder size={230} /><Chip color={C.white} size={26}><span style={{fontFamily: MONO}}>feedback/</span></Chip></div>
      </Pop>
      {[0, 1, 2].map((i) => (
        <Hop key={i} a={files + i * 8} b={files + 20 + i * 8} x1={760} y1={520} x2={1075} y2={510} height={140}><IDoc size={80} /></Hop>
      ))}
      <Enter at={collects} from="right" x={1520} y={230} dist={400}><Dana size={250} mood={frame >= better ? 'grin' : 'happy'} /></Enter>
      <Pop at={at('into a sheet')} x={1300} y={560}><ISheet size={240} /></Pop>
      {[0, 1, 2].map((i) => (
        <Hop key={i} a={at('into a sheet') + 6 + i * 6} b={at('into a sheet') + 24 + i * 6} x1={1075} y1={510} x2={1420} y2={680} height={120}><IDoc size={70} /></Hop>
      ))}
      <Pop at={better} x={1080} y={150} rotate={-6}><Chip color={C.mint} size={40}>next version: better ↑</Chip></Pop>
      <Pop at={better + 4} x={1700} y={170}><Float><ISparkle size={80} /></Float></Pop>
    </Stage>
  );
};

// ---------------------------------------------------------------- 12 safety

const SafeCard: React.FC<{color: string; icon: React.ReactNode; title: string; sub: string}> = ({color, icon, title, sub}) => (
  <Card color={C.white} style={{width: 790, height: 280, display: 'flex', alignItems: 'center', gap: 30}}>
    <div style={{width: 200, height: 200, borderRadius: 30, background: color, border: `5px solid ${C.ink}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{icon}</div>
    <div>
      <div style={{fontSize: 44, fontWeight: 700, lineHeight: 1.1}}>{title}</div>
      <div style={{fontSize: 30, fontWeight: 500, marginTop: 10, lineHeight: 1.25}}>{sub}</div>
    </div>
  </Card>
);

const Gardens: React.FC<{bounceAt: number}> = ({bounceAt}) => {
  const frame = useCurrentFrame();
  const t = frame - bounceAt;
  const px = t < 0 ? -40 : t < 12 ? -40 + t * 4 : t < 24 ? 8 - (t - 12) * 5 : -52;
  return (
    <svg width={170} height={170} viewBox="0 0 170 170">
      {[0, 1, 2].map((i) => (
        <g key={i} transform={`translate(${12 + i * 52} ${60})`}>
          <rect x={0} y={0} width={44} height={70} rx={6} fill={[C.mint, C.coral, C.sun][i]} stroke={C.ink} strokeWidth={4} />
          {[8, 22, 36].map((x) => <line key={x} x1={x} y1={-8} x2={x} y2={78} stroke={C.ink} strokeWidth={4} strokeLinecap="round" />)}
        </g>
      ))}
      <g transform={`translate(${70 + px} 10) rotate(30)`}><rect x={0} y={0} width={14} height={40} rx={3} fill={C.sun} stroke={C.ink} strokeWidth={3} /></g>
    </svg>
  );
};

export const Safety: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const fp = at('every single download');
  const dim = useSmooth(fp, 15);
  const keyT = frame - at('looks like a secret');
  const keyX = keyT < 0 ? 0 : keyT < 10 ? keyT * 4 : 40 - (keyT - 10) * 3;
  return (
    <Stage tint={C.grape}>
      <SceneTag n={12} label="Safe by design" />
      <Pop at={at('safe by design')} x={0} y={100} w={1920} style={{textAlign: 'center'}}>
        <div style={{display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 24}}><IShield size={100} /><Title size={88}>Safe by design</Title></div>
      </Pop>
      <div style={{position: 'absolute', inset: 0, opacity: 1 - dim * 0.75}}>
        <Pop at={at('walled garden')} x={130} y={260} rotate={-1}>
          <SafeCard color={C.mint} icon={<Gardens bounceAt={at('only write to their own')} />} title="Every package is its own garden" sub="Maintainers can write to their own package only" />
        </Pop>
        <Pop at={at('never replace the installer')} x={1000} y={260} rotate={1}>
          <SafeCard color={C.sky} icon={<div style={{position: 'relative'}}><IGear size={140} /><div style={{position: 'absolute', right: -24, bottom: -16}}><ILock size={80} /></div></div>} title="The installer is locked" sub="Only the framework ships it, never a content package" />
        </Pop>
        <Pop at={at('Scripts only work on local files')} x={130} y={600} rotate={1}>
          <SafeCard color={C.sun} icon={<div style={{position: 'relative'}}><ILaptop size={140} /><div style={{position: 'absolute', right: -30, top: -26}}><Pop at={at('never fetch data')} x={0} y={0} style={{position: 'relative'}}><ICross size={70} /></Pop></div></div>} title="Scripts stay local" sub="No fetching data, no holding credentials" />
        </Pop>
        <Pop at={at('a release refuses')} x={1000} y={600} rotate={-1}>
          <SafeCard color={C.pink} icon={<div style={{display: 'flex', alignItems: 'center'}}><div style={{transform: `translateX(${keyX}px)`}}><IKey size={80} /></div><IZip size={100} /></div>} title="Secrets get refused" sub="A release with anything password-like won't build" />
        </Pop>
      </div>
      <Pop at={fp} x={760} y={330}><IFinger size={400} /></Pop>
      <Stamp at={at('fingerprint checked')} text="CHECKED" color={C.mint} x={960} y={540} size={110} rotate={-12} />
    </Stage>
  );
};

// ---------------------------------------------------------------- 13 outro

export const Outro: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const stays = at('Dana stays');
  const team = at('whole team');
  const final = at('Your expertise');
  const recap: [string, string, React.ReactNode, string][] = [
    ['Three layers', 'Three layers', <IGear key="1" size={90} />, C.grape],
    ['Shared drives', 'Shared drives you have', <IFolder key="2" size={90} />, C.sun],
    ['One sentence to install', 'One sentence to install', <ILaptop key="3" size={90} />, C.sky],
    ['Updates that check', 'Self-checking updates', <IFinger key="4" size={90} />, C.teal],
    ['Publishing by asking', 'Publish by asking', <IInbox key="5" size={90} />, C.pink],
    ['reviews with everything', 'Reviews on one page', <IMagnifier key="6" size={90} />, C.mint],
  ];
  const people = [C.pink, C.sky, C.sun, C.grape];
  return (
    <Stage tint={C.coral}>
      <Exit at={stays - 4}>
        <Pop at={at('to recap')} x={0} y={100} w={1920} style={{textAlign: 'center'}}><Title size={96}>Recap!</Title></Pop>
        {recap.map(([cue, label, icon, color], i) => (
          <Pop key={cue} at={at(cue)} x={120 + (i % 3) * 570} y={290 + Math.floor(i / 3) * 270} rotate={[-2, 2, -1, 1, -2, 2][i]}>
            <Card color={C.white} style={{width: 520, height: 200, display: 'flex', alignItems: 'center', gap: 22}}>
              <div style={{width: 130, height: 130, borderRadius: 26, background: color, border: `5px solid ${C.ink}`, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{icon}</div>
              <div style={{fontSize: 40, fontWeight: 700, lineHeight: 1.1}}>{label}</div>
            </Card>
          </Pop>
        ))}
      </Exit>
      <Exit at={final - 4}>
        <Enter at={stays} from="bottom" x={300} y={330} dist={500}><Dana size={300} mood="grin" /></Enter>
        <Pop at={at('irrigation expert')} x={280} y={230} rotate={-5}><Chip color={C.sun} size={34}>still an irrigation expert</Chip></Pop>
        {people.map((c, i) => (
          <Pop key={c} at={team + i * 4} x={1000 + i * 210} y={420}><Float phase={i}><IPerson size={170} color={c} /></Float></Pop>
        ))}
        {people.map((c, i) => (
          <Hop key={c} a={at('best tricks') + i * 5} b={at('best tricks') + 22 + i * 5} x1={500} y1={480} x2={1085 + i * 210} y2={380} height={150}>
            <ISparkle size={60} color={[C.mint, C.sun, C.pink, C.sky][i]} />
          </Hop>
        ))}
      </Exit>
      <Pop at={final} x={0} y={170} w={1920} style={{textAlign: 'center'}}><Title size={130}>Your expertise,</Title></Pop>
      <Pop at={at('one sentence away')} x={0} y={340} w={1920} style={{textAlign: 'center'}}>
        <Title size={90} color={C.coral}>one sentence away from<br />everyone’s agent.</Title>
      </Pop>
      <Enter at={final + 10} from="left" x={180} y={600} dist={500}><Dana size={260} mood="grin" wave /></Enter>
      <Enter at={final + 16} from="right" x={1480} y={620} dist={500}><Bot size={250} /></Enter>
      <Confetti at={at("everyone's agent")} x={960} y={400} count={90} spread={1100} />
      <Confetti at={at("everyone's agent") + 40} x={500} y={300} count={50} />
      <Confetti at={at("everyone's agent") + 70} x={1400} y={300} count={50} />
    </Stage>
  );
};
