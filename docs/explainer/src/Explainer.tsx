import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import timings from './timings.json';
import {C, FPS, LEAD, MONO, SANS, SceneId, SceneProvider, sceneFrames, useSceneId} from './kit';
import {Anatomy, DriveScene, Idea, Intro, Layers, QuickStart, TitleScene} from './scenesA';
import {Checks, Feedback, Maintainer, Outro, Publish, Release, Safety, Sync} from './scenesB';

export const TITLE_FRAMES = 110;
const OUTRO_HOLD = 80;
const XFADE = 10;

const SCENES: [SceneId, React.FC][] = [
  ['intro', Intro], ['idea', Idea], ['layers', Layers], ['anatomy', Anatomy], ['drive', DriveScene], ['quickstart', QuickStart],
  ['sync', Sync], ['publish', Publish], ['maintainer', Maintainer], ['checks', Checks], ['release', Release], ['feedback', Feedback], ['safety', Safety], ['outro', Outro],
];

const framesOf = (id: SceneId) => sceneFrames(id, id === 'outro' ? OUTRO_HOLD : undefined);
export const totalFrames = () => TITLE_FRAMES + SCENES.reduce((n, [id]) => n + framesOf(id), 0);

/** Lower-left caption: the current sentence; spoken words in ink, upcoming in grey. */
const Caption: React.FC = () => {
  const id = useSceneId();
  const frame = useCurrentFrame();
  const t = (frame - LEAD) / FPS;
  const {sentences, words} = timings[id];
  const current = sentences.find((s) => t >= s.start - 0.05 && t < s.end - 0.05);
  if (!current) return null;
  const first = words.findIndex((w) => Math.abs(w.s - current.start) < 0.001);
  const ws = words.slice(first, first + current.text.split(' ').length);
  const enter = interpolate(t - current.start, [0, 0.15], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 80, right: 80, bottom: 44, display: 'flex', justifyContent: 'center', opacity: enter}}>
      <div style={{maxWidth: 1500, background: C.ink, color: '#fff', borderRadius: 8, padding: '12px 24px', fontFamily: SANS, fontWeight: 500, fontSize: 30, lineHeight: 1.35, textAlign: 'center'}}>
        {ws.map((w, i) => (
          <span key={i} style={{opacity: t >= w.s - 0.02 ? 1 : 0.45}}>{w.w}{i < ws.length - 1 ? ' ' : ''}</span>
        ))}
      </div>
    </div>
  );
};

/** Fade in at the start of a scene and out at its end. */
const SceneFade: React.FC<{dur: number; children: React.ReactNode}> = ({dur, children}) => {
  const frame = useCurrentFrame();
  const o = Math.min(interpolate(frame, [0, XFADE], [0, 1], {extrapolateRight: 'clamp'}), interpolate(frame, [dur - XFADE, dur], [1, 0], {extrapolateLeft: 'clamp'}));
  return <AbsoluteFill style={{opacity: o}}>{children}</AbsoluteFill>;
};

const Progress: React.FC = () => {
  const frame = useCurrentFrame();
  const total = totalFrames();
  return (
    <div style={{position: 'absolute', left: 0, bottom: 0, height: 5, width: (frame / total) * 1920, background: C.blue}} />
  );
};

export const Explainer: React.FC = () => {
  let start = TITLE_FRAMES;
  const placed = SCENES.map(([id, Comp]) => {
    const from = start;
    start += framesOf(id);
    return {id, Comp, from, dur: framesOf(id)};
  });
  return (
    <AbsoluteFill style={{background: C.paper}}>
      <Sequence durationInFrames={TITLE_FRAMES}>
        <SceneFade dur={TITLE_FRAMES}><TitleScene /></SceneFade>
      </Sequence>
      {placed.map(({id, Comp, from, dur}) => (
        <Sequence key={id} from={from} durationInFrames={dur} name={id}>
          <SceneProvider id={id}>
            <SceneFade dur={dur}>
              <Comp />
              <Caption />
            </SceneFade>
          </SceneProvider>
          <Sequence from={LEAD}>
            <Audio src={staticFile(`audio/${id}.mp3`)} />
          </Sequence>
        </Sequence>
      ))}
      <Progress />
      <div style={{position: 'absolute', right: 80, top: 66, fontFamily: MONO, fontSize: 20, color: C.ink3}}>skills-hub</div>
    </AbsoluteFill>
  );
};
