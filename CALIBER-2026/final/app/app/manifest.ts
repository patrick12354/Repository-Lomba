import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Sparekit",
    short_name: "Sparekit",
    description: "Spare-part readiness, forecasts and stock decisions for plant maintenance.",
    start_url: "/todo",
    display: "standalone",
    background_color: "#edf0f2",
    theme_color: "#edf0f2",
    icons: [
      { src: "/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
    ],
  };
}
