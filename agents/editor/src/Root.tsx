import React from 'react';
import {Composition} from 'remotion';
import {ClipComposition, ClipProps} from './ClipComposition';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ClipComposition"
        component={ClipComposition}
        durationInFrames={30 * 35}
        fps={30}
        width={1080}
        height={1920}
        defaultProps={{
          hook: 'Ye Whop offer miss mat karo',
          scriptLines: [
            'Ye hai aaj ka top Whop affiliate offer',
            'Commission sun ke hairaan ho jaoge',
            'Link description me hai, abhi check karo',
          ],
          caption: 'Top Whop Offer #affiliate #whop',
          backgroundColor: '#0a0a0a',
          accentColor: '#00ff88',
        } as ClipProps}
      />
    </>
  );
};
