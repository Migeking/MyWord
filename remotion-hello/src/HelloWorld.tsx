import React from "react";
import {
  AbsoluteFill,
  useCurrentFrame,
  interpolate,
  spring,
  useVideoConfig,
} from "remotion";

export const HelloWorld: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 从左边飞入：x 从 -500 到 960 (屏幕中心)
  const translateX = interpolate(frame, [0, 60], [-500, 960], {
    extrapolateRight: "clamp",
  });

  // 旋转效果：从 -180 度到 0 度
  const rotation = interpolate(frame, [0, 90], [-180, 0], {
    extrapolateRight: "clamp",
  });

  // 缩放效果：使用 spring 让动画更有弹性
  const scale = spring({
    frame,
    fps,
    config: {
      damping: 12,
      stiffness: 100,
      mass: 1,
    },
  });

  // 文字样式
  const textStyle: React.CSSProperties = {
    position: "absolute",
    left: translateX,
    top: "50%",
    transform: `translateY(-50%) rotate(${rotation}deg) scale(${scale})`,
    fontSize: 120,
    fontWeight: "bold",
    color: "white",
    textShadow: "0 0 40px rgba(255,255,255,0.5)",
    whiteSpace: "nowrap",
  };

  return (
    <AbsoluteFill
      style={{
        background: "linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%)",
        justifyContent: "center",
        alignItems: "center",
      }}
    >
      <div style={textStyle}>Hello World</div>
    </AbsoluteFill>
  );
};