import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {
  Arrow, Bot, Bubble, C, Card, Chip, Confetti, Dana, Enter, Exit, Float, Hop, IBucket, ICheck, IClock, ICross, IDoc,
  IFinger, IFolder, IInbox, ILaptop, ILock, IPencil, IRepo, IServer, IShield, ISparkle, IZip, MONO, Pop, SceneTag,
  Stage, Stamp, Title, useAt, usePop, useSmooth, useWiggle,
} from './kit';
import {Abs, SkillCard} from './scenes1';

// ---------------------------------------------------------------- 05 drive

export const DriveScene: React.FC = () => {
  const at = useAt();
  const move = useSmooth(at("That's it", 10), 20);
  const folderX = interpolate(move, [0, 1], [760, 300]);
  const sso = at('single sign-on');
  const nos: [string, React.ReactNode, string][] = [
    ['No servers', <IServer key="s" size={120} />, 'servers'],
    ['No cloud buckets', <IBucket key="b" size={120} />, 'cloud buckets'],
    ['No GitHub accounts', <IRepo key="r" size={120} />, 'GitHub accounts'],
  ];
  return (
    <Stage tint={C.sun}>
      <SceneTag n={5} label="Where it lives" />
      <Pop at={at('where do packages live')} x={0} y={110} w={1920} style={{textAlign: 'center'}}>
        <Title size={84}>Where do packages live?</Title>
      </Pop>
      <Abs x={folderX} y={260}>
        <Pop at={at('Google Shared Drives')} x={0} y={0}>
          <Float amp={6}><IFolder size={400} /></Float>
          <div style={{position: 'absolute', left: 40, top: 400, width: 340, textAlign: 'center'}}>
            <Chip color={C.white} size={36}>Google Shared Drive</Chip>
          </div>
          <Pop at={sso} x={250} y={170}><ILock size={150} /></Pop>
          <Pop at={sso + 8} x={250} y={110} rotate={10}><Chip color={C.coral} size={30}>SSO</Chip></Pop>
        </Pop>
      </Abs>
      <Pop at={at("That's it")} x={folderX - 60} y={240}><Float><ISparkle size={90} /></Float></Pop>
      <Pop at={at("That's it", 5)} x={folderX + 380} y={300}><Float phase={1}><ISparkle size={70} color={C.pink} /></Float></Pop>
      <Exit at={sso - 4}>
        {nos.map(([cue, icon, label], i) => (
          <React.Fragment key={cue}>
            <Pop at={at(cue)} x={900 + i * 330} y={380}>
              <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 16, width: 260}}>
                {icon}
                <Chip color={C.white} size={30}>{label}</Chip>
              </div>
            </Pop>
            <Pop at={at(cue, 10)} x={1060 + i * 330} y={330}><ICross size={90} /></Pop>
          </React.Fragment>
        ))}
      </Exit>
      <Pop at={at('guards the door')} x={900} y={330}><Bubble tail="none" size={40} color={C.white}>Your login already<br />guards the door</Bubble></Pop>
      <Enter at={at('your agent already knows')} from="right" x={1500} y={480} dist={500}><Bot size={240} /></Enter>
      <Arrow at={at('talk to Drive')} x1={1500} y1={640} x2={760} y2={560} bend={-0.15} />
      <Pop at={at('talk to Drive', 10)} x={1000} y={690}><Chip color={C.mint} size={30}>Drive connector</Chip></Pop>
    </Stage>
  );
};

// ---------------------------------------------------------------- 06 install

