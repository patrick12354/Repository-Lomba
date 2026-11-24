/**
 * Five pieces of cracker-unit equipment. Each pickable zone carries the part category it stands for,
 * so a click on the bearing housing opens the bearings that are really short in the database.
 */
import * as THREE from "three";
import { add, bake, barrel, barrelY, barrelZ, boltCircle, boltRow, conduit, flange, gateValve, gauge, ibeam, junctionBox, ladder, lathe, makeMats, pipe, plate, rail, rbox, scatter, sweep, walkway, type Mats, type V3 } from "./kit";

export type MachineSlug = "pump" | "compressor" | "turbine" | "furnace" | "exchanger";

export type Zone = { key: string; group: THREE.Group; anchor: THREE.Object3D; inside: boolean };
export type Built = {
  root: THREE.Group;
  zones: Zone[];
  moves: { o: THREE.Object3D; d: THREE.Vector3; home: THREE.Vector3 }[];
  cam: V3;
  look: V3;
};

class Rig {
  root = new THREE.Group();
  zones: Zone[] = [];
  moves: Built["moves"] = [];
  m: Mats;
  constructor(m: Mats) {
    this.m = m;
  }
  /** A group that slides by `d` when the machine opens. */
  part(d: V3 = [0, 0, 0], parent: THREE.Object3D = this.root) {
    const g = new THREE.Group();
    parent.add(g);
    this.moves.push({ o: g, d: new THREE.Vector3(...d), home: new THREE.Vector3() });
    return g;
  }
  /** A pickable zone tied to a part category. The anchor is where its hotspot sits. */
  zone(key: string, anchor: V3, d: V3 = [0, 0, 0], inside = false) {
    const g = this.part(d);
    g.userData.zone = key;
    const a = new THREE.Object3D();
    a.position.set(...anchor);
    g.add(a);
    this.zones.push({ key, group: g, anchor: a, inside });
    return g;
  }
  done(cam: V3, look: V3): Built {
    this.root.traverse((o) => {
      if (o.type === "Group") o.updateMatrix();
    });
    /* merge meshes per group so the detail stays cheap */
    const groups: THREE.Group[] = [];
    this.root.children.forEach((c) => {
      if (c.type === "Group") groups.push(c as THREE.Group);
    });
    groups.forEach((g) => {
      const keep = g.children.filter((c) => !(c as THREE.Mesh).isMesh && c.type !== "Group");
      bake(g);
      keep.forEach((k) => g.add(k));
    });
    return { root: this.root, zones: this.zones, moves: this.moves, cam, look };
  }
}

/** Plinth, anchor bolts and a fabricated I-beam baseplate shared by the rotating machines. */
function skid(r: Rig, g: THREE.Group, w: number, d: number, cx = 0, cz = 0, top = 0.43) {
  const m = r.m;
  add(g, rbox(w + 0.5, 0.2, d + 0.5, 0.03), m.concrete, cx, 0.1, cz);
  add(g, rbox(w + 0.34, 0.03, d + 0.34, 0.01), m.concrete, cx, 0.21, cz);
  const h = top - 0.24;
  for (const s of [-1, 1]) add(g, ibeam(w, h, 0.16, 0.022), m.paintGrey, cx, 0.22 + h / 2, cz + (s * (d - 0.16)) / 2);
  const n = Math.max(3, Math.round(w / 0.8));
  for (let i = 0; i < n; i++) add(g, ibeam(d - 0.2, h * 0.8, 0.1, 0.018).rotateY(Math.PI / 2), m.paintGrey, cx - w / 2 + 0.1 + (i * (w - 0.2)) / (n - 1), 0.22 + h * 0.42, cz);
  add(g, rbox(w, 0.024, d, 0.004), m.paintGrey, cx, top - 0.012, cz);
  /* drip rim and drain */
  for (const s of [-1, 1]) add(g, rbox(w, 0.04, 0.012, 0.002), m.paintGrey, cx, top + 0.018, cz + (s * d) / 2);
  for (const s of [-1, 1]) add(g, rbox(0.012, 0.04, d, 0.002), m.paintGrey, cx + (s * w) / 2, top + 0.018, cz);
  add(g, barrelZ(0.025, 0.1, 14), m.steel, cx + w / 2 - 0.18, top - 0.1, cz + d / 2 + 0.03);
  for (let i = 0; i < n; i++)
    for (const s of [-1, 1]) {
      const x = cx - w / 2 + 0.06 + (i * (w - 0.12)) / (n - 1);
      const z = cz + (s * (d + 0.2)) / 2;
      add(g, new THREE.CylinderGeometry(0.018, 0.018, 0.05, 6), m.bolt, x, 0.25, z);
      add(g, new THREE.CylinderGeometry(0.03, 0.03, 0.01, 12), m.steel, x, 0.228, z);
    }
}

/** Deep-groove ball bearing with real balls, axis along X. */
function ballBearing(parent: THREE.Object3D, m: Mats, x: number, y: number, z: number, od: number, id: number, w: number) {
  const g = new THREE.Group();
  const race = (od + id) / 2;
  add(g, lathe([[-w / 2, od - (od - id) * 0.22], [-w / 2, od], [w / 2, od], [w / 2, od - (od - id) * 0.22], [-w / 2, od - (od - id) * 0.22]], 56), m.machined);
  add(g, lathe([[-w / 2, id], [-w / 2, id + (od - id) * 0.22], [w / 2, id + (od - id) * 0.22], [w / 2, id], [-w / 2, id]], 56), m.machined);
  const n = 12;
  scatter(g, new THREE.SphereGeometry((od - id) * 0.28, 14, 10), m.steel, (i, o) => {
    const a = (i / n) * Math.PI * 2;
    o.position.set(0, Math.cos(a) * race, Math.sin(a) * race);
  }, n);
  g.position.set(x, y, z);
  parent.add(g);
  return g;
}

/** Closed centrifugal impeller: shrouds, hub, backward-curved vanes. Axis along X. */
function impeller(parent: THREE.Object3D, mat: THREE.Material, m: Mats, r: number, w: number, vanes = 7) {
  const g = new THREE.Group();
  add(g, lathe([[-w * 0.5, 0], [-w * 0.5, r * 0.3], [-w * 0.46, r * 0.7], [-w * 0.3, r], [-w * 0.24, r], [-w * 0.36, r * 0.66], [-w * 0.4, 0]], 64), mat);
  add(g, lathe([[w * 0.5, r * 0.36], [w * 0.45, r * 0.36], [w * 0.28, r * 0.62], [w * 0.18, r], [w * 0.24, r], [w * 0.36, r * 0.66], [w * 0.5, r * 0.42], [w * 0.5, r * 0.36]], 64), mat);
  add(g, barrel(r * 0.2, w * 0.95, 28), mat);
  add(g, barrel(r * 0.1, w * 1.05, 18), m.machined);
  const vane = new THREE.BoxGeometry(w * 0.55, r * 0.62, 0.011 + r * 0.012, 1, 8, 1);
  const p = vane.getAttribute("position");
  for (let i = 0; i < p.count; i++) {
    const t = (p.getY(i) + r * 0.31) / (r * 0.62);
    p.setZ(i, p.getZ(i) + t * t * r * 0.3);
  }
  vane.computeVertexNormals();
  scatter(g, vane, mat, (i, o) => {
    o.rotation.x = (i / vanes) * Math.PI * 2;
    o.position.set(0, Math.cos(o.rotation.x) * r * 0.62, Math.sin(o.rotation.x) * r * 0.62);
    o.rotation.x = -o.rotation.x;
  }, vanes);
  parent.add(g);
  return g;
}

/* ------------------------------------------------------------------- pump */

