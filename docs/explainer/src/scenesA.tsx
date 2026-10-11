import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {
  Agent, C, Code, Col, Fade, FileTree, H, Heading, Line, MONO, Mark, P, Persona, Rise, SANS, Say, Sheet, Stage, Status, Tag,
  Terminal, Travel, Typed, useAfter, useAt, useReveal,
} from './kit';

const Abs: React.FC<{x: number; y: number; children: React.ReactNode; style?: React.CSSProperties}> = ({x, y, children, style}) => (
  <div style={{position: 'absolute', left: x, top: y, ...style}}>{children}</div>
);

// ---------------------------------------------------------------- title

/** A short arrow that draws itself, laid out inline in a flex row (unlike Line, which uses stage coordinates). */
const InlineArrow: React.FC<{at: number; dashed?: boolean; w?: number}> = ({at, dashed = false, w = 90}) => {
  const p = useReveal(at, 12);
  return (
    <svg width={w} height={24} viewBox={`0 0 ${w} 24`} style={{flexShrink: 0, opacity: p}}>
      <path d={`M2 12 H${w - 14}`} stroke={C.ink3} strokeWidth={3} strokeLinecap="round" strokeDasharray={dashed ? '8 10' : undefined}
        style={{clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`}} />
      {p > 0.95 && <path d={`M${w - 22} 5 L${w - 12} 12 L${w - 22} 19`} fill="none" stroke={C.ink3} strokeWidth={3} strokeLinecap="round" strokeLinejoin="round" />}
    </svg>
  );
};

export const TitleScene: React.FC = () => {
  const frame = useCurrentFrame();
  const rule = interpolate(frame, [4, 30], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <Stage>
      <Abs x={80} y={330}>
        <div style={{height: 4, width: 1760 * rule, background: C.blue}} />
      </Abs>
      <Rise at={8} x={80} y={278}><Tag mono size={24}>Skills Hub</Tag></Rise>
      <Rise at={14} x={80} y={370}><H size={110}>Simple Skills Sharing</H></Rise>
      <Rise at={30} x={80} y={520} w={1300}>
        <P size={38}>How an organization shares agent skills through Google Drive: get them, stay current, and contribute back, by asking your agent.</P>
      </Rise>
      <Rise at={48} x={80} y={700}>
        <div style={{display: 'flex', gap: 44, alignItems: 'center'}}>
          <Persona initials="D" name="Dana" role="Demand planner, supply chain" />
          <InlineArrow at={64} />
          <Agent size={100} />
          <InlineArrow at={76} dashed />
          <DriveHub size={84} label="Google Drive" />
        </div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 01 intro

export const Intro: React.FC = () => {
  const at = useAt();
  const share = at('The question is');
  const skills: [string, string, string][] = [
    ['stock exports', 'stock-readout', 'Reads the warehouse stock exports'],
    ['lead times', 'lead-times', 'Which supplier lead times to trust'],
    ['weekly replenishment brief', 'weekly-brief', 'The brief in the format the team expects'],
  ];
  const groups = ['planning', 'finance', 'stores', 'marketing', 'customer care', 'data platform'];
  return (
    <Stage>
      <Heading n={1} title="An expert and her skills" />
      <Rise at={at('Meet Dana')} x={80} y={220}><Persona initials="D" name="Dana" role={<>Demand planner<br />supply chain group</> as unknown as string} size={150} /></Rise>
      <Fade at={share - 12}>
        <Rise at={at('taught her AI agent')} x={90} y={470}><Agent size={130} /></Rise>
        <Line at={at('only she knows')} points={[[155, 395], [155, 460]]} color={C.ink3} dur={10} />
        {skills.map(([cue, name, note], i) => (
          <Rise key={name} at={at(cue)} x={520} y={220 + i * 150} w={900}>
            <Sheet pad={18} style={{display: 'flex', alignItems: 'center', gap: 24}}>
              <Tag mono size={26}>{name}</Tag>
              <P size={26}>{note}</P>
            </Sheet>
          </Rise>
        ))}
        <Rise at={at('These are skills')} x={520} y={690} w={900}>
          <P size={30} color={C.ink}>A <Mark at={at('These are skills', 8)}>skill</Mark> is a small package of know-how: one question in, one reliable answer out.</P>
        </Rise>
      </Fade>
      <Rise at={share} x={520} y={220} w={1300}>
        <P size={30} color={C.ink}>How does this reach the whole organization?</P>
      </Rise>
      <Rise at={at('whole organization')} x={520} y={310} w={1300}>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 400px)', gap: 20}}>
          {groups.map((g, i) => (
            <Rise key={g} at={at('whole organization') + i * 4} x={0} y={0} style={{position: 'relative'}}>
              <Sheet pad={16} style={{display: 'flex', alignItems: 'center', gap: 16}}>
                <Agent size={44} label="" />
                <P size={26} color={C.ink}>{g}</P>
              </Sheet>
            </Rise>
          ))}
        </div>
      </Rise>
      <Rise at={at('without becoming')} x={520} y={720} w={1300}>
        <div style={{display: 'flex', gap: 18, alignItems: 'center'}}>
          <P size={28}>Without</P>
          {['git clone', 'git rebase', 'pull request', 'CI'].map((t, i) => (
            <Rise key={t} at={at('software engineer') + i * 4} x={0} y={0} style={{position: 'relative'}}>
              <Tag mono bg={C.redSoft} color={C.red} size={24} style={{textDecoration: 'line-through'}}>{t}</Tag>
            </Rise>
          ))}
        </div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 02 idea

/** Google Drive as a hub: a triangle mark with the label beside it. */
export const DriveHub: React.FC<{size?: number; label?: string}> = ({size = 64, label}) => (
  <div style={{display: 'flex', alignItems: 'center', gap: size * 0.3, fontFamily: SANS}}>
    <svg width={size} height={size} viewBox="0 0 64 64">
      <path d="M22 8 H42 L62 42 L52 58 H12 L2 42 Z" fill={C.blueSoft} stroke={C.ink} strokeWidth={2.5} strokeLinejoin="round" />
      <path d="M22 8 L2 42 M42 8 L62 42 M12 58 L32 24 L52 58" fill="none" stroke={C.ink} strokeWidth={2.5} strokeLinejoin="round" />
    </svg>
    {label && <div style={{fontSize: size * 0.42, fontWeight: 600, color: C.ink, lineHeight: 1.1}}>{label}</div>}
  </div>
);

export const Idea: React.FC = () => {
  const at = useAt();
  const hub = at('Google Drive is the hub');
  const turns: [string, string, string][] = [
    ['Installing', 'Install the planning package.', 'install.py --package planning --sha256 9f2c…e71'],
    ['Updating', 'Anything new?', 'sync.py  →  planning 0.4.0 → 0.5.0'],
    ['Submitting a change', 'Publish my change to weekly-brief.', 'publish.py --skill weekly-brief --rationale "…"'],
    ['Sending feedback', 'That answer looked wrong.', 'feedback.py --skill weekly-brief'],
  ];
  const hosts: [string, string, string, string][] = [
    ['Claude Code', 'claude.ai Drive connector', 'plugin marketplace at ~/.skills-hub', 'uv run --script'],
    ['Cursor', 'remote Google Drive MCP', 'one symlink per package', 'uv run --script'],
    ['Claude Science', 'claude.ai Drive connector', 'skills published via host.skills', 'manage_packages, then python'],
  ];
  return (
    <Stage>
      <Heading n={2} title="Everything goes through the agent" />
      <Fade at={hub - 12}>
        <Rise at={at('The answer is')} x={80} y={190}><Persona initials="D" name="Dana" size={90} /></Rise>
        <Rise at={at('The answer is')} x={1690} y={180}><Agent size={100} /></Rise>
        <Rise at={at('Skills Hub')} x={1560} y={330}><Tag mono size={22}>Skills Hub</Tag></Rise>
        {turns.map(([cue, ask, cmd], i) => (
          <React.Fragment key={cue}>
            <Rise at={at(cue)} x={380} y={190 + i * 150}><Say who="person" size={28}>{ask}</Say></Rise>
            <Rise at={at(cue, 10)} x={760} y={255 + i * 150}>
              <Say who="agent" size={22}><span style={{fontFamily: MONO, color: C.ink2}}>{cmd}</span></Say>
            </Rise>
          </React.Fragment>
        ))}
        <Rise at={at('plain language')} x={380} y={800} w={1200}>
          <P size={28}>You speak; the agent runs the tooling under <span style={{fontFamily: MONO}}>~/.skills-hub/framework/current/tools/</span>.</P>
        </Rise>
      </Fade>
      <Rise at={hub} x={560} y={180} w={800}>
        <Sheet pad={20} tone={C.blueSoft} style={{border: 'none', display: 'flex', alignItems: 'center', gap: 24, justifyContent: 'center'}}>
          <DriveHub size={72} label="Google Drive" />
          <P size={24}>the hub, behind the organization's SSO</P>
        </Sheet>
      </Rise>
      {hosts.map(([h], i) => (
        <Line key={h} at={at(h)} points={[[960, 300], [960, 360], [350 + i * 580, 360], [350 + i * 580, 440]]} color={C.ink3} arrow dur={14} />
      ))}
      {hosts.map(([h, transport, how, run], i) => (
        <Rise key={h} at={at(h)} x={80 + i * 580} y={440} w={540}>
          <Sheet pad={28}>
            <H size={40}>{h}</H>
            <P size={24} style={{marginTop: 16, color: C.ink}}>{transport}</P>
            <P size={24} style={{marginTop: 8}}>{how}</P>
            <P size={22} mono style={{marginTop: 10, color: C.ink3}}>{run}</P>
          </Sheet>
        </Rise>
      ))}
      <Rise at={at('on Mac')} x={80} y={760}>
        <div style={{display: 'flex', gap: 16, alignItems: 'center'}}>
          <P size={26}>Same tooling on</P>
          {['macOS', 'Windows', 'Linux'].map((os, i) => (
            <Rise key={os} at={at(['Mac', 'Windows', 'Linux'][i])} x={0} y={0} style={{position: 'relative'}}><Tag size={26}>{os}</Tag></Rise>
          ))}
        </div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 03 layers

const Band: React.FC<{at: number; y: number; h: number; x: number; w: number; tone: string; title: string; children?: React.ReactNode; version: string; flipAt?: number; newVersion?: string; titleW?: number}> = ({at, y, h, x, w, tone, title, children, version, flipAt, newVersion, titleW = 220}) => {
  const p = useReveal(at, 18);
  const flipped = flipAt !== undefined && useAfter(flipAt);
  return (
    <div style={{position: 'absolute', left: x, top: y + (1 - p) * 16, width: w, height: h, opacity: p, background: tone, border: `1.5px solid ${C.ink}`, borderRadius: 8, padding: '18px 26px', boxSizing: 'border-box', display: 'flex', alignItems: 'center', gap: 30}}>
      <H size={34} style={{width: titleW}}>{title}</H>
      <div style={{flex: 1}}>{children}</div>
      <Tag mono size={22} bg={flipped ? C.blue : C.sheet} color={flipped ? '#fff' : C.ink2} style={{border: `1.5px solid ${flipped ? C.blue : C.rule}`}}>{flipped && newVersion ? newVersion : version}</Tag>
    </div>
  );
};

export const Layers: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const X = 80, W = 1180;
  const release = at('releases on its own');
  const shared = at('shared ground');
  const domains = ['planning', 'finance', 'stores'];
  const extend = at('extend that foundation');
  return (
    <Stage>
      <Heading n={3} title="Three layers" />
      <Band at={at('Skills Hub itself')} x={X} y={700} h={130} w={W} tone={C.violetSoft} title="Skills Hub" version="1.4.0">
        <P size={22} color={C.ink2}>the framework</P>
        <P size={24} mono color={C.ink2}>install.py  sync.py  publish.py  feedback.py  doctor.py</P>
      </Band>
      <Band at={at('foundation package')} x={X} y={480} h={180} w={W} tone={C.blueSoft} title="Foundation" version="0.9.2">
        <div style={{display: 'flex', gap: 14, flexWrap: 'wrap'}}>
          {[['data sources', 'its data sources'], ['vocabulary', 'its vocabulary'], ['internal systems', 'its internal systems']].map(([label, cue]) => (
            <Rise key={label} at={at(cue)} x={0} y={0} style={{position: 'relative'}}><Tag size={24} bg={C.sheet} style={{border: `1.5px solid ${C.rule}`}}>{label}</Tag></Rise>
          ))}
        </div>
        <Rise at={at('same understanding')} x={0} y={0} style={{position: 'relative', marginTop: 12}}>
          <P size={22}>Installed by everyone. Every agent starts from the same understanding of the organization.</P>
        </Rise>
      </Band>
      {domains.map((d, i) => (
        <Band key={d} at={extend + i * 6} x={X + i * 400} y={300} h={130} w={380} tone={C.greenSoft} title={d} titleW={160} version={i === 0 ? '0.4.0' : i === 1 ? '1.1.0' : '0.2.3'} flipAt={i === 0 ? release + 12 : undefined} newVersion="0.5.0">
          <P size={19} color={C.ink3}>{i === 0 ? 'Dana, Sam' : i === 1 ? 'finance team' : 'store ops team'}</P>
        </Band>
      ))}
      <Line at={extend + 20} points={[[X + 190, 430], [X + 190, 480]]} color={C.ink3} arrow dur={10} />
      <Line at={extend + 24} points={[[X + 590, 430], [X + 590, 480]]} color={C.ink3} arrow dur={10} />
      <Line at={extend + 28} points={[[X + 990, 430], [X + 990, 480]]} color={C.ink3} arrow dur={10} />
      <Rise at={at('Skills travel')} x={1330} y={190} w={510}>
        <P size={26}>Every layer is a package: a zip with a manifest, one version, its own release.</P>
      </Rise>
      <Rise at={at('maintained by the experts')} x={1330} y={300} w={510}>
        <Sheet pad={20} tab="package.json">
          <Code at={at('maintained by the experts')} size={20} lines={[
            {text: '{'},
            {text: '  "package": "planning",'},
            {text: '  "title": "Planning",'},
            {text: '  "maintainers": ["dana@org","sam@org"],'},
            {text: '  "version": "0.5.0"', hi: frame >= release + 12 ? C.blueSoft : undefined},
            {text: '}'},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={release} x={1330} y={560} w={510}>
        <P size={26} color={C.ink}>A planning release rebuilds only planning. The foundation and Skills Hub stay as they are.</P>
      </Rise>
      <Rise at={release + 8} x={1330} y={680}>
        <div style={{display: 'flex', flexDirection: 'column', gap: 10}}>
          {['planning 0.4.0 → 0.5.0', 'foundation 0.9.2 unchanged', 'skills-hub 1.4.0 unchanged'].map((t, i) => (
            <Rise key={t} at={release + 8 + i * 4} x={0} y={0} style={{position: 'relative', display: 'flex', gap: 12, alignItems: 'center'}}>
              <Status kind={i === 0 ? 'ok' : 'off'} size={24} /><P size={24} mono>{t}</P>
            </Rise>
          ))}
        </div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 04 anatomy

export const Anatomy: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const hi = (cue: string) => (frame >= at(cue) ? C.blueSoft : undefined);
  const scripts = at('Scripts are optional');
  return (
    <Stage>
      <Heading n={4} title="A skill is a folder" />
      <Rise at={at('a skill is just a folder')} x={80} y={200} w={820}>
        <Sheet pad={28} tab="skills/weekly-brief/">
          <FileTree at={at('a skill is just a folder')} size={26} rows={[
            {d: 0, name: 'SKILL.md', note: 'when to use it, and how', hi: hi('A short instruction file'), at: at('A short instruction file')},
            {d: 0, name: 'examples', dir: true, hi: hi('worked example'), at: at('worked example')},
            {d: 1, name: 'run.md', note: 'question, steps, expected answer', at: at('shows a question')},
            {d: 0, name: 'CHANGES.md', note: 'a dated entry per submission', hi: hi('change log'), at: at('change log')},
            {d: 0, name: 'scripts', dir: true, note: 'optional', hi: hi('Scripts are optional'), at: scripts},
            {d: 1, name: 'brief.py', at: scripts + 4},
            {d: 0, name: 'tests', dir: true, note: 'optional', at: scripts + 8},
            {d: 1, name: 'test_brief.py', at: scripts + 12},
            {d: 0, name: 'submission.json', note: 'written by publish', at: scripts + 16},
          ]} />
        </Sheet>
      </Rise>
      <Fade at={scripts - 4}>
        <Rise at={at('A short instruction file')} x={980} y={200} w={860}>
          <Sheet pad={24} tab="SKILL.md" tone="#FBFCFE">
            <Code at={at('A short instruction file')} size={22} lines={[
              {text: '---', color: C.ink3},
              {text: 'name: weekly-brief'},
              {text: 'description: "Use when asked to write the weekly'},
              {text: '  replenishment brief for the supply chain group."'},
              {text: 'owner: dana@org'},
              {text: 'data_sources: stock exports (Drive)'},
              {text: '---', color: C.ink3},
              {text: ''},
              {text: "Read the week's stock export. Produce the", at: at('how') + 4},
              {text: 'four-part brief: demand, stock, orders, risks.', at: at('how') + 7},
            ]} />
          </Sheet>
        </Rise>
        <Rise at={at('worked example')} x={980} y={610} w={860}>
          <Sheet pad={24} tab="examples/run.md" tone="#FBFCFE">
            <Code at={at('worked example')} size={22} lines={[
              {text: 'Question: weekly brief for week 41'},
              {text: 'Steps: open the export, apply the four-part format', at: at('the steps')},
              {text: 'Answer: Demand: … Stock: 412 lines below target …', at: at('expected answer')},
            ]} />
          </Sheet>
        </Rise>
      </Fade>
      <Rise at={scripts} x={980} y={200} w={860}>
        <Sheet pad={24} tab="scripts/brief.py" tone="#FBFCFE">
          <Code at={scripts} size={22} lines={[
            {text: '# /// script', color: C.ink3},
            {text: '# dependencies = ["pandas==2.2.2"]', color: C.ink3},
            {text: '# ///', color: C.ink3},
            {text: 'import sys, json'},
            {text: 'week = json.load(sys.stdin)   # input in', at: at('read local files')},
            {text: 'print(brief(week))            # result out', at: at('print a result')},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={at('read local files')} x={980} y={520}>
        <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
          <Tag mono size={22}>stdin / files</Tag>
          <div style={{width: 90}} />
          <Tag mono size={22}>script</Tag>
          <div style={{width: 90}} />
          <Tag mono size={22}>stdout</Tag>
        </div>
      </Rise>
      {/* Lines use stage coordinates, so they sit outside the positioned Rise above. */}
      <Line at={at('read local files') + 6} points={[[1192, 538], [1288, 538]]} arrow dur={8} />
      <Line at={at('print a result')} points={[[1422, 538], [1518, 538]]} arrow dur={8} />
      <Rise at={at('never fetch data')} x={980} y={630}>
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}><Status kind="block" /><P size={26} color={C.ink}>No network. Data access stays in the host's connectors, behind SSO.</P></div>
      </Rise>
      <Rise at={at('never hold credentials')} x={980} y={700}>
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}><Status kind="block" /><P size={26} color={C.ink}>No credentials. Release and install refuse credential-like files.</P></div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 05 drive

export const DriveScene: React.FC = () => {
  const at = useAt();
  const pub = at('published drive');
  const sub = at('submissions drive');
  const own = at('Skills Hub has');
  return (
    <Stage>
      <Heading n={5} title="Where packages live" />
      <Rise at={at('Google Shared Drives')} x={80} y={200} w={820}>
        <Sheet pad={28} tab="Google Shared Drives">
          <FileTree at={at('Google Shared Drives')} size={24} rows={[
            {d: 0, name: 'planning — Published', dir: true, at: at('Each package'), hi: C.blueSoft},
            {d: 1, name: 'START HERE', at: pub + 3},
            {d: 1, name: 'current.json', at: pub + 6},
            {d: 1, name: 'releases/planning-0.5.0.zip', at: pub + 9},
            {d: 0, name: 'planning — Submissions', dir: true, at: sub, hi: C.amberSoft},
            {d: 1, name: 'inbox/', at: sub + 3},
            {d: 1, name: 'accepted/   rejected/', at: sub + 6},
            {d: 1, name: 'feedback/', at: sub + 9},
            {d: 0, name: 'Skills Hub — Published', dir: true, at: own, hi: C.violetSoft},
            {d: 1, name: 'START HERE', note: 'Google Doc', at: at('START HERE')},
            {d: 1, name: 'current.json', at: at('START HERE') + 4},
            {d: 1, name: 'releases/skills-hub-1.4.0.zip', at: at('START HERE') + 8},
            {d: 1, name: 'index.json', note: 'every registered package', at: at('index of every')},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={at('single sign-on')} x={980} y={200} w={860}>
        <Sheet pad={24}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}>
            <svg width={40} height={40} viewBox="0 0 40 40"><rect x={8} y={17} width={24} height={18} rx={4} fill={C.ink} /><path d="M13 17 V12 a7 7 0 0 1 14 0 V17" fill="none" stroke={C.ink} strokeWidth={3.5} /></svg>
            <P size={26} color={C.ink}>Access is the organization's single sign-on. Nothing to provision.</P>
          </div>
        </Sheet>
      </Rise>
      <Rise at={pub} x={980} y={360} w={860}>
        <div style={{display: 'flex', gap: 14, alignItems: 'center'}}><Tag size={24} bg={C.blueSoft}>Published</Tag><P size={26}>everyone reads. Maintainers of that package write.</P></div>
      </Rise>
      <Rise at={sub} x={980} y={430} w={860}>
        <div style={{display: 'flex', gap: 14, alignItems: 'center'}}><Tag size={24} bg={C.amberSoft}>Submissions</Tag><P size={26}>authors contribute. Maintainers review.</P></div>
      </Rise>
      <Rise at={own} x={980} y={500} w={860}>
        <div style={{display: 'flex', gap: 14, alignItems: 'center'}}><Tag size={24} bg={C.violetSoft}>Skills Hub</Tag><P size={26}>where a new user starts, and the index of every package.</P></div>
      </Rise>
      <Rise at={at('Nothing new to provision')} x={980} y={600} w={860}>
        <div style={{display: 'flex', gap: 14}}>
          {['No servers', 'No buckets', 'No GitHub'].map((t, i) => (
            <Rise key={t} at={at('Nothing new to provision') + i * 5} x={0} y={0} style={{position: 'relative'}}><Tag size={24} bg={C.sheet} style={{border: `1.5px solid ${C.rule}`}}>{t}</Tag></Rise>
          ))}
        </div>
      </Rise>
      <Rise at={at('the agent already knows')} x={980} y={700}>
        <div style={{display: 'flex', alignItems: 'center', gap: 30}}>
          <Agent size={90} />
          <div style={{width: 200}} />
          <Sheet pad={16}><P size={22} mono color={C.ink}>Drive connector<br />download_file_content(id)</P></Sheet>
        </div>
      </Rise>
      <Line at={at('talk to Drive')} points={[[1090, 745], [1280, 745]]} arrow dashed dur={14} />
    </Stage>
  );
};

// ---------------------------------------------------------------- 06 quick start

const Step: React.FC<{at: number; n: number; title: string; x: number; y: number; w: number; children?: React.ReactNode}> = ({at, n, title, x, y, w, children}) => (
  <Rise at={at} x={x} y={y} w={w}>
    <div style={{display: 'flex', gap: 22, alignItems: 'flex-start'}}>
      <div style={{width: 52, height: 52, borderRadius: '50%', background: C.blue, color: '#fff', fontFamily: SANS, fontWeight: 600, fontSize: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{n}</div>
      <div style={{flex: 1}}>
        <H size={34}>{title}</H>
        <div style={{marginTop: 14}}>{children}</div>
      </div>
    </div>
  </Rise>
);

export const QuickStart: React.FC = () => {
  const at = useAt();
  const two = at('Two: tell');
  const three = at('Three: ask');
  return (
    <Stage>
      <Heading n={6} title="Quick start" />
      <Step at={at('One: connect')} n={1} title="Connect Google Drive in your host" x={80} y={190} w={800}>
        <P size={24}>Claude Code, Cursor, or Claude Science. The connector is the only transport.</P>
      </Step>
      <Step at={two} n={2} title="Tell your agent" x={80} y={360} w={800}>
        <Say who="person" size={26} width={720}>Read the START HERE doc on the Skills Hub drive and follow it.</Say>
        <Rise at={at('The agent installs')} x={0} y={0} style={{position: 'relative', marginTop: 18}}>
          <P size={24}>The agent installs Skills Hub, then the foundation package and the domain packages you name.</P>
        </Rise>
      </Step>
      <Step at={three} n={3} title="Ask for doctor" x={80} y={700} w={800}>
        <Say who="person" size={26}>Run doctor and tell me what's installed.</Say>
      </Step>
      <Rise at={at('The agent installs')} x={960} y={190} w={880}>
        <Terminal at={at('The agent installs')} width={880} size={21} title="what the agent runs" command="python ~/.skills-hub/framework/current/tools/install.py --package planning --sha256 9f2c…e71 --bytes 184320 --version 0.5.0 --current-file-id 1AbC… --from-tool-result planning-0.5.0.json" output={[
          {text: 'verified sha256 9f2c…e71  184320 bytes', color: '#7CE0A3', at: at('fingerprint')},
          {text: 'staging → current  planning 0.5.0', at: at('fingerprint') + 5},
          {text: 'state.json updated', at: at('fingerprint') + 9},
        ]} />
      </Rise>
      <Rise at={three} x={960} y={520} w={880}>
        <Terminal at={three} width={880} size={21} title="doctor" command="python ~/.skills-hub/framework/current/tools/doctor.py" output={[
          {text: 'skills-hub: 1.4.0 maintainers platform@org', at: at('every installed version')},
          {text: 'package foundation 0.9.2 maintainers platform@org', at: at('every installed version') + 4},
          {text: 'package planning 0.5.0 maintainers dana@org, sam@org', at: at('every installed version') + 8},
          {text: 'ok', color: '#7CE0A3', at: at('needs attention')},
        ]} />
      </Rise>
      <Rise at={at('From then on')} x={960} y={880} w={880}>
        <P size={26} color={C.ink}>From here on, the organization's skills are in your agent.</P>
      </Rise>
    </Stage>
  );
};

export {Abs};