export const Install: React.FC = () => {
  const at = useAt();
  const steps: [string, React.ReactNode, string][] = [
    ['downloads', <IZip key="z" size={120} />, 'Download'],
    ['checks it', <IFinger key="f" size={120} />, 'Check'],
    ['unpacks it', <IFolder key="o" size={120} />, 'Unpack'],
    ['installs the packages', <ILaptop key="l" size={120} />, 'Install'],
  ];
  return (
    <Stage tint={C.mint}>
      <SceneTag n={6} label="Install" />
      <Pop at={at('one sentence')} x={0} y={110} w={1920} style={{textAlign: 'center'}}>
        <Title size={90}>One <span style={{color: C.coral}}>sentence</span> to install</Title>
      </Pop>
      <Enter at={at('Dana tells')} from="left" x={70} y={330} dist={400}><Dana size={250} /></Enter>
      <Pop at={at('read the START HERE')} x={330} y={250} style={{transformOrigin: 'left bottom'}}>
        <Bubble tail="left" size={44} color={C.sun}>“Read the START HERE doc,<br />and follow it.”</Bubble>
      </Pop>
      <Enter at={at('The agent downloads')} from="right" x={1620} y={300} dist={400}><Bot size={210} /></Enter>
      {steps.map(([cue, icon, label], i) => (
        <React.Fragment key={cue}>
          <Pop at={at(cue)} x={330 + i * 330} y={560}>
            <Card color={C.white} style={{width: 250, height: 250, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12}}>
              {icon}
              <div style={{fontSize: 38, fontWeight: 700}}>{label}</div>
            </Card>
          </Pop>
          {i < 3 && <Arrow at={at(steps[i + 1][0]) - 8} x1={600 + i * 330} y1={690} x2={650 + i * 330} y2={690} dur={8} />}
        </React.Fragment>
      ))}
      <Pop at={at('One time')} x={880} y={860} rotate={-4}><Chip color={C.white} size={36}>one time</Chip></Pop>
      <Stamp at={at('Done')} text="DONE!" color={C.mint} x={1180} y={440} size={110} rotate={-10} />
      <Confetti at={at('Done')} x={1180} y={440} count={50} />
    </Stage>
  );
};

// ---------------------------------------------------------------- 07 sync

const FingerCompare: React.FC<{at: number; ok: boolean; result: number}> = ({at, ok, result}) => {
  const frame = useCurrentFrame();
  const scan = interpolate(frame, [at, result], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const done = frame >= result;
  const tint = done ? (ok ? C.mint : C.coral) : C.teal;
  const shake = useWiggle(result, ok ? 0 : 14, 24);
  return (
    <div style={{display: 'flex', alignItems: 'center', gap: 30, transform: `translateX(${shake}px)`}}>
      {['expected', 'downloaded'].map((label, i) => (
        <div key={label} style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, position: 'relative'}}>
          <IFinger size={170} color={i === 1 ? tint : done ? tint : C.teal} />
          {!done && <div style={{position: 'absolute', left: -10, right: -10, top: 10 + scan * 150, height: 8, background: C.coral, borderRadius: 4, opacity: 0.85}} />}
          <Chip color={C.white} size={26}>{label}</Chip>
        </div>
      ))}
      <div style={{width: 110}}>{done && (ok ? <ICheck size={110} /> : <ICross size={110} />)}</div>
    </div>
  );
};