function pump(m: Mats): Built {
  const r = new Rig(m);
  const cy = 1.1;
  const base = r.part();
  skid(r, base, 4.9, 1.34, 0.1, 0);

  /* motor */
  const motor = r.part([-0.45, 0, 0]);
  const mx = -1.35;
  add(motor, barrel(0.5, 1.46, 72, 0.012), m.paintDark, mx, cy, 0);
  const fins = 44;
  scatter(motor, rbox(1.3, 0.065, 0.014, 0.004, 1), m.paintDark, (i, o) => {
    const a = (i / fins) * Math.PI * 2;
    if (Math.abs(a - Math.PI) < 0.25 || a < 0.14 || a > Math.PI * 2 - 0.14) {
      o.scale.setScalar(0);
      return;
    }
    o.position.set(mx, cy + Math.cos(a) * 0.53, Math.sin(a) * 0.53);
    o.rotation.x = -a;
  }, fins);
  /* drive-end shield with bearing boss */
  add(motor, lathe([[0, 0.55], [0.03, 0.56], [0.09, 0.55], [0.12, 0.46], [0.2, 0.28], [0.26, 0.2], [0.26, 0]], 72), m.paintDark, mx + 0.74, cy, 0);
  boltCircle(motor, m.bolt, 8, 0.52, "x", [mx + 0.83, cy, 0], 0.018, 0.02);
  /* non-drive end and fan cowl */
  add(motor, lathe([[0, 0.55], [-0.06, 0.56], [-0.1, 0.5], [-0.1, 0]], 72), m.paintDark, mx - 0.73, cy, 0);
  add(motor, lathe([[-0.12, 0.47], [-0.12, 0.525], [-0.4, 0.52], [-0.47, 0.46], [-0.475, 0.1], [-0.475, 0]], 72), m.paintGrey, mx - 0.73, cy, 0);
  for (let k = 0; k < 6; k++) add(motor, new THREE.TorusGeometry(0.1 + k * 0.058, 0.0065, 8, 56).rotateY(Math.PI / 2), m.black, mx - 1.206, cy, 0);
  scatter(motor, new THREE.BoxGeometry(0.012, 0.36, 0.012), m.black, (i, o) => {
    const a = (i / 10) * Math.PI * 2;
    o.position.set(mx - 1.21, cy + Math.cos(a) * 0.27, Math.sin(a) * 0.27);
    o.rotation.x = -a;
  }, 10);
  /* feet, eyebolt, plate */
  for (const x of [mx - 0.5, mx + 0.5]) for (const s of [-1, 1]) {
    add(motor, rbox(0.3, 0.2, 0.26, 0.012), m.paintDark, x, 0.54, s * 0.4);
    add(motor, rbox(0.34, 0.03, 0.3, 0.004), m.steel, x, 0.45, s * 0.4);
    boltRow(motor, m.boltZinc, [x - 0.1, 0.645, s * 0.42], [x + 0.1, 0.645, s * 0.42], 2, [0, 1, 0], 0.016, 0.03);
  }
  add(motor, new THREE.TorusGeometry(0.05, 0.015, 10, 24), m.steel, mx - 0.35, cy + 0.65, 0);
  add(motor, barrelY(0.022, 0.08, 10), m.steel, mx - 0.35, cy + 0.58, 0);
  plate(motor, ["KM-PP-1022", "90 kW  380V  50Hz", "2975 r/min  IP55"], [mx - 0.1, cy + 0.26, 0.47], 0.26, [0, 0.45, 1]);

  /* terminal box */
  const term = r.zone("TERMINAL", [mx + 0.2, cy + 0.74, 0.16], [0, 0.24, 0]);
  junctionBox(term, m, [mx + 0.2, cy + 0.62, 0.05], [0.42, 0.18, 0.36], m.paintDark);
  conduit(term, m, [[mx + 0.34, cy + 0.54, 0.26], [mx + 0.6, cy + 0.34, 0.68], [mx + 0.7, 0.8, 0.74], [mx + 0.76, 0.46, 0.68]], 0.018);

  /* grease nipples on the motor bearings */
  const grease = r.zone("GREASE", [mx + 0.82, cy + 0.32, 0.3]);
  add(grease, barrelY(0.012, 0.05, 10), m.brass, mx + 0.82, cy + 0.32, 0.3);
  add(grease, new THREE.SphereGeometry(0.015, 10, 8), m.brass, mx + 0.82, cy + 0.36, 0.3);

  /* coupling, then the guard over it */
  const coupling = r.part();
  add(coupling, barrel(0.05, 2.6, 24), m.machined, 0.05, cy, 0);
  add(coupling, lathe([[-0.11, 0], [-0.11, 0.12], [-0.09, 0.15], [0.07, 0.15], [0.09, 0.18], [0.11, 0.18], [0.11, 0]], 48), m.steel, -0.42, cy, 0);
  add(coupling, lathe([[-0.11, 0], [-0.11, 0.18], [-0.09, 0.18], [-0.07, 0.15], [0.09, 0.15], [0.11, 0.12], [0.11, 0]], 48), m.steel, 0.02, cy, 0);
  add(coupling, barrel(0.07, 0.26, 24), m.steel, -0.2, cy, 0);
  boltCircle(coupling, m.bolt, 8, 0.15, "x", [-0.31, cy, 0], 0.013, 0.02);
  boltCircle(coupling, m.bolt, 8, 0.15, "-x", [-0.09, cy, 0], 0.013, 0.02);
  const guard = r.part([0, 0.72, 0.46]);
  add(guard, lathe([[-0.34, 0.3], [-0.34, 0.33], [-0.31, 0.33], [-0.3, 0.3], [0.3, 0.3], [0.31, 0.33], [0.34, 0.33], [0.34, 0.3]], 48), m.guard, -0.2, cy, 0);
  scatter(guard, new THREE.CylinderGeometry(0.008, 0.008, 0.012, 8).rotateZ(Math.PI / 2), m.black, (i, o) => {
    o.position.set(-0.38 + ((i % 8) * 0.052), cy + 0.3, 0);
  }, 0);
  for (const s of [-1, 1]) add(guard, rbox(0.72, 0.024, 0.024, 0.002), m.guard, -0.2, cy - 0.27, s * 0.13);
  add(guard, rbox(0.1, 0.34, 0.4, 0.004), m.guard, -0.2, 0.62, 0);

  /* bearing frame */
  const frame = r.part();
  const fx = 0.54;
  add(frame, lathe([[-0.38, 0.26], [-0.36, 0.28], [-0.3, 0.28], [-0.28, 0.25], [0.26, 0.25], [0.28, 0.3], [0.38, 0.3], [0.4, 0.26]], 64), m.cast, fx, cy, 0);
  scatter(frame, rbox(0.5, 0.05, 0.012, 0.003, 1), m.cast, (i, o) => {
    const a = (i / 10) * Math.PI * 2;
    o.position.set(fx, cy + Math.cos(a) * 0.272, Math.sin(a) * 0.272);
    o.rotation.x = -a;
  }, 10);
  add(frame, rbox(0.86, 0.4, 0.66, 0.02), m.cast, fx, 0.63, 0);
  add(frame, rbox(1.0, 0.03, 0.8, 0.005), m.steel, fx, 0.45, 0);
  for (const s of [-1, 1]) boltRow(frame, m.boltZinc, [fx - 0.34, 0.47, s * 0.36], [fx + 0.34, 0.47, s * 0.36], 3, [0, 1, 0], 0.018, 0.03);
  plate(frame, ["PP-1022", "API 610 OH2  3x4-13", "Q 180 m3/h  H 92 m"], [fx, 0.68, 0.335], 0.3);

  /* bearings slide up out of the frame */
  const bearing = r.zone("BEARING", [fx, cy + 0.33, 0.18], [0, 0.82, 0], false);
  ballBearing(bearing, m, fx - 0.26, cy, 0, 0.17, 0.065, 0.075);
  ballBearing(bearing, m, fx + 0.26, cy, 0, 0.17, 0.065, 0.075);
  add(bearing, barrel(0.16, 0.02, 40), m.brass, fx - 0.37, cy, 0);
  add(bearing, lathe([[-0.02, 0.07], [-0.02, 0.21], [0.02, 0.21], [0.02, 0.07]], 48), m.brass, fx - 0.4, cy, 0);
  boltCircle(bearing, m.bolt, 6, 0.235, "-x", [fx - 0.385, cy, 0], 0.012, 0.015);

  /* lube oil: constant level oiler, sight glass, breather, drain */
  const oil = r.zone("OIL", [fx + 0.1, cy - 0.06, 0.42]);
  pipe(oil, m.brass, [[fx + 0.1, cy - 0.17, 0.27], [fx + 0.1, cy - 0.17, 0.42], [fx + 0.1, cy - 0.1, 0.42]], 0.012);
  add(oil, new THREE.SphereGeometry(0.058, 22, 16).scale(1, 1.3, 1), m.glass, fx + 0.1, cy, 0.42);
  add(oil, new THREE.SphereGeometry(0.05, 18, 12).scale(1, 0.7, 1), m.oil, fx + 0.1, cy - 0.04, 0.42);
  add(oil, barrelY(0.04, 0.03, 18), m.steel, fx + 0.1, cy - 0.09, 0.42);
  add(oil, barrelZ(0.05, 0.02, 24), m.steel, fx - 0.16, cy - 0.12, 0.27);
  add(oil, new THREE.CircleGeometry(0.038, 20), m.oil, fx - 0.16, cy - 0.12, 0.281);
  add(oil, barrelY(0.03, 0.05, 12), m.brass, fx - 0.1, cy + 0.31, 0);
  add(oil, new THREE.SphereGeometry(0.036, 12, 8), m.steel, fx - 0.1, cy + 0.35, 0);

  /* mechanical seal: gland plate and seal sleeve, with its O-rings */
  const seal = r.zone("O-RING", [1.03, cy + 0.24, 0.14], [0.16, 0.96, 0]);
  add(seal, barrel(0.19, 0.07, 48), m.steel, 1.02, cy, 0);
  add(seal, barrel(0.13, 0.12, 36), m.machined, 0.92, cy, 0);
  for (const x of [0.88, 0.95, 1.06]) add(seal, new THREE.TorusGeometry(0.135, 0.012, 12, 48).rotateY(Math.PI / 2), m.rubber, x, cy, 0);
  boltCircle(seal, m.boltZinc, 4, 0.155, "-x", [0.985, cy, 0], 0.016, 0.03, 0);
  const flush = r.part();
  pipe(flush, m.steel, [[1.28, cy + 0.46, 0.36], [1.1, cy + 0.32, 0.36], [1.02, cy + 0.19, 0.3], [1.02, cy + 0.14, 0.12]], 0.011, 0.04);

  /* volute casing with a real spiral into the tangential discharge */
  const casing = r.part();
  const path: V3[] = [];
  const nSpiral = 110;
  for (let i = 0; i <= nSpiral; i++) {
    const t = i / nSpiral;
    const th = Math.PI / 2 + Math.PI * 2 * 0.985 * (1 - t);
    const R = 0.37 + 0.11 * t;
    path.push([0, Math.cos(th) * R, Math.sin(th) * R]);
  }
  const endZ = 0.48;
  for (let i = 1; i <= 20; i++) path.push([0, (i / 20) * 0.64, endZ]);
  const rr = (t: number) => {
    const q = t / (nSpiral / (nSpiral + 20));
    return q < 1 ? 0.06 + 0.13 * q : 0.19 - (q - 1) * 0.08;
  };
  add(casing, sweep(path, rr, 0.92, 36), m.paint, 1.36, cy, 0);
  add(casing, lathe([[-0.17, 0], [-0.17, 0.26], [-0.11, 0.42], [0.0, 0.44], [0.13, 0.42], [0.13, 0]], 72), m.paint, 1.36, cy, 0);
  add(casing, barrel(0.28, 0.1, 48), m.paint, 1.17, cy, 0);
  /* casing back cover to frame */
  add(casing, lathe([[-0.05, 0], [-0.05, 0.31], [0.05, 0.31], [0.05, 0]], 48), m.paint, 1.14, cy, 0);
  boltCircle(casing, m.boltZinc, 10, 0.28, "-x", [1.09, cy, 0], 0.016, 0.02);
  /* centreline feet */
  for (const s of [-1, 1]) {
    add(casing, rbox(0.26, 0.5, 0.2, 0.012), m.paint, 1.36, 0.67, s * 0.34);
    add(casing, rbox(0.34, 0.03, 0.3, 0.004), m.steel, 1.36, 0.445, s * 0.34);
    boltRow(casing, m.boltZinc, [1.28, 0.47, s * 0.36], [1.44, 0.47, s * 0.36], 2, [0, 1, 0], 0.018, 0.03);
  }
  /* cast ribs on the volute */
  for (let i = 0; i < 6; i++) {
    const a = (i / 6) * Math.PI * 2 + 0.4;
    const b = add(casing, rbox(0.03, 0.12, 0.05, 0.006), m.paint, 1.36, cy + Math.cos(a) * 0.44, Math.sin(a) * 0.44);
    b.rotation.x = -a;
  }
  /* vent, drain, lifting lug */
  add(casing, barrelY(0.02, 0.06, 12), m.steel, 1.36, cy - 0.57, 0.08);
  add(casing, new THREE.CylinderGeometry(0.03, 0.03, 0.02, 6), m.steel, 1.36, cy - 0.61, 0.08);
  /* discharge nozzle */
  const ny = cy + 0.64;
  add(casing, barrelY(0.135, 0.1, 40), m.paint, 1.36, ny, endZ);
  /* discharge spool, gasket and flanges */
  const gasketZone = r.zone("GASKET", [1.36, ny + 0.17, endZ + 0.22]);
  flange(gasketZone, m, { bore: 0.13, od: 0.235, t: 0.04, neck: 0.03, bolts: 8, at: [1.36, ny + 0.12, endZ], dir: "y" });
  flange(gasketZone, m, { bore: 0.13, od: 0.235, t: 0.04, neck: 0.1, bolts: 8, mat: m.paintGrey, at: [1.36, ny + 0.21, endZ], dir: "-y" });
  const spool = r.part();
  add(spool, barrelY(0.128, 0.42, 40), m.paintGrey, 1.36, ny + 0.51, endZ);
  add(spool, new THREE.TorusGeometry(0.13, 0.008, 8, 32).rotateX(Math.PI / 2), m.steel, 1.36, ny + 0.32, endZ);
  pipe(spool, m.steel, [[1.36, ny + 0.48, endZ + 0.12], [1.36, ny + 0.48, endZ + 0.26], [1.36, ny + 0.56, endZ + 0.26]], 0.012, 0.04);
  gauge(spool, m, [1.36, ny + 0.64, endZ + 0.26], 0.07, [0, -1, 0], [0.3, 0.1, 1]);

  /* impeller */
  const imp = r.zone("IMPELLER", [1.46, cy + 0.27, 0.12], [0.86, 0, 0], true);
  const ig = impeller(imp, m.brass, m, 0.33, 0.2, 7);
  ig.position.set(1.46, cy, 0);
  add(imp, barrel(0.05, 0.05, 6, 0.008), m.machined, 1.59, cy, 0);

  /* casing cover and suction */
  const cover = r.part([1.75, 0, 0]);
  add(cover, lathe([[-0.06, 0], [-0.06, 0.5], [0.055, 0.5], [0.075, 0.46], [0.09, 0.3], [0.2, 0.17], [0.34, 0.15], [0.34, 0]], 72), m.paint, 1.56, cy, 0);
  const suction = r.zone("FLANGE", [2.0, cy + 0.2, 0.15], [1.75, 0, 0]);
  flange(suction, m, { bore: 0.15, od: 0.26, t: 0.04, neck: 0.03, bolts: 12, at: [1.92, cy, 0] });
  flange(suction, m, { bore: 0.15, od: 0.26, t: 0.04, neck: 0.08, bolts: 12, mat: m.paintGrey, at: [2.02, cy, 0], dir: "-x" });
  const sp = r.part([1.75, 0, 0]);
  pipe(sp, m.paintGrey, [[2.05, cy, 0], [2.42, cy, 0], [2.42, cy - 0.5, 0]], 0.145, 0.22);
  add(sp, barrelY(0.2, 0.05, 40), m.paintGrey, 2.42, cy - 0.52, 0);
  const studs = r.zone("STUDBOLT", [1.5, cy + 0.46, 0.08], [1.75, 0, 0]);
  boltCircle(studs, m.boltZinc, 16, 0.46, "x", [1.615, cy, 0], 0.024, 0.13);

  return r.done([2.6, 3.9, 8.8], [0.2, 1.0, 0]);
}

