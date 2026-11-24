import { ImageResponse } from "next/og";

export function pwaIcon(size: number) {
  const s = size;
  return new ImageResponse(
    (
      <div style={{ width: s, height: s, display: "flex", alignItems: "center", justifyContent: "center", background: "#0f1e2d" }}>
        <svg width={s * 0.62} height={s * 0.62} viewBox="6 6 20 20">
          <path d="M16 7.5 24 12v8.4L16 25l-8-4.6V12z" fill="none" stroke="white" strokeWidth="1.9" strokeLinejoin="round" />
          <path d="M8 12l8 4.5 8-4.5M16 16.5V25" fill="none" stroke="white" strokeWidth="1.9" strokeLinejoin="round" />
          <path d="M12 9.8l8 4.5" stroke="#f2b33d" strokeWidth="1.9" strokeLinecap="round" />
        </svg>
      </div>
    ),
    { width: s, height: s },
  );
}
