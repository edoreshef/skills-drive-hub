import React from 'react';
import {AbsoluteFill, Audio, interpolate, Sequence, staticFile, useCurrentFrame} from 'remotion';
import timings from './timings.json';
import {C, FONT, FPS, LEAD, SceneId, SceneProvider, sceneFrames, useSceneId} from './kit';
import {Idea, Intro, Layers, Problem, TitleScene} from './scenes1';
import {DriveScene, Install, Publish, Sync} from './scenes2';
import {Feedback, Maintainer, Outro, Review, Safety} from './scenes3';

export const TITLE_FRAMES = 96;
const OUTRO_HOLD = 90;

const SCENES: [SceneId, React.FC, string][] = [
  ['intro', Intro, C.mint],
  ['problem', Problem, C.coral],
  ['idea', Idea, C.sky],
  ['layers', Layers, C.grape],
  ['drive', DriveScene, C.sun],
  ['install', Install, C.mint],
  ['sync', Sync, C.teal],
  ['publish', Publish, C.pink],
  ['maintainer', Maintainer, C.sun],
  ['review', Review, C.mint],
  ['feedback', Feedback, C.sky],
  ['safety', Safety, C.grape],
  ['outro', Outro, C.coral],
];

const framesOf = (id: SceneId) => sceneFrames(id, id === 'outro' ? OUTRO_HOLD : undefined);

export const totalFrames = () => TITLE_FRAMES + SCENES.reduce((n, [id]) => n + framesOf(id), 0);

/** Karaoke caption: the current sentence, spoken words dark, upcoming words faded. */
const Caption: React.FC = () => {
  const id = useSceneId();
  const frame = useCurrentFrame();
  const t = (frame - LEAD) / FPS;
  const {sentences, words} = timings[id];
  const current = sentences.find((s) => t >= s.start - 0.05 && t < s.end - 0.05);
  if (!current) return null;
  const first = words.findIndex((w) => Math.abs(w.s - current.start) < 0.001);
  const count = current.text.split(' ').length;
  const ws = words.slice(first, first + count);
  const enter = interpolate(t - current.start, [0, 0.18], [0, 1], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 0, right: 0, bottom: 40, display: 'flex', justifyContent: 'center'}}>
      <div style={{
        maxWidth: 1560, background: C.white, border: `5px solid ${C.ink}`, borderRadius: 26, boxShadow: `7px 7px 0 ${C.ink}`,
        padding: '14px 34px', fontFamily: FONT, fontWeight: 600, fontSize: 38, lineHeight: 1.3, textAlign: 'center',
        transform: `translateY(${(1 - enter) * 20}px)`, opacity: 0.4 + 0.6 * enter,
      }}>
        {ws.map((w, i) => {
          const spoken = t >= w.s - 0.02;
          const isNow = spoken && (i === ws.length - 1 || t < ws[i + 1].s);
          return (
            <span key={i} style={{color: isNow ? C.coral : C.ink, opacity: spoken ? 1 : 0.32}}>{w.w}{i < ws.length - 1 ? ' ' : ''}</span>
          );
        })}
      </div>
    </div>
  );
};

/** A circle wipe in the next scene's color, centered on the cut. */
const Iris: React.FC<{color: string}> = ({color}) => {
  const frame = useCurrentFrame();
  const half = 14;
  const r = frame < half
    ? interpolate(frame, [0, half], [0, 1250], {extrapolateRight: 'clamp'})
    : interpolate(frame, [half, half * 2], [1250, 0], {extrapolateLeft: 'clamp'});
  const shrinking = frame >= half;
  return (
    <AbsoluteFill style={{pointerEvents: 'none'}}>
      <svg width={1920} height={1080}>
        <circle cx={shrinking ? 960 : 960} cy={540} r={r} fill={color} stroke={C.ink} strokeWidth={14} />
      </svg>
    </AbsoluteFill>
  );
};

export const Explainer: React.FC = () => {
  let start = TITLE_FRAMES;
  const placed = SCENES.map(([id, Comp, color]) => {
    const from = start;
    start += framesOf(id);
    return {id, Comp, color, from, dur: framesOf(id)};
  });
  return (
    <AbsoluteFill style={{background: C.cream}}>
      <Sequence durationInFrames={TITLE_FRAMES}>
        <TitleScene />
      </Sequence>
      {placed.map(({id, Comp, from, dur}) => (
        <Sequence key={id} from={from} durationInFrames={dur} name={id}>
          <SceneProvider id={id}>
            <Comp />
            <Caption />
          </SceneProvider>
          <Sequence from={LEAD}>
            <Audio src={staticFile(`audio/${id}.mp3`)} />
          </Sequence>
        </Sequence>
      ))}
      {placed.map(({id, color, from}) => (
        <Sequence key={`iris-${id}`} from={from - 14} durationInFrames={28} name={`wipe → ${id}`}>
          <Iris color={color} />
        </Sequence>
      ))}
    </AbsoluteFill>
  );
};
