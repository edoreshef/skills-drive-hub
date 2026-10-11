import React from 'react';
import {interpolate, useCurrentFrame} from 'remotion';
import {
  Agent, C, Code, Fade, FileTree, H, Heading, Line, MONO, P, Persona, Rise, Say, Sheet, Stage, Status, Tag, Terminal, Travel,
  useAt, useReveal,
} from './kit';

const Row: React.FC<{at: number; kind: 'ok' | 'warn' | 'block' | 'off'; children: React.ReactNode; size?: number; mono?: boolean}> = ({at, kind, children, size = 25, mono}) => (
  <Rise at={at} x={0} y={0} style={{position: 'relative', display: 'flex', alignItems: 'center', gap: 14, marginBottom: 12}}>
    <Status kind={kind} size={26} />
    <P size={size} color={C.ink} mono={mono}>{children}</P>
  </Rise>
);

// ---------------------------------------------------------------- 07 sync

export const Sync: React.FC = () => {
  const at = useAt();
  const frame = useCurrentFrame();
  const reads = at('reads the pointer');
  const verify = at('verifies the fingerprint');
  const swap = at('replaces the current one');
  const fail = at('If the check fails');
  const gate = at('Stale skills');
  const remind = at('In Claude Code');
  const swapP = useReveal(swap, 24);
  const okAt = verify + 24;
  // Three slots: previous | current | staging. On swap both boxes move one slot left, so they never cross.
  const slot = (i: number) => 10 + i * 330;
  return (
    <Stage>
      <Heading n={7} title="Staying current" />
      <Rise at={at('one small pointer file')} x={80} y={200} w={640}>
        <Sheet pad={24} tab="current.json  (fixed file ID)">
          <Code at={at('one small pointer file')} size={23} lines={[
            {text: '{'},
            {text: '  "package": "genomics",'},
            {text: '  "version": "0.5.0",', hi: frame >= at('latest version') ? C.blueSoft : undefined},
            {text: '  "min_version": "0.3.0",'},
            {text: '  "zip_file_id": "1AbC…",'},
            {text: '  "zip_sha256": "9f2c…e71",', hi: frame >= at('its fingerprint') ? C.blueSoft : undefined},
            {text: '  "zip_bytes": 184320'},
            {text: '}'},
          ]} />
        </Sheet>
      </Rise>
      <Fade at={gate - 12}>
        <Rise at={reads} x={800} y={200} w={1040}>
          <Terminal at={reads} width={1040} size={21} title="sync" command="python ~/.skills-hub/framework/current/tools/sync.py --package genomics" output={[
            {text: 'current.json: 0.5.0  (installed 0.4.0)', at: reads + 30},
            {text: 'downloading releases/genomics-0.5.0.zip', at: at('downloads the release')},
            {text: 'sha256 expected  9f2c4a…e71', at: verify},
            {text: 'sha256 computed  9f2c4a…e71', at: verify + 10},
            {text: 'size 184320 = 184320  verified', color: '#7CE0A3', at: okAt},
            {text: 'swap staging → current, previous kept', at: swap},
            {text: 'state.json: genomics 0.5.0, last_check now', at: at('previous version is kept')},
          ]} />
        </Rise>
        <Fade at={fail - 2}>
          <Rise at={swap - 6} x={800} y={585} w={1040}>
            <Sheet pad={22} tab="~/.skills-hub/packages/genomics/">
              <div style={{position: 'relative', height: 130}}>
                {['previous/', 'current/', 'staging/'].map((label, i) => (
                  <div key={label} style={{position: 'absolute', left: slot(i), top: 0, width: 300, height: 120, border: `1.5px dashed ${C.rule}`, borderRadius: 8, boxSizing: 'border-box', padding: '10px 16px', fontFamily: MONO, fontSize: 20, color: C.ink3}}>{label}</div>
                ))}
                {[['0.4.0', C.sheet, 1], ['0.5.0', C.greenSoft, 2]].map(([v, tone, from]) => {
                  const x = interpolate(swapP, [0, 1], [slot(from as number), slot((from as number) - 1)]);
                  return (
                    <div key={v as string} style={{position: 'absolute', left: x + 14, top: 46, width: 272, background: tone as string, border: `1.5px solid ${C.rule}`, borderRadius: 8, padding: '12px 16px', fontFamily: MONO, fontSize: 23, color: C.ink, boxSizing: 'border-box', opacity: from === 1 ? 1 - swapP * 0.45 : 1}}>
                      genomics {v}
                    </div>
                  );
                })}
              </div>
            </Sheet>
          </Rise>
        </Fade>
        <Rise at={fail} x={800} y={585} w={1040}>
          <Sheet pad={22} tone={C.redSoft} tab="on mismatch">
            <Code at={fail} size={22} lines={[
              {text: 'sha256 expected  9f2c4a…e71'},
              {text: 'sha256 computed  31d0b7…0c9', color: C.red},
              {text: 'mismatch: nothing written. retry once, then stop.', color: C.red, at: at('nothing changes')},
              {text: 'current/ still genomics 0.4.0', at: at('nothing changes') + 6},
            ]} />
          </Sheet>
        </Rise>
      </Fade>
      <Rise at={gate} x={800} y={200} w={1040}>
        <Terminal at={gate} width={1040} size={21} title="a skill script, three days later" command="uv run --script ~/.skills-hub/packages/genomics/current/skills/study-summary/scripts/summarize.py" output={[
          {text: 'blocked: package genomics: last sync check is over 24h old.', color: '#F2A3A3', at: at('refuse to run')},
          {text: 'Run the sync skill, then run this script again.', color: '#F2A3A3', at: at('tell the agent to sync')},
          {text: 'exit 75', color: '#9AA6B8', at: at('tell the agent to sync') + 6},
        ]} />
      </Rise>
      <Rise at={at('not been checked')} x={800} y={470} w={1040}>
        <P size={25}>The gate is added at release, to every script in a content package. It reads <span style={{fontFamily: MONO}}>state.json</span>: over 24 hours since the last check, or a newer version pending, and the script stops before it does anything.</P>
      </Rise>
      <Rise at={remind} x={800} y={640} w={1040}>
        <Sheet pad={24} tab="Claude Code  SessionStart hook  (stale.py)">
          <P size={23} mono color={C.ink}>sync: packages are stale and their scripts will not run until synced: genomics</P>
        </Sheet>
      </Rise>
      <Rise at={at('start of each session')} x={800} y={770} w={1040}>
        <P size={25}>Local only: the hook reads <span style={{fontFamily: MONO}}>state.json</span>, nothing else. Cursor users ask to sync when the gate tells them to.</P>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 08 publish

export const Publish: React.FC = () => {
  const at = useAt();
  const run = at('runs the structure checks');
  const why = at('asks why');
  const pack = at('packages the skill');
  const upload = at('uploads it');
  const back = at('downloads it back');
  return (
    <Stage>
      <Heading n={8} title="Submitting a change" />
      <Rise at={at('When Maya improves')} x={80} y={190}><Persona initials="M" name="Maya" size={90} /></Rise>
      <Rise at={at('tells the agent to publish')} x={300} y={190}><Say who="person" size={27}>Publish study-summary.</Say></Rise>
      <Rise at={why} x={300} y={290}><Say who="agent" size={26}>What changed, and why?</Say></Rise>
      <Rise at={at('records the reason')} x={300} y={385}><Say who="person" size={26} width={560}>It now includes the caveats section the review board asks for.</Say></Rise>
      <Rise at={run} x={80} y={560} w={820}>
        <Terminal at={run} width={820} size={20} title="publish" command="python …/tools/publish.py --package-dir ~/.skills-hub/drafts/genomics --skill study-summary --rationale '…' --author maya@org --out inbox/" output={[
          {text: 'check: skills/study-summary  0 blocking, 0 warnings', color: '#7CE0A3', at: run + 40},
          {text: 'CHANGES.md: 2026-10-10 entry added', at: at('change log')},
          {text: 'submission.json written', at: at('change log') + 5},
          {text: 'zip: study-summary__20261010-1432__maya.zip', at: pack},
          {text: 'sha256 4b19c0…8aa', at: pack + 6},
        ]} />
      </Rise>
      <Rise at={at('records the reason') + 10} x={980} y={190} w={860}>
        <Sheet pad={22} tab="CHANGES.md">
          <Code at={at('records the reason') + 10} size={22} lines={[
            {text: '## 2026-10-10  maya@org'},
            {text: 'Adds the caveats section the review board asks for.'},
            {text: ''},
            {text: '## 2026-08-02  maya@org', color: C.ink3},
            {text: 'First version.', color: C.ink3},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={pack} x={980} y={450} w={860}>
        <Sheet pad={22} tab="genomics — Submissions / inbox/">
          <FileTree at={upload} size={22} rows={[
            {d: 0, name: 'cohort-definitions__20261003-0911__sam.zip'},
            {d: 0, name: 'study-summary__20261010-1432__maya.zip', hi: C.greenSoft, at: upload + 14},
          ]} />
        </Sheet>
      </Rise>
      <Travel a={upload} b={upload + 16} x1={700} y1={760} x2={1300} y2={560} hideAfter>
        <Tag mono size={22} bg={C.sheet} style={{border: `1.5px solid ${C.ink}`}}>study-summary__…__maya.zip</Tag>
      </Travel>
      <Rise at={back} x={980} y={660} w={860}>
        <Code at={back} size={22} lines={[
          {text: 'download back:  sha256 4b19c0…8aa'},
          {text: 'uploaded copy matches. one retry on mismatch.', color: C.green, at: at('copy matches')},
        ]} />
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 09 maintainer

export const Maintainer: React.FC = () => {
  const at = useAt();
  const report = at('prints a single report');
  const lines: [string, string, string?][] = [
    ['who submitted it', 'submitter: sam@org'],
    ['who owns the skill', 'owner: maya@org'],
    ['the stated reason', 'rationale: Adds frost… adds the p-value column to the cohort table'],
    ['exact difference', '--- a/skills/cohort-definitions/SKILL.md'],
    ['exact difference', '+++ b/skills/cohort-definitions/SKILL.md'],
    ['exact difference', '- Report cohort sizes only.', 'del'],
    ['exact difference', '+ Include the adjusted p-value next to each cohort size.', 'add'],
    ['results of the checks', 'warning: skills/cohort-definitions/scripts/table.py: third-party dependency pandas'],
    ['results of the checks', '0 blocking, 1 warning'],
  ];
  return (
    <Stage>
      <Heading n={9} title="Reviewing a submission" />
      <Rise at={at('Maya is also')} x={80} y={200}><Persona initials="M" name="Maya" role="maintainer, genomics" size={120} badge="MAINTAINER" badgeAt={at('also a maintainer')} /></Rise>
      <Rise at={at('submissions from colleagues')} x={80} y={420}><Persona initials="S" name="Sam" role="submitted cohort-definitions" size={100} color={C.violet} /></Rise>
      <Line at={at('come to her')} points={[[300, 470], [300, 300], [230, 300]]} color={C.ink3} arrow dur={16} />
      <Rise at={report} x={620} y={190} w={1220}>
        <Terminal at={report} width={1220} size={21} title="review" command="python maintainer/review.py --package inbox/cohort-definitions --skill cohort-definitions --baseline releases/genomics-0.5.0" output={[
          {text: 'package: genomics', at: report + 36},
          {text: 'maintainers: maya@org, sam@org', at: report + 40},
          {text: 'skill: cohort-definitions', at: report + 44},
          ...lines.map(([cue, text, kind], i) => ({
            text: kind === 'add' ? text : kind === 'del' ? text : text.replace('Adds frost… ', ''),
            color: kind === 'add' ? '#7CE0A3' : kind === 'del' ? '#F2A3A3' : text.startsWith('warning') ? '#F5D278' : undefined,
            at: at(cue) + (cue === 'exact difference' ? (i - 3) * 5 : cue === 'results of the checks' ? (i - 7) * 8 : 0),
          })),
        ]} />
      </Rise>
      <Rise at={at('single report')} x={620} y={760} w={1220}>
        <P size={26}>One screen, the same for every submission: enough to decide, without opening a diff tool.</P>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 10 checks and decision

export const Checks: React.FC = () => {
  const at = useAt();
  const judge = at('do not judge');
  const decide = at('Then she accepts');
  return (
    <Stage>
      <Heading n={10} title="What blocks, what warns, who decides" />
      <Fade at={judge - 4}>
        <Rise at={at('two levels')} x={80} y={200} w={840}>
          <Sheet pad={26} tab="blocking" tabColor={C.red}>
            <Row at={at('missing example')} kind="block">no example</Row>
            <Row at={at('no dated change entry')} kind="block">no dated CHANGES.md entry</Row>
            <Row at={at('dependency without')} kind="block">dependency range: <span style={{fontFamily: MONO}}>pandas&gt;=2</span> (needs <span style={{fontFamily: MONO}}>==</span>)</Row>
            <Row at={at('looks like a credential')} kind="block">credential-like file</Row>
            <Row at={at('looks like a credential') + 8} kind="block">invalid frontmatter, reserved name, binary, symlink, over 64 KiB</Row>
            <Rise at={at('looks like a credential') + 18} x={0} y={0} style={{position: 'relative', marginTop: 10}}><P size={24}>Refused at publish and at release.</P></Rise>
          </Sheet>
        </Rise>
        <Rise at={at('Everything else')} x={980} y={200} w={860}>
          <Sheet pad={26} tab="warning" tabColor={C.amber}>
            <Row at={at('talks to the network')} kind="warn">imports <span style={{fontFamily: MONO}}>socket</span>, <span style={{fontFamily: MONO}}>requests</span>, <span style={{fontFamily: MONO}}>urllib</span>, <span style={{fontFamily: MONO}}>subprocess</span></Row>
            <Row at={at('third-party dependency')} kind="warn">any third-party dependency</Row>
            <Row at={at('third-party dependency') + 8} kind="warn"><span style={{fontFamily: MONO}}>eval</span>, <span style={{fontFamily: MONO}}>exec</span>, paths outside the skill, no tests, large size increase</Row>
            <Rise at={at('for the reviewer')} x={0} y={0} style={{position: 'relative', marginTop: 10}}><P size={24}>Reported. The reviewer weighs them.</P></Rise>
          </Sheet>
        </Rise>
      </Fade>
      <Rise at={judge} x={80} y={200} w={840}>
        <H size={40}>The tools do not judge content.</H>
        <P size={28} style={{marginTop: 16}}>The maintainer does.</P>
      </Rise>
      <Rise at={at('reads the instructions')} x={80} y={360} w={840}>
        <Sheet pad={22} tab="SKILL.md  (prose is instructions to the agent)">
          <Code at={at('reads the instructions')} size={22} lines={[
            {text: 'Include the adjusted p-value next to each cohort size.'},
            {text: 'If the registry is unavailable, use the cached table', hi: C.amberSoft, at: at('what the agent will follow')},
            {text: 'from the shared drive instead.', hi: C.amberSoft, at: at('what the agent will follow') + 2},
          ]} />
          <Rise at={at('what the agent will follow') + 10} x={0} y={0} style={{position: 'relative', marginTop: 12}}>
            <P size={23}>One sentence changes what the agent does. Read it as carefully as the script.</P>
          </Rise>
        </Sheet>
      </Rise>
      <Rise at={decide} x={980} y={200} w={860}>
        <Sheet pad={24} tab="genomics — Submissions">
          <FileTree at={decide} size={23} rows={[
            {d: 0, name: 'accepted', dir: true, hi: C.greenSoft, at: at('accepts')},
            {d: 1, name: 'cohort-definitions__20261003-0911__sam.zip', at: at('accepts') + 4},
            {d: 1, name: 'REVIEW.md', note: 'the short note', at: at('short note')},
            {d: 0, name: 'rejected', dir: true, at: at('rejects')},
            {d: 1, name: 'REVIEW.md', note: 'why, so the author can fix it', at: at('rejects') + 4},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={at("author's agent can read")} x={980} y={520}>
        <div style={{display: 'flex', alignItems: 'center', gap: 22}}>
          <Agent size={80} />
          <Say who="agent" size={24} width={640}>Your cohort-definitions change was accepted. It ships in genomics 0.6.0.</Say>
        </div>
      </Rise>
      <Rise at={at('next release')} x={980} y={680} w={860}>
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}><Status kind="ok" /><P size={26} color={C.ink}>Accepted: committed to the genomics repo, queued for 0.6.0.</P></div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 11 release

export const Release: React.FC = () => {
  const at = useAt();
  const commit = at('committed to the');
  const bump = at('bumps the version');
  const build = at('builds the zip');
  const upload = at('zip is uploaded');
  const pointer = at('rewritten last');
  const sync = at('The next sync');
  const users = ['Maya', 'Sam', 'Jun', 'Rin', 'Ava', 'Lee'];
  return (
    <Stage>
      <Heading n={11} title="Releasing to everyone" />
      <Rise at={commit} x={80} y={200} w={820}>
        <Sheet pad={22} tab="genomics repo">
          <Code at={commit} size={22} lines={[
            {text: 'git log --oneline', color: C.ink3},
            {text: 'a41f2c  cohort-definitions: adjusted p-value (sam)'},
            {text: '9b03e7  release 0.6.0', hi: C.blueSoft, at: bump},
            {text: '        package.json   "version": "0.6.0"', at: bump + 4},
            {text: '        CHANGELOG.md   ## 0.6.0', at: bump + 7},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={build} x={80} y={440} w={820}>
        <Terminal at={build} width={820} size={20} title="release" command="python maintainer/release.py --package genomics --out dist" output={[
          {text: 'check: 0 blocking, 1 warning', at: build + 32},
          {text: 'sync gate added to 2 scripts: table.py, summarize.py', at: at('adds the sync gate')},
          {text: 'refuses: an installer, a credential-like file, a blocked check', color: '#F5D278', at: at('refuses anything')},
          {text: 'genomics-0.6.0.zip  sha256 c71d…04b  190464 bytes', color: '#7CE0A3', at: at('refuses anything') + 24},
          {text: 'manifest.json  current.json', at: at('refuses anything') + 28},
        ]} />
      </Rise>
      <Rise at={upload - 10} x={980} y={200} w={860}>
        <Sheet pad={24} tab="genomics — Published">
          <FileTree at={upload - 10} size={23} rows={[
            {d: 0, name: 'releases', dir: true},
            {d: 1, name: 'genomics-0.5.0.zip'},
            {d: 1, name: 'genomics-0.6.0.zip', note: 'sha256Checksum matches', hi: C.greenSoft, at: upload},
            {d: 0, name: 'current.json', note: '"version": "0.5.0" → "0.6.0"', hi: C.blueSoft, at: pointer},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={at('never pointed at')} x={980} y={450} w={860}>
        <P size={25}>The pointer changes only after the zip is on Drive and its checksum matches, so no agent ever downloads a half-uploaded release.</P>
      </Rise>
      <Rise at={sync} x={980} y={600} w={860}>
        <div style={{display: 'grid', gridTemplateColumns: 'repeat(3, 270px)', gap: 16}}>
          {users.map((u, i) => (
            <UserSync key={u} name={u} at={sync + 14 + i * 7} />
          ))}
        </div>
      </Rise>
      <Rise at={at('everyone who has')} x={980} y={840} w={860}>
        <P size={25} color={C.ink}>Only genomics moves. Foundation and Skills Hub stay where they were.</P>
      </Rise>
    </Stage>
  );
};

/** One user's agent picking up a release: the version tag flips on its own sync. */
const UserSync: React.FC<{name: string; at: number}> = ({name, at}) => {
  const p = useReveal(at, 12);
  const flipped = p > 0.5;
  return (
    <Sheet pad={14} style={{display: 'flex', alignItems: 'center', gap: 14}}>
      <Agent size={40} label="" />
      <P size={22} color={C.ink} style={{flex: 1}}>{name}</P>
      <Tag mono size={19} bg={flipped ? C.blue : C.sheet} color={flipped ? '#fff' : C.ink2} style={{border: `1.5px solid ${flipped ? C.blue : C.rule}`}}>{flipped ? '0.6.0' : '0.5.0'}</Tag>
    </Sheet>
  );
};

// ---------------------------------------------------------------- 11 feedback

export const Feedback: React.FC = () => {
  const at = useAt();
  const writes = at('writes a small note');
  const collect = at('collect those notes');
  return (
    <Stage>
      <Heading n={12} title="Feedback" />
      <Rise at={at('A colleague')} x={80} y={200}><Persona initials="J" name="Jun" role="clinical group" size={90} color={C.violet} /></Rise>
      <Rise at={at('gave an odd answer')} x={380} y={200}><Say who="person" size={26}>study-summary gave an odd answer for GX-2041.</Say></Rise>
      <Rise at={at('asks which skill')} x={380} y={295}><Say who="agent" size={25}>Which package and skill? May I send a note to its maintainers?</Say></Rise>
      <Rise at={at('asks for consent')} x={380} y={390}><Say who="person" size={26}>genomics / study-summary. Yes.</Say></Rise>
      <Rise at={writes} x={80} y={540} w={840}>
        <Sheet pad={22} tab="genomics — Submissions / feedback/">
          <FileTree at={writes} size={22} rows={[
            {d: 0, name: '20261010-1502__jun@org__study-summary.json', hi: C.blueSoft},
          ]} />
          <Code at={writes + 10} size={21} lines={[
            {text: '{ "package": "genomics", "skill": "study-summary",'},
            {text: '  "author": "jun@org", "consent": true,'},
            {text: '  "note": "Summary omitted the cohort size for GX-2041." }'},
          ]} />
        </Sheet>
      </Rise>
      <Rise at={collect} x={1560} y={200}><Persona initials="M" name="Maya" role="maintainer" size={90} /></Rise>
      <Rise at={collect + 6} x={980} y={370} w={860}>
        <Terminal at={collect + 6} width={860} size={20} title="collect" command="python maintainer/collect-feedback.py --feedback feedback/ --sheet feedback.csv" output={[
          {text: '1 new entry appended', at: at('into a sheet')},
        ]} />
      </Rise>
      <Rise at={at('into a sheet')} x={980} y={580} w={860}>
        <Sheet pad={0} tab="Feedback (Sheet)" style={{paddingTop: 22}}>
          <div style={{overflow: 'hidden', borderRadius: '0 0 7px 7px'}}>
            <table style={{borderCollapse: 'collapse', width: '100%', fontFamily: MONO, fontSize: 20, color: C.ink}}>
              <tbody>
                {[['2026-09-28', 'sam@org', 'assay-readout', 'Units missing on plate 3'], ['2026-10-04', 'rin@org', 'cohort-definitions', 'Age band wrong for 65+'], ['2026-10-10', 'jun@org', 'study-summary', 'Cohort size omitted']].map((r, i) => (
                  <tr key={i} style={{background: i === 2 ? C.blueSoft : i % 2 ? '#F7F9FC' : C.sheet}}>
                    {r.map((c, j) => <td key={j} style={{padding: '10px 14px', borderBottom: i < 2 ? `1px solid ${C.rule}` : 'none'}}>{c}</td>)}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Sheet>
      </Rise>
      <Rise at={at('next release improves')} x={980} y={800} w={860}>
        <div style={{display: 'flex', alignItems: 'center', gap: 14}}><Status kind="ok" /><P size={26} color={C.ink}>Fixed in study-summary, genomics 0.7.0.</P></div>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 12 safety

export const Safety: React.FC = () => {
  const at = useAt();
  const rows: [string, string, string][] = [
    ['write only to their own', 'One package, one trust boundary', 'Published drive: maintainers write, everyone else reads. A genomics maintainer cannot touch clinical, or Skills Hub.'],
    ['Only Skills Hub carries', 'Only Skills Hub ships the installer', 'release.py and install.py refuse a content zip that contains tools/install.py.'],
    ['Scripts work on local files', 'Scripts stay local', 'stdin and files in, stdout out. No network calls; credential-like files are refused at release and install.'],
    ['every download is verified', 'Every download is verified first', 'sha256 and size are checked before anything is written; then staging is swapped into current.'],
  ];
  return (
    <Stage>
      <Heading n={13} title="Narrow boundaries" />
      {rows.map(([cue, title, detail], i) => (
        <Rise key={title} at={at(cue)} x={80} y={200 + i * 180} w={1760}>
          <div style={{display: 'flex', gap: 26, alignItems: 'flex-start', borderTop: `1.5px solid ${C.rule}`, paddingTop: 22}}>
            <Status kind="ok" size={34} />
            <div style={{width: 560}}><H size={32}>{title}</H></div>
            <P size={25} style={{flex: 1}}>{detail}</P>
          </div>
        </Rise>
      ))}
      <Rise at={at('before it is used')} x={80} y={930} w={1760}>
        <P size={24} color={C.ink3}>Submissions are untrusted until reviewed. The hash detects corruption, not a compromised maintainer; keep two managers on every published drive.</P>
      </Rise>
    </Stage>
  );
};

// ---------------------------------------------------------------- 13 outro

export const Outro: React.FC = () => {
  const at = useAt();
  const recap: [string, string, string][] = [
    ['Three layers', 'Three layers', 'Skills Hub, foundation, domain packages'],
    ['Shared drives', 'Shared drives', 'the ones you already have, behind SSO'],
    ['Get skills', 'Get, sync, contribute', 'by asking; every download verified'],
    ['Feedback in', 'Feedback', 'one sentence, with consent'],
    ['One report', 'Review and release', 'one report; the next sync reaches all'],
  ];
  const final = at('Your expertise');
  return (
    <Stage>
      <Heading n={14} title="The whole model" />
      {recap.map(([cue, title, sub], i) => (
        <Rise key={title} at={at(cue)} x={80} y={200 + i * 110} w={940}>
          <div style={{display: 'flex', alignItems: 'baseline', gap: 24, borderTop: `1.5px solid ${C.rule}`, paddingTop: 16}}>
            <H size={34} style={{width: 400, flexShrink: 0}}>{title}</H>
            <P size={25} style={{whiteSpace: 'nowrap'}}>{sub}</P>
          </div>
        </Rise>
      ))}
      <Rise at={final} x={1060} y={200} w={780}>
        <Sheet pad={30} tone={C.blueSoft} style={{border: 'none'}}>
          <H size={34}>Quick start</H>
          <div style={{marginTop: 18, display: 'flex', flexDirection: 'column', gap: 14}}>
            {['Connect Google Drive in your host.', 'Say: "Read the START HERE doc on the Skills Hub drive and follow it."', 'Say: "Run doctor."'].map((s, i) => (
              <div key={s} style={{display: 'flex', gap: 16, alignItems: 'flex-start'}}>
                <div style={{width: 34, height: 34, borderRadius: '50%', background: C.blue, color: '#fff', fontWeight: 600, fontSize: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0}}>{i + 1}</div>
                <P size={24} color={C.ink}>{s}</P>
              </div>
            ))}
          </div>
        </Sheet>
      </Rise>
      <Rise at={at('available to every agent')} x={80} y={790} w={1760}>
        <H size={56} weight={500}>Your expertise, available to every agent in the organization.</H>
      </Rise>
    </Stage>
  );
};