/* -------------------------------------------------------------- compressor */

function compressor(m: Mats): Built {
  const r = new Rig(m);
  const cy = 1.42;
  const base = r.part();
  skid(r, base, 5.8, 2.7, -0.1, 0.35);

  /* barrel casing */
  const casing = r.part();
  add(casing, lathe([[-1.0, 0], [-1.0, 0.62], [-0.97, 0.66], [-0.82, 0.66], [-0.8, 0.61], [0.72, 0.61], [0.74, 0.66], [0.94, 0.66], [0.96, 0.62], [0.96, 0]], 96), m.paint, 0, cy, 0);
  /* bands from the forging */
  for (const x of [-0.3, 0.26]) add(casing, new THREE.TorusGeometry(0.615, 0.012, 10, 96).rotateY(Math.PI / 2), m.paint, x, cy, 0);
  /* support feet at the centreline */
  for (const x of [-0.75, 0.75]) for (const s of [-1, 1]) {
    add(casing, rbox(0.4, 0.14, 0.5, 0.014), m.paint, x, cy - 0.15, s * 0.62);
    add(casing, rbox(0.36, cy - 0.57, 0.3, 0.012), m.paintGrey, x, (cy - 0.22 + 0.43) / 2, s * 0.66);
    boltRow(casing, m.boltZinc, [x - 0.12, cy - 0.07, s * 0.7], [x + 0.12, cy - 0.07, s * 0.7], 2, [0, 1, 0], 0.024, 0.05);
  }
  /* nozzle pads and stubs */
  add(casing, barrelY(0.36, 0.16, 56), m.paint, -0.42, cy + 0.6, 0);
  add(casing, barrelY(0.27, 0.36, 48), m.paint, -0.42, cy + 0.82, 0);
  add(casing, barrelY(0.28, 0.14, 52), m.paint, 0.42, cy + 0.6, 0);
  add(casing, barrelY(0.2, 0.34, 40), m.paint, 0.42, cy + 0.82, 0);
  /* casing drains and thermowells */
  for (const x of [-0.5, 0.5]) add(casing, barrelY(0.03, 0.1, 12), m.steel, x, cy - 0.64, 0);
  plate(casing, ["KC-391D", "Charge gas compressor", "PD 34 bar  11,400 r/min"], [-0.05, cy + 0.2, 0.585], 0.36, [0, 0.32, 1]);

  /* suction and discharge lines with gaskets at the flanges */
  const gasket = r.zone("GASKET", [-0.42, cy + 1.05, 0.34]);
  flange(gasket, m, { bore: 0.25, od: 0.4, t: 0.06, neck: 0.03, bolts: 16, at: [-0.42, cy + 1.0, 0], dir: "y" });
  flange(gasket, m, { bore: 0.25, od: 0.4, t: 0.06, neck: 0.1, bolts: 16, mat: m.paintGrey, at: [-0.42, cy + 1.14, 0], dir: "-y" });
  flange(gasket, m, { bore: 0.18, od: 0.31, t: 0.055, neck: 0.03, bolts: 12, at: [0.42, cy + 1.0, 0], dir: "y" });
  flange(gasket, m, { bore: 0.18, od: 0.31, t: 0.055, neck: 0.1, bolts: 12, mat: m.paintGrey, at: [0.42, cy + 1.14, 0], dir: "-y" });
  const lines = r.part();
  pipe(lines, m.insul, [[-0.42, cy + 1.14, 0], [-0.42, cy + 1.72, 0], [-0.42, cy + 1.72, -1.5]], 0.25, 0.42);
  pipe(lines, m.paintGrey, [[0.42, cy + 1.14, 0], [0.42, cy + 1.5, 0], [0.42, cy + 1.5, -1.5]], 0.18, 0.3);
  for (let i = 0; i < 5; i++) add(lines, new THREE.TorusGeometry(0.255, 0.006, 6, 40).rotateY(Math.PI / 2).rotateY(Math.PI / 2), m.steel, -0.42, cy + 1.72, -0.5 - i * 0.2);
  gauge(lines, m, [-0.1, cy + 1.45, 0], 0.07, [-1, 0, 0], [0.2, 0.1, 1]);
  pipe(lines, m.steel, [[-0.42 + 0.24, cy + 1.45, 0], [-0.17, cy + 1.45, 0]], 0.012);

  /* rotor bundle: shaft, stages, balance drum */
  const rotor = r.part([1.5, 0, 0]);
  add(rotor, barrel(0.085, 3.3, 28), m.machined, 0, cy, 0);
  for (let i = 0; i < 6; i++) {
    const ig = impeller(rotor, m.steel, m, 0.48, 0.16, 11);
    ig.position.set(-0.68 + i * 0.27, cy, 0);
    add(rotor, lathe([[-0.05, 0.1], [-0.05, 0.56], [0.05, 0.56], [0.05, 0.1]], 56), m.cast, -0.55 + i * 0.27, cy, 0);
  }
  add(rotor, barrel(0.2, 0.2, 40), m.steel, 0.95, cy, 0);
  rotor.visible = true;

  /* drive-side bearing housing */
  const brgL = r.zone("BEARING", [-1.38, cy + 0.4, 0.15], [0, 0.85, 0]);
  add(brgL, lathe([[-0.24, 0.15], [-0.24, 0.3], [-0.2, 0.34], [0.2, 0.34], [0.24, 0.3], [0.24, 0.15]], 56), m.cast, -1.38, cy, 0);
  add(brgL, rbox(0.56, cy - 0.52, 0.86, 0.018), m.cast, -1.38, (cy + 0.43 - 0.08) / 2, 0);
  boltRow(brgL, m.boltZinc, [-1.58, cy + 0.0, 0.36], [-1.18, cy + 0.0, 0.36], 3, [0, 0, 1], 0.02, 0.03);
  boltRow(brgL, m.boltZinc, [-1.58, cy + 0.0, -0.36], [-1.18, cy + 0.0, -0.36], 3, [0, 0, -1], 0.02, 0.03);
  add(brgL, barrelY(0.04, 0.14, 14), m.steel, -1.46, cy + 0.38, 0);
  add(brgL, barrelY(0.03, 0.1, 10), m.brass, -1.28, cy + 0.38, 0.05);

  /* non-drive end assembly that withdraws with the end cover */
  const brgR = r.zone("BEARING", [1.5, cy + 0.42, 0], [2.1, 0, 0]);
  add(brgR, lathe([[-0.26, 0], [-0.26, 0.36], [-0.2, 0.4], [0.2, 0.4], [0.3, 0.3], [0.3, 0]], 56), m.cast, 1.5, cy, 0);
  add(brgR, barrelY(0.03, 0.12, 12), m.steel, 1.5, cy + 0.44, 0);
  conduit(brgR, m, [[1.5, cy + 0.5, 0], [1.6, cy + 0.6, 0.4], [1.8, cy + 0.2, 0.7], [1.9, 0.6, 0.7]], 0.012);

  const cover = r.zone("O-RING", [1.08, cy + 0.3, 0.45], [2.1, 0, 0]);
  add(cover, lathe([[-0.1, 0], [-0.1, 0.59], [0.1, 0.6], [0.14, 0.56], [0.14, 0.34], [0.26, 0.28], [0.26, 0]], 72), m.paint, 1.06, cy, 0);
  for (const x of [0.97, 1.0]) add(cover, new THREE.TorusGeometry(0.595, 0.012, 10, 72).rotateY(Math.PI / 2), m.rubber, x, cy, 0);
  const studs = r.zone("STUDBOLT", [1.12, cy + 0.52, 0], [2.1, 0, 0]);
  boltCircle(studs, m.boltZinc, 36, 0.5, "x", [1.2, cy, 0], 0.024, 0.24);
  const seal = r.zone("SEAL", [1.25, cy + 0.22, 0.2], [2.1, 0, 0]);
  add(seal, barrel(0.22, 0.14, 44), m.machined, 1.26, cy, 0);
  for (const x of [1.21, 1.26, 1.31]) add(seal, new THREE.TorusGeometry(0.226, 0.006, 8, 44).rotateY(Math.PI / 2), m.brass, x, cy, 0);
  /* dry-gas seal tubing */
  for (let i = 0; i < 3; i++) pipe(seal, m.steel, [[1.25 + i * 0.03, cy + 0.2, 0.08 * i], [1.3 + i * 0.03, cy + 0.34, 0.2 + i * 0.05], [1.3 + i * 0.03, cy + 0.34, 0.72], [1.3 + i * 0.03, 0.74, 0.72]], 0.008, 0.05);

  /* coupling */
  const coupling = r.zone("COUPLING", [-2.0, cy + 0.32, 0.1], [0, 0.0, 0]);
  add(coupling, lathe([[-0.17, 0], [-0.17, 0.17], [-0.12, 0.22], [0.12, 0.22], [0.17, 0.17], [0.17, 0]], 44), m.steel, -1.8, cy, 0);
  add(coupling, lathe([[-0.17, 0], [-0.17, 0.17], [-0.12, 0.22], [0.12, 0.22], [0.17, 0.17], [0.17, 0]], 44), m.steel, -2.3, cy, 0);
  add(coupling, barrel(0.09, 0.42, 22), m.machined, -2.05, cy, 0);
  for (const x of [-1.95, -2.15]) add(coupling, barrel(0.21, 0.02, 40), m.machined, x, cy, 0);
  boltCircle(coupling, m.bolt, 10, 0.17, "x", [-1.97, cy, 0], 0.014, 0.02);
  boltCircle(coupling, m.bolt, 10, 0.17, "-x", [-2.13, cy, 0], 0.014, 0.02);
  const guard = r.part([0, 1.1, 0]);
  add(guard, lathe([[-0.55, 0.3], [-0.55, 0.34], [-0.52, 0.34], [-0.5, 0.31], [0.5, 0.31], [0.52, 0.34], [0.55, 0.34], [0.55, 0.3]], 52), m.guard, -2.05, cy, 0);
  add(guard, rbox(1.08, 0.5, 0.62, 0.012), m.guard, -2.05, 0.73, 0);

  /* driver stub: gearbox casting into frame */
  const drive = r.part();
  add(drive, rbox(0.95, 1.5, 1.5, 0.05), m.paintGrey, -2.95, 1.2, 0);
  add(drive, barrel(0.22, 0.2, 40), m.steel, -2.42, cy, 0);
  add(drive, rbox(1.0, 0.04, 1.56, 0.008), m.paintGrey, -2.95, 1.42, 0);
  boltRow(drive, m.boltZinc, [-3.35, 1.45, 0.72], [-2.55, 1.45, 0.72], 6, [0, 1, 0], 0.02, 0.04);
  boltRow(drive, m.boltZinc, [-3.35, 1.45, -0.72], [-2.55, 1.45, -0.72], 6, [0, 1, 0], 0.02, 0.04);
  add(drive, rbox(0.5, 0.05, 0.5, 0.01), m.steel, -2.95, 1.97, 0);
  boltCircle(drive, m.boltZinc, 8, 0.2, "y", [-2.95, 1.995, 0], 0.014, 0.02);

  /* lube oil console on the skid front */
  const oil = r.zone("OIL", [-1.15, 1.08, 1.32], [0, 0, 0.5]);
  add(oil, rbox(1.56, 0.6, 0.8, 0.02), m.paintGrey, -1.1, 0.75, 1.2);
  add(oil, rbox(1.6, 0.03, 0.84, 0.005), m.paintGrey, -1.1, 1.06, 1.2);
  add(oil, barrelZ(0.06, 0.02, 24), m.steel, -1.6, 0.75, 1.6);
  add(oil, new THREE.CircleGeometry(0.048, 22), m.oil, -1.6, 0.75, 1.612);
  add(oil, barrelY(0.06, 0.05, 20), m.steel, -0.6, 1.1, 1.0);
  pipe(oil, m.steel, [[-1.38, 1.06, 0.96], [-1.38, cy - 0.35, 0.6], [-1.38, cy - 0.35, 0.34]], 0.02, 0.06);
  pipe(oil, m.steel, [[-0.3, 0.9, 0.8], [0.95, 0.72, 0.8], [1.45, 0.72, 0.4], [1.45, cy - 0.38, 0.32]], 0.018, 0.08);
  /* filter canisters with changeover valve */
  const filt = r.zone("FILTER ELEMENT", [-0.82, 1.52, 1.25], [0, 0.42, 0.5]);
  for (const [x, t] of [[-0.98, 0], [-0.66, 1]] as const) {
    add(filt, barrelY(0.13, 0.5, 36), t ? m.paintDark : m.paintDark, x, 1.34, 1.2);
    add(filt, lathe([[0, 0.14], [0.03, 0.15], [0.06, 0.13], [0.09, 0.05], [0.09, 0]], 36).rotateZ(Math.PI / 2), m.paintDark, x, 1.6, 1.2);
    boltCircle(filt, m.boltZinc, 8, 0.12, "y", [x, 1.59, 1.2], 0.011, 0.02);
  }
  add(filt, barrel(0.05, 0.42, 20), m.steel, -0.82, 1.14, 1.2);
  add(filt, barrelY(0.03, 0.14, 10), m.red, -0.82, 1.24, 1.2);
  add(filt, rbox(0.26, 0.018, 0.03, 0.004), m.red, -0.82, 1.31, 1.2);
  gauge(filt, m, [-0.82, 1.5, 1.2], 0.055, [0, -1, 0], [0.1, 0.2, 1]);
  /* oil pump and small motor */
  const lube = r.part([0, 0, 0.5]);
  add(lube, barrelZ(0.1, 0.28, 28), m.paintDark, -0.25, 0.86, 1.2);
  add(lube, rbox(0.32, 0.08, 0.3, 0.008), m.paintGrey, -0.25, 0.72, 1.2);
  add(lube, barrelZ(0.075, 0.13, 22), m.paintGrey, -0.25, 0.86, 1.03);

  /* instrument junction box */
  const jb = r.zone("TERMINAL", [0.62, 1.1, 1.04]);
  junctionBox(jb, m, [0.62, 0.92, 1.05], [0.46, 0.5, 0.2], m.paintLight);
  for (let i = 0; i < 3; i++) conduit(jb, m, [[0.5 + i * 0.1, 0.62, 1.05], [0.5 + i * 0.1, 0.5, 0.95], [0.2 + i * 0.4, 0.55, 0.6], [i * 0.5, cy - 0.5, 0.56]], 0.01);

  const grease = r.zone("GREASE", [-1.8, cy + 0.26, 0]);
  add(grease, barrelY(0.012, 0.05, 10), m.brass, -1.8, cy + 0.23, 0);
  add(grease, new THREE.SphereGeometry(0.016, 10, 8), m.brass, -1.8, cy + 0.26, 0);

  return r.done([2.5, 3.6, 10.8], [-0.1, 1.42, 0.2]);
}