export const Sync: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const download = at('downloads the new release');
  const check = at('checks that fingerprint');
  const swap = at('swap in');
  const off = at('If anything is off');
  const nudge = at('more than a day');
  const swapT = useSmooth(swap, 20);
  return (
    <Stage tint={C.teal}>
      <SceneTag n={7} label="Staying up to date" />
      <Exit at={nudge - 4}>
        <Enter at={at('one tiny pointer file')} from="left" x={110} y={170} dist={600}>
          <Card color={C.paper} style={{width: 720, fontFamily: MONO, fontSize: 32, lineHeight: 1.7}}>
            <div style={{fontFamily: 'inherit', fontWeight: 700, fontSize: 30, marginBottom: 8, display: 'flex', alignItems: 'center', gap: 12}}>
              <IDoc size={50} /> current.json
            </div>
            <div>{'{'}</div>
            <Pop at={at('the latest version')} x={0} y={0} style={{position: 'relative', transformOrigin: 'left center'}}>
              <div style={{paddingLeft: 30, background: frame >= at('the latest version') && frame < at('fingerprint') + 20 ? `${C.sun}88` : 'transparent', borderRadius: 8}}>"version": "0.5.0",</div>
            </Pop>
            <Pop at={at('fingerprint')} x={0} y={0} style={{position: 'relative', transformOrigin: 'left center'}}>
              <div style={{paddingLeft: 30, background: frame >= at('fingerprint') ? `${C.teal}66` : 'transparent', borderRadius: 8}}>"zip_sha256": "9f2c…e71"</div>
            </Pop>
            <div>{'}'}</div>
          </Card>
        </Enter>
        <Pop at={at('fingerprint')} x={760} y={230}><Float><IFinger size={110} /></Float></Pop>
        <Pop at={download} x={1050} y={160}>
          <div style={{display: 'flex', alignItems: 'center', gap: 16}}><IZip size={130} /><Chip color={C.white} size={28}>irrigation-0.5.0.zip</Chip></div>
        </Pop>
        <Arrow at={download + 6} x1={1130} y1={310} x2={1130} y2={420} dur={10} />
        <Exit at={off - 4}>
          <Pop at={check} x={830} y={460}><FingerCompare at={check + 6} result={at('Only if it matches')} ok /></Pop>
          <Pop at={at('byte for byte')} x={420} y={560} rotate={-6}><Chip color={C.sun} size={30}>byte for byte</Chip></Pop>
          <Pop at={swap - 4} x={110} y={640}>
            <div style={{position: 'relative', width: 700, height: 240}}>
              <div style={{position: 'absolute', left: 0, top: 0}}><Chip color={C.white} size={26}>~/.ai-dist/…/irrigation/</Chip></div>
              {[['v0.4.0', C.white], ['v0.5.0', C.mint]].map(([v, c], i) => {
                const x = i === 0 ? interpolate(swapT, [0, 1], [0, 360]) : interpolate(swapT, [0, 1], [360, 0]);
                const y = i === 0 ? interpolate(swapT, [0, 1], [80, 110]) : 80;
                const label = i === 0 ? (swapT > 0.5 ? 'previous/' : 'current/') : swapT > 0.5 ? 'current/' : 'staging/';
                return (
                  <div key={v} style={{position: 'absolute', left: x, top: y}}>
                    <Card color={c} pad={14} radius={18} shadow={6} style={{width: 300, textAlign: 'center', fontSize: 30, fontWeight: 700, opacity: i === 0 ? 1 - swapT * 0.45 : 1}}>
                      <div style={{fontFamily: MONO, fontSize: 24, fontWeight: 500}}>{label}</div>{v}
                    </Card>
                  </div>
                );
              })}
            </div>
          </Pop>
        </Exit>
        <Pop at={off} x={830} y={460}><FingerCompare at={off + 4} result={at('nothing changes')} ok={false} /></Pop>
        <Pop at={at('old version keeps working')} x={180} y={640}>
          <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
            <IShield size={150} />
            <Card color={C.white} style={{fontSize: 38, fontWeight: 700}}>v0.4.0 keeps working</Card>
          </div>
        </Pop>
      </Exit>
      <Pop at={nudge} x={260} y={250}>
        <div style={{transform: `rotate(${(frame - nudge) * 6}deg)`}}><IClock size={300} /></div>
      </Pop>
      <Pop at={nudge + 6} x={250} y={580} rotate={-5}><Chip color={C.sun} size={34}>24 hours later…</Chip></Pop>
      <Enter at={at('friendly nudge')} from="right" x={1500} y={430} dist={500}><Bot size={250} /></Enter>
      <Pop at={at('friendly nudge', 6)} x={790} y={250} style={{transformOrigin: 'right bottom'}}>
        <Bubble tail="right" size={42} color={C.white}>Hey Dana, it's been a day.<br />Check for updates?</Bubble>
      </Pop>
      <Enter at={at('check for updates')} from="bottom" x={880} y={560} dist={400}><Dana size={220} mood="grin" wave /></Enter>
    </Stage>
  );
};

// ---------------------------------------------------------------- 08 publish

