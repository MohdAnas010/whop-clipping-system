import React from 'react';
import {AbsoluteFill, OffthreadVideo, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';

export type SourceClipProps = {
  source: string;
  start: number;
  duration: number;
  hook?: string;
  fit?: 'contain' | 'cover';
  subtitles?: {start: number; end: number; text: string}[];
};

export const SourceClip: React.FC<SourceClipProps> = ({source, start, hook, fit = 'contain', subtitles = []}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const seconds = frame / fps;
  const subtitle = subtitles.find((cue) => seconds >= cue.start && seconds < cue.end);
  return <AbsoluteFill style={{backgroundColor: '#000', fontFamily: 'Arial, sans-serif'}}>
    <OffthreadVideo src={staticFile(source)} startFrom={Math.round(start * fps)}
      style={{width: '100%', height: '100%', objectFit: fit}} />
    {hook && seconds < 3 ? <div style={{position: 'absolute', top: 170, left: 70, right: 70,
      color: '#fff', background: 'rgba(0,0,0,0.78)', padding: 24, borderRadius: 18,
      textAlign: 'center', fontSize: 54, fontWeight: 800, overflowWrap: 'anywhere'}}>{hook}</div> : null}
    {subtitle ? <div style={{position: 'absolute', bottom: 340, left: 75, right: 75,
      color: '#fff', background: 'rgba(0,0,0,0.78)', padding: 20, borderRadius: 16,
      textAlign: 'center', fontSize: 52, fontWeight: 700, overflowWrap: 'anywhere'}}>{subtitle.text}</div> : null}
  </AbsoluteFill>;
};