/* ----------------------------------------------------------------- turbine */

function halfShell(points: [number, number][], upper: boolean, seg = 64) {
  const pts = points.map(([x, r]) => new THREE.Vector2(r, x));
  const g = new THREE.LatheGeometry(pts, seg, upper ? Math.PI : 0, Math.PI);
  g.rotateZ(-Math.PI / 2);
  return g;
}

function turbine(m: Mats): Built {
  const r = new Rig(m);
  const cy = 1.42;
  const base = r.part();
  skid(r, base, 5.6, 2.3, 0, 0.1);
  const paint2 = m.paint.clone();
  paint2.side = THREE.DoubleSide;

  const profile: [number, number][] = [[-1.42, 0.2], [-1.34, 0.4], [-1.18, 0.46], [-0.5, 0.52], [-0.1, 0.6], [0.45, 0.72], [0.98, 0.86], [1.16, 0.88], [1.3, 0.62], [1.42, 0.24]];

  /* lower casing and its split flange */
  const lower = r.part();
  add(lower, halfShell(profile, false), paint2, 0, cy, 0);
  for (const s of [-1, 1]) {
    const seg = (x0: number, x1: number, z: number) => add(lower, rbox(x1 - x0, 0.06, 0.2, 0.008), m.paint, (x0 + x1) / 2, cy - 0.03, s * z);
    seg(-1.36, -0.5, 0.54);
    seg(-0.5, -0.1, 0.62);
    seg(-0.1, 0.45, 0.72);
    seg(0.45, 1.3, 0.92);
  }
  /* inside glow of the diaphragm steps in the lower half */
  for (let i = 0; i < 9; i++) {
    const x = -1.05 + i * 0.25;
    const rad = 0.42 + i * 0.044;
    add(lower, halfShell([[x - 0.03, rad - 0.06], [x - 0.03, rad - 0.01], [x + 0.03, rad - 0.01], [x + 0.03, rad - 0.06]], false, 48), m.cast, 0, cy, 0);
  }
  for (const x of [-1.0, 1.0]) for (const s of [-1, 1]) add(lower, rbox(0.32, cy - 0.68, 0.36, 0.014), m.paintGrey, x, (cy + 0.43 - 0.25) / 2, s * 0.74);

  /* rotor with blade rows, visible when the upper casing lifts */
  const rotor = r.part();
  add(rotor, barrel(0.15, 3.5, 36), m.machined, 0, cy, 0);
  for (let i = 0; i < 9; i++) {
    const x = -1.05 + i * 0.25;
    const rd = 0.27 + i * 0.022;
    const h = 0.11 + i * 0.022;
    add(rotor, lathe([[-0.03, 0.15], [-0.03, rd - 0.015], [0, rd], [0.03, rd - 0.015], [0.03, 0.15]], 48), m.steel, x, cy, 0);
    const n = 36 + i * 3;
    const blade = new THREE.BoxGeometry(0.03 + i * 0.002, h, 0.011);
    blade.rotateY(0.6);
    scatter(rotor, blade, m.machined, (k, o) => {
      const a = (k / n) * Math.PI * 2;
      o.position.set(x, cy + Math.cos(a) * (rd + h / 2), Math.sin(a) * (rd + h / 2));
      o.rotation.x = -a;
    }, n);
    add(rotor, new THREE.TorusGeometry(rd + h + 0.002, 0.005, 6, 64).rotateY(Math.PI / 2), m.steel, x, cy, 0);
  }

  /* upper casing, which lifts with the steam chest */
  const upper = r.part([0, 1.55, 0]);
  add(upper, halfShell(profile, true), paint2, 0, cy, 0);
  const seg2 = (x0: number, x1: number, z: number, s: number) => add(upper, rbox(x1 - x0, 0.06, 0.2, 0.008), m.paint, (x0 + x1) / 2, cy + 0.03, s * z);
  for (const s of [-1, 1]) {
    seg2(-1.36, -0.5, 0.54, s);
    seg2(-0.5, -0.1, 0.62, s);
    seg2(-0.1, 0.45, 0.72, s);
    seg2(0.45, 1.3, 0.92, s);
  }
  plate(upper, ["KT-264A", "Steam turbine driver", "42 bar  8,200 r/min"], [0.75, cy + 0.42, 0.72], 0.34, [0, 0.55, 1]);
  /* lifting lugs */
  for (const x of [-0.8, 0.8]) add(upper, new THREE.TorusGeometry(0.06, 0.018, 10, 24), m.steel, x, cy + (x < 0 ? 0.56 : 0.9), 0);

  /* split-line studs */
  const bolts = r.zone("STUDBOLT", [0.8, cy + 0.12, 0.92], [0, 1.55, 0]);
  for (const s of [-1, 1]) {
    boltRow(bolts, m.boltZinc, [-1.3, cy + 0.06, s * 0.56], [-0.54, cy + 0.06, s * 0.56], 7, [0, 1, 0], 0.024, 0.12);
    boltRow(bolts, m.boltZinc, [-0.46, cy + 0.06, s * 0.64], [-0.14, cy + 0.06, s * 0.64], 3, [0, 1, 0], 0.024, 0.12);
    boltRow(bolts, m.boltZinc, [-0.06, cy + 0.06, s * 0.74], [0.42, cy + 0.06, s * 0.74], 5, [0, 1, 0], 0.024, 0.12);
    boltRow(bolts, m.boltZinc, [0.5, cy + 0.06, s * 0.94], [1.26, cy + 0.06, s * 0.94], 7, [0, 1, 0], 0.024, 0.12);
  }

  /* steam chest, governor valve, servo */
  add(upper, rbox(0.92, 0.3, 0.62, 0.05), m.paint, -0.72, cy + 0.68, 0);
  boltRow(upper, m.boltZinc, [-1.08, cy + 0.84, 0.25], [-0.36, cy + 0.84, 0.25], 6, [0, 1, 0], 0.016, 0.02);
  boltRow(upper, m.boltZinc, [-1.08, cy + 0.84, -0.25], [-0.36, cy + 0.84, -0.25], 6, [0, 1, 0], 0.016, 0.02);
  for (let i = 0; i < 3; i++) {
    const x = -1.0 + i * 0.28;
    add(upper, barrelY(0.05, 0.32, 18), m.machined, x, cy + 1.0, 0);
    add(upper, barrelY(0.075, 0.03, 18), m.steel, x, cy + 0.86, 0);
  }
  add(upper, rbox(0.86, 0.04, 0.2, 0.008), m.steel, -0.72, cy + 1.18, 0);
  add(upper, barrelY(0.13, 0.42, 30), m.paintDark, -0.72, cy + 1.42, 0);
  add(upper, barrelY(0.145, 0.03, 30), m.steel, -0.72, cy + 1.21, 0);
  add(upper, barrelY(0.145, 0.03, 30), m.steel, -0.72, cy + 1.63, 0);
  conduit(upper, m, [[-0.6, cy + 1.46, 0.08], [-0.28, cy + 1.2, 0.36], [-0.24, cy + 0.8, 0.5]], 0.012);

  /* steam inlet with gasket flange and trip & throttle valve */
  const gasket = r.zone("GASKET", [-0.42, cy + 0.76, 0.84]);
  flange(gasket, m, { bore: 0.12, od: 0.22, t: 0.04, neck: 0.03, bolts: 10, at: [-0.5, cy + 0.68, 0.34], dir: "z" });
  const steam = r.part();
  pipe(steam, m.insul, [[-0.5, cy + 0.68, 0.38], [-0.5, cy + 0.68, 0.98], [-1.4, cy + 0.68, 0.98]], 0.12, 0.18);
  const tt = gateValve(steam, m, [-1.72, cy + 0.68, 0.98], 1.25, { body: m.paintDark });
  tt.rotation.x = 0;
  pipe(steam, m.insul, [[-2.02, cy + 0.68, 0.98], [-2.5, cy + 0.68, 0.98]], 0.12);
  const drainS = r.part();
  gauge(drainS, m, [-1.15, cy + 0.98, 0.98], 0.065, [0, -1, 0], [0.1, 0.1, 1]);
  pipe(drainS, m.steel, [[-1.15, cy + 0.78, 0.98], [-1.15, cy + 0.9, 0.98]], 0.01);

  /* exhaust duct down through the deck with its big flange */
  const exh = r.part();
  add(exh, barrelY(0.42, 0.34, 56), m.paint, 0.72, cy - 0.9, 0);
  const gasket2 = r.zone("GASKET", [0.72, 0.78, 0.5]);
  flange(gasket2, m, { bore: 0.4, od: 0.56, t: 0.05, neck: 0.03, bolts: 24, at: [0.72, 0.72, 0], dir: "-y" });
  /* gland steam line */
  pipe(exh, m.steel, [[1.44, cy - 0.1, 0.1], [1.7, cy - 0.5, 0.42], [1.2, 0.62, 0.84], [0.9, 0.62, 0.84]], 0.022, 0.1);

  /* O-ring end seals on the shaft */
  const ring = r.zone("O-RING", [1.47, cy + 0.2, 0.05], [0.25, 0, 0]);
  add(ring, barrel(0.21, 0.07, 44), m.machined, 1.46, cy, 0);
  for (const x of [1.43, 1.49]) add(ring, new THREE.TorusGeometry(0.215, 0.012, 10, 44).rotateY(Math.PI / 2), m.rubber, x, cy, 0);

  /* front bearing standard with governor box */
  const front = r.zone("BEARING", [-1.92, cy + 0.42, 0.1], [-0.45, 0, 0]);
  add(front, rbox(0.72, cy - 0.36 + 0.42, 0.92, 0.03), m.paintDark, -1.92, (cy + 0.42 + 0.43) / 2 - 0.02, 0);
  add(front, rbox(0.74, 0.03, 0.94, 0.006), m.paintDark, -1.92, cy + 0.08, 0);
  boltRow(front, m.boltZinc, [-2.2, cy + 0.1, 0.42], [-1.64, cy + 0.1, 0.42], 4, [0, 1, 0], 0.018, 0.03);
  boltRow(front, m.boltZinc, [-2.2, cy + 0.1, -0.42], [-1.64, cy + 0.1, -0.42], 4, [0, 1, 0], 0.018, 0.03);
  add(front, barrelY(0.05, 0.14, 16), m.steel, -1.92, cy + 0.5, 0);
  gauge(front, m, [-1.72, cy + 0.2, 0.5], 0.055, [0, 0, -1], [0, 0.1, 1]);
  /* rear bearing and coupling */
  const rear = r.zone("BEARING", [1.82, cy + 0.34, 0.1], [0.6, 0, 0]);
  add(rear, lathe([[-0.17, 0], [-0.17, 0.26], [-0.13, 0.31], [0.13, 0.31], [0.17, 0.26], [0.17, 0]], 44), m.cast, 1.82, cy, 0);
  add(rear, rbox(0.42, cy - 0.45, 0.72, 0.016), m.cast, 1.82, (cy + 0.43) / 2 - 0.02, 0);
  const cg = r.part([0.6, 0.7, 0]);
  add(cg, lathe([[-0.3, 0.27], [-0.3, 0.31], [-0.26, 0.31], [-0.24, 0.28], [0.24, 0.28], [0.26, 0.31], [0.3, 0.31], [0.3, 0.27]], 48), m.guard, 2.32, cy, 0);
  add(cg, rbox(0.56, 0.5, 0.56, 0.01), m.guard, 2.32, 0.72, 0);

  /* duplex oil filter */
  const filt = r.zone("FILTER ELEMENT", [-1.05, 1.15, 1.1], [0, 0.32, 0.38]);
  for (const x of [-1.2, -0.9]) {
    add(filt, barrelY(0.11, 0.42, 30), m.paintDark, x, 0.84, 1.0);
    add(filt, lathe([[0, 0.12], [0.03, 0.125], [0.05, 0.1], [0.07, 0.03], [0.07, 0]], 30).rotateZ(Math.PI / 2), m.paintDark, x, 1.06, 1.0);
    boltCircle(filt, m.boltZinc, 6, 0.105, "y", [x, 1.05, 1.0], 0.01, 0.02);
  }
  add(filt, barrel(0.045, 0.36, 18), m.steel, -1.05, 0.66, 1.0);
  add(filt, rbox(0.24, 0.016, 0.03, 0.004), m.red, -1.05, 0.72, 1.0);
  const oilLines = r.part();
  pipe(oilLines, m.steel, [[-0.9, 0.56, 0.86], [-0.9, 0.56, 0.5], [-1.7, 0.56, 0.5], [-1.7, cy - 0.35, 0.5]], 0.018, 0.07);
  pipe(oilLines, m.steel, [[-1.2, 0.56, 0.86], [-1.2, 0.5, 0.65], [1.7, 0.5, 0.65], [1.8, cy - 0.32, 0.34]], 0.018, 0.07);
  return r.done([2.6, 3.7, 10.6], [-0.05, 1.58, 0]);
}