export const Publish: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const improves = at('improves the skill');
  const zips = at('zips the skill');
  const drop = at('drops it into');
  const back = at('downloads it back');
  const scribble = interpolate(frame, [improves - 10, improves + 20], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const shrink = useSmooth(zips, 14);
  const items: [string, string][] = [
    ['checks the structure', 'Structure check'],
    ['asks Dana why', 'Why: “handles drip zones”'],
    ['notes the reason', 'CHANGES.md updated'],
  ];
  return (
    <Stage tint={C.pink}>
      <SceneTag n={8} label="Share an improvement" />
      <Enter at={at('Now for the fun part') + 4} from="left" x={60} y={450} dist={400}>
        <Dana size={280} mood={frame >= back ? 'grin' : 'happy'} />
      </Enter>
      <Pop at={at('fun part')} x={110} y={150} rotate={-8}><Chip color={C.sun} size={36}>the fun part</Chip></Pop>
      {frame < zips + 14 && (
        <Pop at={at('a better way')} x={540} y={190}>
          <div style={{transform: `scale(${1 - shrink * 0.9})`, transformOrigin: '260px 160px', opacity: 1 - shrink}}>
            <Card color={C.paper} style={{width: 500, height: 330, position: 'relative'}}>
              <SkillCard name="watering-plan" color={C.mint} />
              {['Read the block’s soil type', 'Pick valves by zone', 'Plan the schedule'].map((l, i) => (
                <div key={l} style={{fontSize: 28, marginTop: i ? 10 : 22, fontWeight: 500}}>• {l}</div>
              ))}
              <svg width={460} height={60} style={{position: 'absolute', left: 40, bottom: 18}}>
                <path d="M0 30 Q30 0 60 30 T120 30 T180 30 T240 30 T300 30 T360 30 T420 30" fill="none" stroke={C.coral} strokeWidth={7} strokeLinecap="round"
                  strokeDasharray={520} strokeDashoffset={520 * (1 - scribble)} />
              </svg>
              <div style={{position: 'absolute', right: -30, top: -30}}><Pop at={improves + 6} x={0} y={0} style={{position: 'relative'}} rotate={12}><Chip color={C.coral} size={32}>v2!</Chip></Pop></div>
              <div style={{position: 'absolute', right: 30, bottom: 50, transform: `translateX(${Math.sin(frame / 3) * 30 * scribble * (scribble < 1 ? 1 : 0)}px)`}}>{scribble > 0 && scribble < 1 && <IPencil size={90} />}</div>
            </Card>
          </div>
        </Pop>
      )}
      <Pop at={at('publish this')} x={110} y={280} style={{transformOrigin: 'left bottom'}}><Bubble tail="left" size={46} color={C.sun}>“Publish this!”</Bubble></Pop>
      {items.map(([cue, label], i) => (
        <Pop key={cue} at={at(cue)} x={1120} y={190 + i * 130} style={{transformOrigin: 'left center'}}>
          <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
            <ICheck size={80} />
            <Card color={C.white} pad={16} radius={20} shadow={6} style={{fontSize: 36, fontWeight: 600}}>{label}</Card>
          </div>
        </Pop>
      ))}
      <Hop a={zips + 4} b={drop + 6} x1={790} y1={350} x2={1450} y2={700} height={200}><IZip size={140} /></Hop>
      <Pop at={drop - 12} x={1360} y={640}>
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6}}>
          <IInbox size={190} />
          <Chip color={C.white} size={28}>irrigation inbox</Chip>
        </div>
      </Pop>
      <Arrow at={back} x1={1360} y1={720} x2={420} y2={640} bend={0.2} />
      <Pop at={back + 10} x={640} y={800}><Chip color={C.white} size={28}><span style={{fontFamily: MONO}}>sha256 ✓ same bytes</span></Chip></Pop>
      <Stamp at={at('arrived intact')} text="INTACT" color={C.mint} x={1100} y={620} size={80} />
    </Stage>
  );
};

