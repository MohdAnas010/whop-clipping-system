import React from 'react';
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

export type ClipProps = {
  hook: string;
  scriptLines: string[];
  caption: string;
  backgroundColor: string;
  accentColor: string;
};

export const ClipComposition: React.FC<ClipProps> = ({
  hook,
  scriptLines,
  caption,
  backgroundColor,
  accentColor,
}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();

  const hookScale = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 120},
  });

  const hookOpacity = interpolate(frame, [0, 15], [0, 1], {
    extrapolateRight: 'clamp',
  });

  return (
    <AbsoluteFill style={{backgroundColor}}>
      {/* Hook - first 3 seconds */}
      <AbsoluteFill
        style={{
          justifyContent: 'center',
          alignItems: 'center',
          padding: 60,
          opacity: hookOpacity,
        }}
      >
        <div
          style={{
            fontSize: 72,
            fontWeight: 900,
            color: '#fff',
            textAlign: 'center',
            lineHeight: 1.2,
            transform: `scale(${hookScale})`,
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {hook}
        </div>
        <div
          style={{
            marginTop: 30,
            height: 8,
            width: 200,
            backgroundColor: accentColor,
            borderRadius: 4,
          }}
        />
      </AbsoluteFill>

      {/* Script lines - kinetic captions */}
      {scriptLines.map((line, i) => {
        const startFrame = 90 + i * 150;
        const endFrame = startFrame + 150;
        const opacity = interpolate(
          frame,
          [startFrame, startFrame + 15, endFrame - 15, endFrame],
          [0, 1, 1, 0],
          {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
        );
        const y = interpolate(frame, [startFrame, startFrame + 20], [60, 0], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        if (frame < startFrame || frame > endFrame) return null;

        return (
          <AbsoluteFill
            key={i}
            style={{
              justifyContent: 'center',
              alignItems: 'center',
              padding: 80,
              opacity,
            }}
          >
            <div
              style={{
                fontSize: 58,
                fontWeight: 700,
                color: '#fff',
                textAlign: 'center',
                lineHeight: 1.3,
                transform: `translateY(${y}px)`,
                fontFamily: 'Inter, sans-serif',
                backgroundColor: 'rgba(0,0,0,0.6)',
                padding: '20px 30px',
                borderRadius: 16,
              }}
            >
              {line}
            </div>
          </AbsoluteFill>
        );
      })}

      {/* Bottom caption bar */}
      <div
        style={{
          position: 'absolute',
          bottom: 120,
          left: 40,
          right: 40,
          opacity: interpolate(frame, [durationInFrames - 30, durationInFrames], [1, 0], {
            extrapolateLeft: 'clamp',
          }),
        }}
      >
        <div
          style={{
            fontSize: 32,
            color: accentColor,
            fontWeight: 600,
            textAlign: 'center',
            fontFamily: 'Inter, sans-serif',
          }}
        >
          {caption}
        </div>
      </div>

      {/* Progress bar */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          height: 10,
          width: `${(frame / durationInFrames) * 100}%`,
          backgroundColor: accentColor,
        }}
      />
    </AbsoluteFill>
  );
};