/* ----------------------------------------------------------------- furnace */

function furnace(m: Mats): Built {
  const r = new Rig(m);
  const base = r.part();
  const W = 4.4;
  const D = 2.0;
  const y0 = 1.05;
  const y1 = 3.25;
  /* foundation and columns */
  add(base, rbox(W + 1.0, 0.16, D + 1.2, 0.03), m.concrete, 0, 0.08, 0);
  for (const x of [-W / 2, -W / 6, W / 6, W / 2]) for (const s of [-1, 1]) {
    add(base, ibeam(y1 + 0.5, 0.16, 0.16, 0.022).rotateZ(Math.PI / 2), m.paintGrey, x, (y1 + 0.5) / 2 + 0.16, (s * D) / 2);
    add(base, rbox(0.3, 0.03, 0.3, 0.005), m.steel, x, 0.175, (s * D) / 2);
    boltRow(base, m.bolt, [x - 0.1, 0.2, (s * D) / 2 - 0.1], [x + 0.1, 0.2, (s * D) / 2 - 0.1], 2, [0, 1, 0], 0.016, 0.03);
    boltRow(base, m.bolt, [x - 0.1, 0.2, (s * D) / 2 + 0.1], [x + 0.1, 0.2, (s * D) / 2 + 0.1], 2, [0, 1, 0], 0.016, 0.03);
  }
  /* floor frame and shell */
  add(base, rbox(W + 0.2, 0.12, D + 0.2, 0.01), m.paintGrey, 0, y0 - 0.06, 0);
  add(base, rbox(W + 0.1, 0.05, D + 0.1, 0.005), m.paintDark, 0, y0 + 0.02, 0);
  const shell = (w: number, h: number, d: number, x: number, y: number, z: number) => add(base, new THREE.BoxGeometry(w, h, d), m.paint, x, y, z);
  const H = y1 - y0;
  const ym = (y0 + y1) / 2;
  shell(W, H, 0.05, 0, ym, -D / 2);
  shell(0.05, H, D, -W / 2, ym, 0);
  shell(0.05, H, D, W / 2, ym, 0);
  add(base, new THREE.BoxGeometry(W + 0.1, 0.06, D + 0.1), m.paint, 0, y1 + 0.03, 0);
  /* stiffeners on the walls that show */
  for (let i = 0; i < 3; i++) add(base, rbox(0.03, 0.08, D, 0.004), m.paintDark, -W / 2 - 0.04, y0 + 0.5 + i * 0.6, 0);
  for (let i = 0; i < 3; i++) add(base, rbox(0.03, 0.08, D, 0.004), m.paintDark, W / 2 + 0.04, y0 + 0.5 + i * 0.6, 0);
  plate(base, ["BF-101", "Cracking furnace", "SRT-III  1100 C"], [W / 2 + 0.058, y0 + 0.28, 0.5], 0.34, [1, 0, 0]);

  /* firebrick lining */
  const brick = r.zone("FIREBRICK", [-1.4, y0 + 0.5, -0.86], [0, 0, 0], true);
  const b = (w: number, h: number, x: number, y: number, z: number, ry = 0, rx = 0) => {
    const g = new THREE.PlaneGeometry(w, h);
    const uv = g.getAttribute("uv");
    for (let i = 0; i < uv.count; i++) uv.setXY(i, (uv.getX(i) * w) / 0.9, (uv.getY(i) * h) / 0.9);
    const p = add(brick, g, m.firebrick, x, y, z);
    p.rotation.set(rx, ry, 0);
    return p;
  };
  b(W - 0.1, 1.12, 0, y0 + 0.6, -D / 2 + 0.06);
  b(D - 0.1, 1.12, -W / 2 + 0.06, y0 + 0.6, 0, Math.PI / 2);
  b(D - 0.1, 1.12, W / 2 - 0.06, y0 + 0.6, 0, -Math.PI / 2);
  b(W - 0.1, D - 0.1, 0, y0 + 0.07, 0, 0, -Math.PI / 2);

  /* ceramic fibre blanket, upper walls */
  const fiber = r.zone("CERAMIC FIBER", [1.5, y0 + 1.72, -0.86], [0, 0, 0], true);
  const fp = (w: number, h: number, x: number, y: number, z: number, ry = 0) => {
    const g = new THREE.BoxGeometry(w, h, 0.05);
    const uv = g.getAttribute("uv");
    for (let i = 0; i < uv.count; i++) uv.setXY(i, (uv.getX(i) * w) / 1.1, (uv.getY(i) * h) / 1.1);
    const p = add(fiber, g, m.fiber, x, y, z);
    p.rotation.y = ry;
  };
  fp(W - 0.1, 1.0, 0, y0 + 1.68, -D / 2 + 0.05);
  fp(D - 0.1, 1.0, -W / 2 + 0.05, y0 + 1.68, 0, Math.PI / 2);
  fp(D - 0.1, 1.0, W / 2 - 0.05, y0 + 1.68, 0, Math.PI / 2);

  /* anchors holding the blanket */
  const anchors = r.zone("ANCHOR", [-1.1, y0 + 1.9, -0.86], [0, 0, 0], true);
  const an = 10 * 3;
  scatter(anchors, new THREE.CylinderGeometry(0.03, 0.03, 0.016, 14).rotateX(Math.PI / 2), m.steel, (i, o) => {
    o.position.set(-W / 2 + 0.34 + (i % 10) * 0.41, y0 + 1.36 + Math.floor(i / 10) * 0.32, -D / 2 + 0.082);
  }, an);
  scatter(anchors, new THREE.CylinderGeometry(0.009, 0.009, 0.04, 8).rotateX(Math.PI / 2), m.machined, (i, o) => {
    o.position.set(-W / 2 + 0.34 + (i % 10) * 0.41, y0 + 1.36 + Math.floor(i / 10) * 0.32, -D / 2 + 0.094);
  }, an);

  /* castable: burner tiles on the floor and the arch */
  const cast = r.zone("CASTABLE", [-0.75, y0 + 0.2, 0.46], [0, 0, 0], true);
  add(cast, rbox(W - 0.1, 0.04, 0.3, 0.008), m.castable, 0, y0 + 2.08, 0);
  const tiles = 10;
  for (const s of [-1, 1]) for (let i = 0; i < tiles; i++) {
    const x = -W / 2 + 0.38 + (i * (W - 0.76)) / (tiles - 1);
    add(cast, lathe([[-0.11, 0.05], [-0.11, 0.14], [0.11, 0.11], [0.11, 0.06], [-0.11, 0.05]], 18).rotateZ(Math.PI / 2), m.castable, x, y0 + 0.17, s * 0.58);
    /* flame core */
    add(cast, new THREE.CylinderGeometry(0.045, 0.045, 0.01, 14), m.black, x, y0 + 0.285, s * 0.58);
  }

  /* serpentine radiant coil */
  const coil = r.part();
  const pts: V3[] = [];
  const nTubes = 16;
  for (let i = 0; i < nTubes; i++) {
    const x = -1.85 + (i * 3.7) / (nTubes - 1);
    const top = y0 + 1.98;
    const bot = y0 + 0.38;
    if (i % 2 === 0) pts.push([x, top, 0], [x, bot, 0]);
    else pts.push([x, bot, 0], [x, top, 0]);
  }
  pipe(coil, m.heat, pts, 0.05, 0.11);
  /* coil guides on the floor */
  scatter(coil, rbox(0.11, 0.1, 0.09, 0.012, 1), m.castable, (i, o) => o.position.set(-1.85 + (i * 3.7) / (nTubes - 1), y0 + 0.13, 0), nTubes);
  /* tube hangers */
  scatter(coil, new THREE.CylinderGeometry(0.008, 0.008, 0.3, 6), m.steel, (i, o) => o.position.set(-1.85 + (i * 3.7) / (nTubes - 1), y0 + 2.08, 0), nTubes);

  /* floor burners beneath: tips, air registers, fuel line */
  const burners = r.part();
  for (const s of [-1, 1]) for (let i = 0; i < tiles; i++) {
    const x = -W / 2 + 0.38 + (i * (W - 0.76)) / (tiles - 1);
    add(burners, barrelY(0.09, 0.34, 18), m.cast, x, y0 - 0.3, s * 0.58);
    add(burners, barrelY(0.12, 0.05, 20), m.paintDark, x, y0 - 0.48, s * 0.58);
    add(burners, barrelY(0.02, 0.2, 10), m.steel, x, y0 - 0.6, s * 0.58);
  }

  /* fuel gas manifold under the floor */
  const pipes = r.zone("PIPE", [-1.5, 0.42, 0.75]);
  for (const s of [-1, 1]) {
    add(pipes, barrel(0.06, W + 0.5, 22), m.paintGrey, 0, 0.42, s * 0.58);
    for (let i = 0; i < tiles; i++) {
      const x = -W / 2 + 0.38 + (i * (W - 0.76)) / (tiles - 1);
      add(pipes, barrelY(0.018, 0.14, 8), m.paintGrey, x, 0.5, s * 0.58);
    }
  }
  pipe(pipes, m.paintGrey, [[-W / 2 - 0.25, 0.42, 0.58], [-W / 2 - 0.5, 0.42, 0.58], [-W / 2 - 0.5, 0.42, -0.58], [-W / 2 - 0.25, 0.42, -0.58]], 0.06, 0.12);
  pipe(pipes, m.paintGrey, [[-W / 2 - 0.5, 0.42, 0], [-W / 2 - 0.95, 0.42, 0]], 0.08);

  /* isolation valves on the fuel header */
  const valves = r.zone("VALVE", [-W / 2 - 0.85, 1.0, 0.1]);
  gateValve(valves, m, [-W / 2 - 1.2, 0.42, 0], 1.2);

  /* front wall comes off to show the firebox */
  const door = r.zone("SCREW", [1.34, y0 + 0.88, D / 2 + 0.14], [0, 0, 1.75]);
  add(door, new THREE.BoxGeometry(W, H, 0.05), m.paint, 0, ym, D / 2);
  for (const x of [-W / 3, 0, W / 3]) add(door, rbox(0.04, H, 0.08, 0.004), m.paintDark, x, ym, D / 2 + 0.05);
  for (let i = 0; i < 3; i++) add(door, rbox(W, 0.05, 0.05, 0.004), m.paintDark, 0, y0 + 0.5 + i * 0.62, D / 2 + 0.05);
  /* peep doors */
  for (const x of [-1.34, 0, 1.34]) for (const y of [y0 + 0.88, y0 + 1.5]) {
    add(door, barrelZ(0.11, 0.05, 28), m.cast, x, y, D / 2 + 0.05);
    add(door, barrelZ(0.075, 0.03, 26), m.steel, x, y, D / 2 + 0.09);
    add(door, new THREE.TorusGeometry(0.04, 0.008, 8, 18), m.black, x, y, D / 2 + 0.11);
    boltCircle(door, m.boltZinc, 6, 0.09, "z", [x, y, D / 2 + 0.076], 0.009, 0.01);
  }

  /* crossover from convection to radiant, with flanged elbows */
  const elbows = r.zone("ELBOW", [-1.0, y1 + 0.72, 0.92]);
  for (const x of [-1.4, 1.4]) pipe(elbows, m.heat, [[x, y1 + 0.42, 0.62], [x, y1 + 0.42, 0.98], [x, y1 + 0.02, 0.98], [x, y1 - 0.1, 0.98]], 0.075, 0.13, m.steel);
  add(elbows, barrel(0.09, 3.1, 28), m.heat, 0, y1 + 0.42, 0.62);
  /* flanged connection on crossover */
  const gask = r.zone("GASKET", [1.4, y1 + 0.2, 1.08]);
  flange(gask, m, { bore: 0.075, od: 0.145, t: 0.03, neck: 0.03, bolts: 8, mat: m.steel, at: [1.4, y1 + 0.18, 0.98], dir: "-y" });
  flange(gask, m, { bore: 0.075, od: 0.145, t: 0.03, neck: 0.03, bolts: 8, mat: m.steel, at: [-1.4, y1 + 0.18, 0.98], dir: "-y" });
  const sb = r.zone("STUDBOLT", [-1.4, y1 + 0.2, 1.08]);
  void sb;

  /* convection section: finned tube bank in a box */
  const conv = r.part();
  add(conv, new THREE.BoxGeometry(3.2, 0.9, 1.2), m.paintDark, 0, y1 + 0.5, 0);
  for (const x of [-1.6, 1.6]) {
    add(conv, rbox(0.14, 0.9, 1.24, 0.006), m.paintGrey, x + Math.sign(x) * 0.06, y1 + 0.5, 0);
    for (let row = 0; row < 3; row++) for (let c = 0; c < 4; c++) add(conv, new THREE.TorusGeometry(0.09, 0.03, 10, 18, Math.PI).rotateY(Math.sign(x) > 0 ? Math.PI / 2 : -Math.PI / 2).rotateX(Math.PI / 2), m.steel, x + Math.sign(x) * 0.14, y1 + 0.2 + row * 0.27, -0.42 + c * 0.27);
  }
  scatter(conv, rbox(3.1, 0.02, 0.012, 0.002, 1), m.paintGrey, (i, o) => o.position.set(0, y1 + 0.12 + (i % 8) * 0.11, 0.606), 8);
  boltRow(conv, m.boltZinc, [-1.55, y1 + 0.955, 0.56], [1.55, y1 + 0.955, 0.56], 12, [0, 1, 0], 0.013, 0.02);
  boltRow(conv, m.boltZinc, [-1.55, y1 + 0.955, -0.56], [1.55, y1 + 0.955, -0.56], 12, [0, 1, 0], 0.013, 0.02);
  /* hood */
  const hood = new THREE.CylinderGeometry(0.24, 1.0, 0.62, 4, 1).rotateY(Math.PI / 4).scale(1.9, 1, 0.75);
  hood.computeVertexNormals();
  const hd = new THREE.Mesh(hood.toNonIndexed(), m.paint);
  hd.geometry.computeVertexNormals();
  hd.position.set(0, y1 + 1.24, 0);
  hd.castShadow = hd.receiveShadow = true;
  conv.add(hd);
  /* stack with damper, sample port, ring platform */
  add(conv, lathe([[0, 0.28], [0.1, 0.285], [0.1, 0.27], [2.1, 0.23], [2.14, 0.25], [2.2, 0.25], [2.2, 0.23]], 44).rotateZ(Math.PI / 2), m.paintDark, 0, y1 + 1.5, 0);
  for (let i = 0; i < 5; i++) add(conv, new THREE.TorusGeometry(0.264 - i * 0.006, 0.008, 8, 40).rotateX(Math.PI / 2), m.steel, 0, y1 + 1.86 + i * 0.32, 0);
  add(conv, rbox(0.1, 0.16, 0.12, 0.01), m.red, 0.34, y1 + 1.68, 0);
  add(conv, barrel(0.012, 0.12, 8), m.steel, 0.28, y1 + 1.68, 0);
  add(conv, barrelZ(0.03, 0.14, 12), m.steel, 0, y1 + 2.5, 0.28);
  /* access platform at the convection level with rail and ladder */
  walkway(conv, m, [0, y1 + 0.04, -D / 2 - 0.3], W + 0.4, 0.6);
  rail(conv, m, [-W / 2 - 0.2, y1 + 0.04, -D / 2 - 0.6], [W / 2 + 0.2, y1 + 0.04, -D / 2 - 0.6], 8);
  walkway(conv, m, [W / 2 + 0.3, y1 + 0.04, 0], 0.6, D + 0.6);
  rail(conv, m, [W / 2 + 0.6, y1 + 0.04, -D / 2 - 0.6], [W / 2 + 0.6, y1 + 0.04, D / 2 + 0.3], 6);
  ladder(conv, m, [W / 2 + 0.3, 0.16, D / 2 + 0.34], y1 - 0.08);

  /* studs: on the crossover flanges (visible bolts) get their own zone anchor */
  boltCircle(sb, m.boltZinc, 8, 0.118, "y", [1.4, y1 + 0.2, 0.98], 0.012, 0.06);
  boltCircle(sb, m.boltZinc, 8, 0.118, "y", [-1.4, y1 + 0.2, 0.98], 0.012, 0.06);

  return r.done([4.6, 5.5, 13.8], [0, 2.75, 0.2]);
}

