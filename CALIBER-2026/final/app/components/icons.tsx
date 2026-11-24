import type { ComponentType, CSSProperties } from "react";
import { cn } from "@/lib/format";

/**
 * Duotone icon set (generated with gpt-image-2.5, see design/icon-themes).
 * Drop-in for the lucide-react icons it replaces: same names, same className sizing.
 * Pure UI controls (X, Check, chevrons, arrows, plus/minus, spinner) stay on lucide-react.
 */
export type IconProps = {
  className?: string;
  size?: number | string;
  strokeWidth?: number | string;
  style?: CSSProperties;
  "aria-hidden"?: boolean | "true" | "false";
  "aria-label"?: string;
  title?: string;
};
export type LucideIcon = ComponentType<IconProps>;

function icon(file: string, name: string): LucideIcon {
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  function Icon({ className, size = 24, strokeWidth, style, title, ...aria }: IconProps) {
    return (
      // eslint-disable-next-line @next/next/no-img-element
      <img
        src={`/icons/${file}.png`}
        alt={aria["aria-label"] ?? ""}
        title={title}
        width={size}
        height={size}
        draggable={false}
        decoding="async"
        aria-hidden={aria["aria-label"] ? undefined : true}
        className={cn("inline-block shrink-0 select-none object-contain", className)}
        style={style}
      />
    );
  }
  Icon.displayName = name;
  return Icon;
}

export const Factory = icon("factory", "Factory");
export const Wrench = icon("wrench", "Wrench");
export const Package = icon("package", "Package");
export const Truck = icon("truck", "Truck");
export const Gauge = icon("gauge", "Gauge");
export const CalendarDays = icon("calendar-days", "CalendarDays");
export const ShieldCheck = icon("shield-check", "ShieldCheck");
export const OctagonAlert = icon("octagon-alert", "OctagonAlert");
export const Coins = icon("coins", "Coins");
export const TrendingUp = icon("trending-up", "TrendingUp");
export const Search = icon("search", "Search");
export const Cog = icon("cog", "Cog");
export const Flame = icon("flame", "Flame");
export const Droplet = icon("droplet", "Droplet");
export const Zap = icon("zap", "Zap");
export const ShoppingCart = icon("shopping-cart", "ShoppingCart");
export const Activity = icon("activity", "Activity");
export const Anchor = icon("anchor", "Anchor");
export const Archive = icon("archive", "Archive");
export const ArrowLeftRight = icon("arrow-left-right", "ArrowLeftRight");
export const BadgeCheck = icon("badge-check", "BadgeCheck");
export const Box = icon("box", "Box");
export const Boxes = icon("boxes", "Boxes");
export const BrickWall = icon("brick-wall", "BrickWall");
export const Bug = icon("bug", "Bug");
export const Cable = icon("cable", "Cable");
export const CalendarClock = icon("calendar-clock", "CalendarClock");
export const CalendarX2 = icon("calendar-x-2", "CalendarX2");
export const ChartColumn = icon("chart-column", "ChartColumn");
export const ChartLine = icon("chart-line", "ChartLine");
export const CheckCheck = icon("check-check", "CheckCheck");
export const CheckCircle2 = icon("check-circle-2", "CheckCircle2");
export const Circle = icon("circle", "Circle");
export const CircleAlert = icon("circle-alert", "CircleAlert");
export const CircleCheck = icon("circle-check", "CircleCheck");
export const CircleDashed = icon("circle-dashed", "CircleDashed");
export const CircleDot = icon("circle-dot", "CircleDot");
export const Clock = icon("clock", "Clock");
export const Clock3 = icon("clock-3", "Clock3");
export const Compass = icon("compass", "Compass");
export const Copy = icon("copy", "Copy");
export const CornerDownRight = icon("corner-down-right", "CornerDownRight");
export const Disc = icon("disc", "Disc");
export const Droplets = icon("droplets", "Droplets");
export const Eye = icon("eye", "Eye");
export const Fan = icon("fan", "Fan");
export const Filter = icon("filter", "Filter");
export const GitFork = icon("git-fork", "GitFork");
export const Grid3x3 = icon("grid-3x-3", "Grid3x3");
export const History = icon("history", "History");
export const Hourglass = icon("hourglass", "Hourglass");
export const Layers = icon("layers", "Layers");
export const Lightbulb = icon("lightbulb", "Lightbulb");
export const Link2 = icon("link-2", "Link2");
export const ListFilter = icon("list-filter", "ListFilter");
export const ListTodo = icon("list-todo", "ListTodo");
export const MapPin = icon("map-pin", "MapPin");
export const PackageCheck = icon("package-check", "PackageCheck");
export const Plug = icon("plug", "Plug");
export const Receipt = icon("receipt", "Receipt");
export const Repeat = icon("repeat", "Repeat");
export const RotateCcw = icon("rotate-ccw", "RotateCcw");
export const RotateCw = icon("rotate-cw", "RotateCw");
export const Route = icon("route", "Route");
export const Ruler = icon("ruler", "Ruler");
export const Scale = icon("scale", "Scale");
export const Scroll = icon("scroll", "Scroll");
export const ShieldAlert = icon("shield-alert", "ShieldAlert");
export const Sigma = icon("sigma", "Sigma");
export const Siren = icon("siren", "Siren");
export const SlidersHorizontal = icon("sliders-horizontal", "SlidersHorizontal");
export const Snowflake = icon("snowflake", "Snowflake");
export const Spline = icon("spline", "Spline");
export const SprayCan = icon("spray-can", "SprayCan");
export const Tag = icon("tag", "Tag");
export const Target = icon("target", "Target");
export const Thermometer = icon("thermometer", "Thermometer");
export const ToggleLeft = icon("toggle-left", "ToggleLeft");
export const TrendingDown = icon("trending-down", "TrendingDown");
export const Undo2 = icon("undo-2", "Undo2");
export const Unlink = icon("unlink", "Unlink");
export const Wallet = icon("wallet", "Wallet");
export const Waves = icon("waves", "Waves");
export const Wind = icon("wind", "Wind");
export const Workflow = icon("workflow", "Workflow");