/* --------------------------------------------------------------- exchanger */

function exchanger(m: Mats): Built {
  const r = new Rig(m);
  const cy = 1.32;
  const base = r.part();
  add(base, rbox(6.6, 0.16, 2.0, 0.03), m.concrete, -0.2, 0.08, 0);
  /* shell */
  const shell = r.part();
  add(shell, lathe([[-1.9, 0.63], [-1.86, 0.64], [1.04, 0.64], [1.06, 0.62]], 96), m.paint, 0, cy, 0);
  /* inner shell dark, so the bundle exit reads as a bore */
  add(shell, barrel(0.6, 0.02, 64), m.black, 1.05, cy, 0);
  add(shell, lathe([[-0.04, 0.63], [-0.02, 0.8], [0.04, 0.8], [0.06, 0.63]], 80), m.paint, 1.08, cy, 0);
  add(shell, lathe([[-0.04, 0.63], [-0.02, 0.8], [0.04, 0.8], [0.06, 0.63]], 80), m.paint, -1.9, cy, 0);
  /* saddles with wear pads, rib plates and anchor bolts */
  for (const x of [-1.2, 0.5]) {
    add(shell, lathe([[-0.2, 0.655], [0.2, 0.655]], 80), m.paintGrey, x, cy, 0);
    const web = new THREE.Shape();
    web.moveTo(-0.72, 0);
    web.lineTo(0.72, 0);
    web.lineTo(0.68, 0.46);
    web.absarc(0, 0.86, 0.66, -0.55, Math.PI + 0.55, true);
    web.lineTo(-0.72, 0);
    const g = new THREE.ExtrudeGeometry(web, { depth: 0.024, bevelEnabled: false, curveSegments: 32 });
    g.rotateY(Math.PI / 2);
    for (const dx of [-0.16, 0.16]) add(shell, g, m.paintGrey, x + dx - 0.012, 0.16, 0);
    add(shell, rbox(0.48, 0.03, 1.6, 0.005), m.paintGrey, x, 0.175, 0);
    for (const z of [-0.5, 0, 0.5]) add(shell, rbox(0.3, 0.3, 0.02, 0.002), m.paintGrey, x, 0.34, z);
    boltRow(shell, m.boltZinc, [x - 0.14, 0.2, 0.7], [x + 0.14, 0.2, 0.7], 2, [0, 1, 0], 0.02, 0.04);
    boltRow(shell, m.boltZinc, [x - 0.14, 0.2, -0.7], [x + 0.14, 0.2, -0.7], 2, [0, 1, 0], 0.02, 0.04);
  }
  /* floating head cover */
  const dome = r.part([-0.4, 0, 0]);
  add(dome, lathe([[0, 0.8], [-0.07, 0.8], [-0.08, 0.63], [-0.26, 0.56], [-0.42, 0.38], [-0.52, 0.16], [-0.54, 0]], 80), m.paint, -1.96, cy, 0);
  boltCircle(dome, m.boltZinc, 24, 0.72, "-x", [-2.04, cy, 0], 0.021, 0.16);
  /* lifting lugs */
  for (const x of [-1.5, 0.75]) add(shell, rbox(0.14, 0.14, 0.03, 0.004), m.paintGrey, x, cy + 0.7, 0);
  /* shell nozzles with reinforcement pads */
  const shellPipe = r.zone("PIPE", [-1.2, cy + 1.52, 0.15]);
  for (const [x, s, rad] of [[-1.1, 1, 0.18], [0.6, -1, 0.18]] as const) {
    add(shell, barrelY(rad + 0.11, 0.03, 40), m.paint, x, cy + s * 0.64, 0);
    add(shell, barrelY(rad, 0.36, 34), m.paint, x, cy + s * 0.82, 0);
    flange(shell, m, { bore: rad, od: rad + 0.13, t: 0.045, neck: 0.03, bolts: 12, at: [x, cy + s * 1.02, 0], dir: s > 0 ? "y" : "-y" });
  }
  flange(shellPipe, m, { bore: 0.18, od: 0.31, t: 0.045, neck: 0.1, bolts: 12, mat: m.paintGrey, at: [-1.1, cy + 1.1, 0], dir: "-y" });
  pipe(shellPipe, m.paintGrey, [[-1.1, cy + 1.14, 0], [-1.1, cy + 1.6, 0], [-2.8, cy + 1.6, 0]], 0.17, 0.28);
  /* vent, drain, thermowell, plate */
  add(shell, barrelY(0.025, 0.1, 12), m.steel, 0.2, cy + 0.68, 0);
  add(shell, barrelY(0.038, 0.03, 12), m.steel, 0.2, cy + 0.73, 0);
  add(shell, barrelY(0.025, 0.1, 12), m.steel, -0.3, cy - 0.68, 0);
  const tw = r.part();
  add(tw, barrelZ(0.03, 0.12, 12), m.steel, -0.6, cy + 0.28, 0.63);
  gauge(tw, m, [-0.6, cy + 0.28, 0.74], 0.055, [0, 0, -1], [0, 0.1, 1]);
  plate(shell, ["HE-1173C", "TEMA AES  Shell & tube", "Design 42 bar  380 C"], [0.1, cy + 0.34, 0.545], 0.36, [0, 0.53, 0.85]);

  /* tube bundle */
  const bundle = r.part([2.15, 0, 0]);
  const rows: [number, number][] = [];
  for (let rad = 0.1; rad < 0.55; rad += 0.082) {
    const n = Math.round((rad * Math.PI * 2) / 0.07);
    for (let i = 0; i < n; i++) rows.push([Math.cos((i / n) * Math.PI * 2 + rad * 8) * rad, Math.sin((i / n) * Math.PI * 2 + rad * 8) * rad]);
  }
  scatter(bundle, new THREE.CylinderGeometry(0.018, 0.018, 3.0, 8).rotateZ(Math.PI / 2), m.machined, (i, o) => o.position.set(-0.45, cy + rows[i][0], rows[i][1]), rows.length);
  /* tube sheet with holes shown as a dark pattern, baffles and tie rods */
  add(bundle, barrel(0.6, 0.1, 72), m.steel, 1.05, cy, 0);
  scatter(bundle, new THREE.CircleGeometry(0.018, 10).rotateY(Math.PI / 2), m.black, (i, o) => o.position.set(1.102, cy + rows[i][0], rows[i][1]), rows.length);
  add(bundle, barrel(0.58, 0.05, 64), m.steel, -1.95, cy, 0);
  for (let i = 0; i < 7; i++) {
    const g = new THREE.CylinderGeometry(0.585, 0.585, 0.014, 48, 1, false, 0, Math.PI * 1.55).rotateZ(Math.PI / 2);
    const b = add(bundle, g, m.steel, -1.65 + i * 0.42, cy, 0);
    b.rotation.x = i % 2 ? Math.PI : 0;
  }
  for (const a of [0.3, 2.3, 4.4]) add(bundle, barrel(0.015, 3.0, 8), m.steel, -0.45, cy + Math.cos(a) * 0.55, Math.sin(a) * 0.55);

  /* channel */
  const channel = r.part([1.1, 0, 0]);
  add(channel, lathe([[0, 0.8], [0.1, 0.8], [0.12, 0.66], [0.66, 0.66], [0.68, 0.8], [0.78, 0.8]], 80), m.paint, 1.14, cy, 0);
  /* channel nozzles */
  for (const [s, rad] of [[1, 0.16], [-1, 0.16]] as const) {
    add(channel, barrelY(rad + 0.1, 0.03, 36), m.paint, 1.54, cy + s * 0.66, 0);
    add(channel, barrelY(rad, 0.34, 30), m.paint, 1.54, cy + s * 0.84, 0);
    flange(channel, m, { bore: rad, od: rad + 0.12, t: 0.04, neck: 0.03, bolts: 8, at: [1.54, cy + s * 1.03, 0], dir: s > 0 ? "y" : "-y" });
  }
  pipe(channel, m.paintGrey, [[1.54, cy + 1.07, 0], [1.54, cy + 1.42, 0], [2.6, cy + 1.42, 0]], 0.15, 0.24);

  /* gasket at the tube sheet */
  const gasket = r.zone("GASKET", [1.13, cy + 0.82, 0.32], [1.1, 0.66, 0]);
  add(gasket, lathe([[-0.012, 0.63], [-0.012, 0.77], [0.012, 0.77], [0.012, 0.63]], 80), m.gasket, 1.135, cy, 0);

  const gasket2 = r.part([1.1, 0, 0]);
  void gasket2;

  /* shell-to-channel studs */
  const studs = r.zone("STUDBOLT", [1.16, cy + 0.72, 0.42], [1.1, 0, 0]);
  boltCircle(studs, m.boltZinc, 28, 0.74, "-x", [1.04, cy, 0], 0.021, 0.2);

  /* channel cover (the blind flange) */
  const cover = r.zone("FLANGE", [2.06, cy + 0.42, 0.42], [2.1, 0, 0]);
  add(cover, lathe([[-0.06, 0], [-0.06, 0.8], [0.06, 0.8], [0.09, 0.75], [0.09, 0]], 80), m.paint, 2.0, cy, 0);
  add(cover, new THREE.TorusGeometry(0.08, 0.018, 10, 24), m.steel, 2.12, cy, 0);
  boltCircle(cover, m.boltZinc, 28, 0.74, "x", [2.06, cy, 0], 0.021, 0.2);

  /* outlet line off the shell underside */
  const outlet = r.part();
  pipe(outlet, m.paintGrey, [[0.6, cy - 1.06, 0], [0.6, 0.3, 0], [2.7, 0.3, 0]], 0.15, 0.2);
  flange(outlet, m, { bore: 0.15, od: 0.31, t: 0.045, neck: 0.1, bolts: 12, mat: m.paintGrey, at: [0.6, cy - 1.1 + 0.07, 0], dir: "y" });
  r.root.position.x = -0.55;
  return r.done([2.4, 3.6, 10.2], [-0.2, 1.42, 0]);
}

const BUILD: Record<MachineSlug, (m: Mats) => Built> = { pump, compressor, turbine, furnace, exchanger };

let mats: Mats | null = null;
export function buildMachine(slug: MachineSlug): Built {
  mats ??= makeMats();
  const b = BUILD[slug](mats);
  b.moves.forEach((q) => q.home.copy(q.o.position));
  b.root.updateMatrixWorld(true);
  return b;
}
export function sharedMats() {
  return (mats ??= makeMats());
}
