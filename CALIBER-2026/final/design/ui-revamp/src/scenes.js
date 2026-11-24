/* Procedural 3D for the Sparekit mockups. No external models: every machine is built from primitives. */
(function () {
  const T = window.THREE;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;

  const PAL = {
    hall: { body: 0xe8480a, dark: 0x24282d, steel: 0xb9bfc5, light: 0xe9e6e2, brass: 0xc99a4b, key: 0xfff4e6, fill: 0xffffff, env: 1.0, floor: 0.2 },
    deck: { body: 0x1b1d20, dark: 0x0d0e10, steel: 0xc9ccd0, light: 0x34373c, brass: 0xe9a23b, key: 0xffe4bd, fill: 0xbfe3ff, env: 1.25, floor: 0.32 },
  };

  function envTexture(renderer, warm) {
    const s = new T.Scene();
    const room = new T.Mesh(new T.BoxGeometry(20, 20, 20), new T.MeshBasicMaterial({ color: warm ? 0xdcd8d2 : 0xb8bcc0, side: T.BackSide }));
    s.add(room);
    const panel = (x, y, z, w, h, c, i) => {
      const m = new T.Mesh(new T.PlaneGeometry(w, h), new T.MeshBasicMaterial({ color: new T.Color(c).multiplyScalar(i), side: T.DoubleSide }));
      m.position.set(x, y, z);
      m.lookAt(0, 0, 0);
      s.add(m);
    };
    panel(0, 9.5, 0, 12, 12, 0xffffff, 5);
    panel(-9, 3, 5, 6, 10, 0xffffff, 3.2);
    panel(9, 2, 4, 3, 12, warm ? 0xffd9b0 : 0xffb35a, 3.5);
    panel(0, 1, -9.5, 14, 3, 0xffffff, 1.6);
    const floor = new T.Mesh(new T.PlaneGeometry(20, 20), new T.MeshBasicMaterial({ color: 0x55585c }));
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -9.8;
    s.add(floor);
    const pm = new T.PMREMGenerator(renderer);
    const tex = pm.fromScene(s, 0.04).texture;
    pm.dispose();
    return tex;
  }

  const std = (color, metal, rough, extra) => new T.MeshStandardMaterial(Object.assign({ color, metalness: metal, roughness: rough }, extra || {}));
  function mesh(geo, mat, x, y, z) {
    const m = new T.Mesh(geo, mat);
    m.castShadow = m.receiveShadow = true;
    m.position.set(x || 0, y || 0, z || 0);
    return m;
  }
  const cylX = (r, len, seg, r2) => new T.CylinderGeometry(r2 == null ? r : r2, r, len, seg || 48).rotateZ(-Math.PI / 2);
  const cylZ = (r, len, seg) => new T.CylinderGeometry(r, r, len, seg || 48).rotateX(Math.PI / 2);
  const cylY = (r, len, seg) => new T.CylinderGeometry(r, r, len, seg || 48);

  function rbox(w, h, d, r) {
    const sh = new T.Shape();
    const x = -w / 2, y = -d / 2;
    sh.moveTo(x + r, y);
    sh.lineTo(x + w - r, y);
    sh.quadraticCurveTo(x + w, y, x + w, y + r);
    sh.lineTo(x + w, y + d - r);
    sh.quadraticCurveTo(x + w, y + d, x + w - r, y + d);
    sh.lineTo(x + r, y + d);
    sh.quadraticCurveTo(x, y + d, x, y + d - r);
    sh.lineTo(x, y + r);
    sh.quadraticCurveTo(x, y, x + r, y);
    const g = new T.ExtrudeGeometry(sh, { depth: h - 0.04, bevelEnabled: true, bevelThickness: 0.02, bevelSize: 0.02, bevelSegments: 3, curveSegments: 8 });
    g.rotateX(Math.PI / 2);
    g.translate(0, h / 2, 0);
    return g;
  }

  /* Bolted flange in the YZ plane (axis along X). */
  function flange(group, x, y, z, r, mat, boltMat, n, axis) {
    const f = new T.Group();
    f.add(mesh(cylX(r, 0.07, 48), mat));
    const count = n || 10;
    for (let i = 0; i < count; i++) {
      const a = (i / count) * Math.PI * 2;
      f.add(mesh(cylX(0.022, 0.1, 8), boltMat, 0.02, Math.cos(a) * r * 0.82, Math.sin(a) * r * 0.82));
    }
    f.position.set(x, y, z);
    if (axis === "y") f.rotation.z = Math.PI / 2;
    if (axis === "z") f.rotation.y = Math.PI / 2;
    group.add(f);
    return f;
  }

  /* Pump volute: a spiral tube whose radius grows with the angle, ending tangent into the discharge. */
  function volute(mat) {
    const rings = 96, seg = 24, pos = [], idx = [];
    const turn = Math.PI * 2 * 0.98;
    for (let i = 0; i <= rings; i++) {
      const t = i / rings, th = t * turn;
      const r = 0.1 + 0.2 * t, R = 0.56 + r + 0.04 * t;
      const cy = Math.cos(th) * R, cz = Math.sin(th) * R;
      for (let j = 0; j < seg; j++) {
        const p = (j / seg) * Math.PI * 2;
        const rad = R + Math.cos(p) * r;
        pos.push(Math.sin(p) * r * 0.82, Math.cos(th) * rad, Math.sin(th) * rad);
      }
      void cy; void cz;
    }
    for (let i = 0; i < rings; i++)
      for (let j = 0; j < seg; j++) {
        const a = i * seg + j, b = i * seg + ((j + 1) % seg), c = a + seg, d = b + seg;
        idx.push(a, c, b, b, c, d);
      }
    const g = new T.BufferGeometry();
    g.setAttribute("position", new T.Float32BufferAttribute(pos, 3));
    g.setIndex(idx);
    g.computeVertexNormals();
    return mesh(g, mat);
  }

  function buildPump(p) {
    const root = new T.Group(), parts = [], anchors = {};
    const body = std(p.body, 0.25, 0.32), dark = std(p.dark, 0.55, 0.48), steel = std(p.steel, 0.92, 0.28), light = std(p.light, 0.3, 0.55), brass = std(p.brass, 0.85, 0.3);
    const y0 = 0.86;

    /* skid */
    root.add(mesh(rbox(5.3, 0.16, 1.9, 0.08), light, 0, 0.08, 0));
    for (const z of [-0.8, 0.8]) root.add(mesh(new T.BoxGeometry(5.1, 0.1, 0.1), dark, 0, 0.21, z));

    /* motor */
    const motor = new T.Group();
    motor.add(mesh(cylX(0.62, 1.75, 64), dark, -1.45, y0, 0));
    for (let i = 0; i < 28; i++) {
      const a = (i / 28) * Math.PI * 2;
      const fin = mesh(new T.BoxGeometry(1.58, 0.1, 0.028), dark, -1.45, y0 + Math.cos(a) * 0.65, Math.sin(a) * 0.65);
      fin.rotation.x = -a;
      motor.add(fin);
    }
    motor.add(mesh(cylX(0.68, 0.14, 64), body, -0.58, y0, 0));
    motor.add(mesh(cylX(0.68, 0.14, 64), body, -2.34, y0, 0));
    const cap = mesh(new T.SphereGeometry(0.56, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2).rotateZ(Math.PI / 2).scale(0.5, 1, 1), dark, -2.41, y0, 0);
    motor.add(cap);
    motor.add(mesh(rbox(0.56, 0.22, 0.44, 0.04), body, -1.45, y0 + 0.74, 0));
    for (const x of [-2.1, -0.8]) motor.add(mesh(new T.BoxGeometry(0.34, 0.3, 1.34), dark, x, 0.36, 0));
    root.add(motor);

    /* coupling guard */
    const guard = mesh(cylX(0.34, 0.68, 48), body, -0.17, y0, 0);
    root.add(guard);

    /* bearing housing, pulls out in the exploded view */
    const brg = new T.Group();
    brg.add(mesh(cylX(0.32, 0.72, 48), steel, 0.5, y0, 0));
    for (const x of [0.25, 0.5, 0.75]) brg.add(mesh(cylX(0.36, 0.05, 48), steel, x, y0, 0));
    const pedestal = mesh(new T.BoxGeometry(0.72, 0.42, 0.8), light, 0.5, 0.42, 0);
    root.add(pedestal);
    root.add(brg);
    const shaft = mesh(cylX(0.075, 2.6, 24), steel, 1.0, y0, 0);
    root.add(shaft);

    /* rear casing */
    const casing = new T.Group();
    const vol = volute(body);
    casing.add(vol);
    casing.add(mesh(cylX(0.6, 0.2, 64), body, 0, 0, 0));
    /* discharge: picks up where the spiral ends at the top */
    casing.add(mesh(cylZ(0.27, 0.5, 40), body, 0, 0.98, -0.24));
    const dis = mesh(new T.CylinderGeometry(0.2, 0.26, 0.5, 40), body, 0, 1.3, -0.3);
    casing.add(dis);
    flange(casing, 0, 1.56, -0.3, 0.33, body, steel, 10, "y");
    casing.position.set(1.34, y0, 0);
    root.add(casing);
    const foot = mesh(new T.BoxGeometry(0.64, 0.5, 1.1), body, 1.34, 0.4, 0);
    root.add(foot);

    /* impeller */
    const imp = new T.Group();
    imp.add(mesh(cylX(0.5, 0.05, 56), brass, -0.09, 0, 0));
    imp.add(mesh(cylX(0.5, 0.04, 56), brass, 0.11, 0, 0));
    imp.add(mesh(cylX(0.13, 0.32, 24, 0.09), brass, 0.02, 0, 0));
    for (let i = 0; i < 7; i++) {
      const a = (i / 7) * Math.PI * 2;
      const v = mesh(new T.BoxGeometry(0.18, 0.4, 0.024), brass, 0.01, Math.cos(a) * 0.3, Math.sin(a) * 0.3);
      v.rotation.x = -a + 0.5;
      imp.add(v);
    }
    imp.position.set(1.46, y0, 0);
    root.add(imp);

    /* seal, sits between casing and bearing */
    const seal = new T.Group();
    seal.add(mesh(new T.TorusGeometry(0.2, 0.035, 14, 48).rotateY(Math.PI / 2), dark));
    seal.add(mesh(cylX(0.16, 0.12, 32), steel, 0.07, 0, 0));
    seal.position.set(1.02, y0, 0);
    root.add(seal);

    /* suction cover and nozzle */
    const cover = new T.Group();
    cover.add(mesh(cylX(0.6, 0.12, 64), body, 0, 0, 0));
    cover.add(mesh(cylX(0.26, 0.48, 40, 0.34), body, 0.28, 0, 0));
    flange(cover, 0.54, 0, 0, 0.42, body, steel, 12);
    for (let i = 0; i < 12; i++) {
      const a = (i / 12) * Math.PI * 2;
      cover.add(mesh(cylX(0.024, 0.2, 8), steel, 0, Math.cos(a) * 0.54, Math.sin(a) * 0.54));
    }
    cover.position.set(1.6, y0, 0);
    root.add(cover);

    parts.push({ o: cover, d: new T.Vector3(1.05, 0, 0) });
    parts.push({ o: imp, d: new T.Vector3(0.68, 0, 0) });
    parts.push({ o: seal, d: new T.Vector3(0.15, 0.72, 0) });
    parts.push({ o: brg, d: new T.Vector3(0, 0.0, 0) });
    parts.push({ o: motor, d: new T.Vector3(-0.3, 0, 0) });
    parts.push({ o: guard, d: new T.Vector3(-0.2, 0, 0) });

    const a = (n, parent, x, y, z) => {
      const o = new T.Object3D();
      o.position.set(x, y, z);
      parent.add(o);
      anchors[n] = o;
    };
    a("impeller", imp, 0.12, 0.42, 0.22);
    a("bearing", brg, 0.5, y0 + 0.36, 0);
    a("ring", seal, 0, 0.2, 0);
    a("flange", cover, 0.56, 0.3, 0.3);
    root.position.set(-0.1, 0, 0);
    return { root, parts, anchors, cam: [1.2, 3.25, 7.9], look: [0.05, 0.92, 0], rot: -0.42 };
  }

  function buildFurnace(p) {
    const root = new T.Group(), parts = [], anchors = {};
    const body = std(p.body, 0.25, 0.34), dark = std(p.dark, 0.55, 0.5), steel = std(p.steel, 0.9, 0.3), light = std(p.light, 0.25, 0.6), fire = std(p.brass, 0.85, 0.32);
    root.add(mesh(rbox(5.4, 0.14, 3.2, 0.08), light, 0, 0.07, 0));
    /* legs */
    for (const x of [-1.9, 0, 1.9]) for (const z of [-0.85, 0.85]) root.add(mesh(new T.BoxGeometry(0.14, 0.75, 0.14), dark, x, 0.5, z));
    /* radiant box, the front wall lifts off in the exploded view */
    const back = mesh(new T.BoxGeometry(4.2, 1.9, 0.08), body, 0, 1.82, -0.86);
    root.add(back);
    root.add(mesh(new T.BoxGeometry(4.2, 0.1, 1.8), dark, 0, 0.85, 0));
    root.add(mesh(new T.BoxGeometry(4.2, 0.1, 1.8), body, 0, 2.78, 0));
    for (const x of [-2.08, 2.08]) root.add(mesh(new T.BoxGeometry(0.08, 1.9, 1.8), body, x, 1.82, 0));
    /* lining */
    root.add(mesh(new T.BoxGeometry(4.0, 1.78, 0.05), std(0xe7ddcf, 0, 0.92), 0, 1.82, -0.8));
    /* serpentine coils */
    const coils = new T.Group();
    for (let i = 0; i < 9; i++) {
      const x = -1.68 + i * 0.42;
      coils.add(mesh(cylY(0.055, 1.55, 18), steel, x, 1.82, -0.1));
      coils.add(mesh(new T.TorusGeometry(0.21, 0.055, 12, 20, Math.PI), steel, x + 0.21, i % 2 ? 1.05 : 2.6, -0.1));
      if (!(i % 2)) coils.children[coils.children.length - 1].rotation.z = 0;
      else coils.children[coils.children.length - 1].rotation.z = Math.PI;
    }
    root.add(coils);
    /* burners along the floor */
    for (let i = 0; i < 8; i++) root.add(mesh(cylY(0.09, 0.26, 18), dark, -1.6 + i * 0.46, 0.72, 0.42));
    /* front wall with ribs */
    const front = new T.Group();
    front.add(mesh(new T.BoxGeometry(4.24, 1.9, 0.07), body, 0, 0, 0));
    for (let i = 0; i < 6; i++) front.add(mesh(new T.BoxGeometry(0.05, 1.9, 0.06), dark, -1.9 + i * 0.76, 0, 0.05));
    for (let i = 0; i < 3; i++) {
      const port = mesh(cylZ(0.11, 0.06, 24), steel, -1.14 + i * 1.14, 0.25, 0.06);
      front.add(port);
    }
    front.position.set(0, 1.82, 0.9);
    root.add(front);
    /* convection section */
    root.add(mesh(new T.BoxGeometry(2.3, 0.72, 1.3), dark, 0, 3.2, 0));
    for (let i = 0; i < 5; i++) root.add(mesh(cylX(0.04, 2.34, 12), steel, 0, 3.0 + i * 0.1, 0.67));
    root.add(mesh(new T.CylinderGeometry(0.28, 0.85, 0.5, 4).rotateY(Math.PI / 4).scale(1.1, 1, 0.8), body, 0, 3.8, 0));
    root.add(mesh(new T.CylinderGeometry(0.2, 0.24, 1.5, 32), dark, 0, 4.72, 0));
    root.add(mesh(cylY(0.25, 0.08, 32), body, 0, 5.46, 0));
    /* crossover and manifold */
    const pipeAnchor = new T.Group();
    pipeAnchor.add(mesh(cylX(0.1, 3.6, 24), steel, 0, 3.05, 1.08));
    for (const x of [-1.4, 1.4]) pipeAnchor.add(mesh(cylY(0.09, 0.4, 20), steel, x, 2.86, 1.08));
    root.add(pipeAnchor);
    const valve = new T.Group();
    valve.add(mesh(cylX(0.13, 0.28, 24), body));
    valve.add(mesh(cylY(0.03, 0.3, 10), steel, 0, 0.26, 0));
    valve.add(mesh(new T.TorusGeometry(0.12, 0.018, 10, 28).rotateX(Math.PI / 2), dark, 0, 0.42, 0));
    valve.position.set(0.62, 3.05, 1.08);
    root.add(valve);
    /* platform */
    root.add(mesh(new T.BoxGeometry(4.5, 0.05, 0.42), light, 0, 2.86, -1.14));
    for (let i = 0; i < 7; i++) root.add(mesh(cylY(0.018, 0.5, 8), dark, -2.2 + i * 0.73, 3.12, -1.32));
    root.add(mesh(cylX(0.02, 4.45, 8), dark, 0, 3.36, -1.32));

    parts.push({ o: front, d: new T.Vector3(0, 0, 1.15) });
    parts.push({ o: pipeAnchor, d: new T.Vector3(0, 0.36, 0.55) });
    parts.push({ o: valve, d: new T.Vector3(0.3, 0.68, 0.6) });
    const a = (n, parent, x, y, z) => {
      const o = new T.Object3D();
      o.position.set(x, y, z);
      parent.add(o);
      anchors[n] = o;
    };
    a("wall", root, -1.5, 1.5, -0.76);
    a("anchor", root, 1.7, 2.3, -0.76);
    a("pipe", pipeAnchor, -1.0, 3.05, 1.1);
    a("valve", valve, 0, 0.42, 0);
    root.position.set(0, 0, 0);
    return { root, parts, anchors, cam: [3.8, 4.9, 12.2], look: [0, 2.55, 0], rot: -0.34 };
  }

  function buildExchanger(p) {
    const root = new T.Group(), parts = [], anchors = {};
    const body = std(p.body, 0.25, 0.34), dark = std(p.dark, 0.55, 0.48), steel = std(p.steel, 0.92, 0.28), light = std(p.light, 0.3, 0.55);
    const y0 = 1.2;
    root.add(mesh(rbox(5.8, 0.14, 2.3, 0.08), light, 0, 0.07, 0));
    for (const x of [-1.5, 1.3]) {
      root.add(mesh(new T.BoxGeometry(0.34, 0.5, 1.3), dark, x, 0.42, 0));
      root.add(mesh(new T.TorusGeometry(0.7, 0.05, 12, 48, Math.PI).rotateX(Math.PI).rotateY(Math.PI / 2), dark, x, y0, 0));
    }
    /* shell */
    root.add(mesh(cylX(0.66, 3.5, 64), dark, -0.15, y0, 0));
    root.add(mesh(new T.SphereGeometry(0.66, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2).rotateZ(Math.PI / 2).scale(0.45, 1, 1), dark, -1.9, y0, 0));
    for (const x of [-1.2, 0.3, 1.25]) root.add(mesh(cylX(0.68, 0.06, 64), body, x, y0, 0));
    /* shell nozzles */
    for (const [x, s] of [[-1.05, 1], [0.95, -1]]) {
      root.add(mesh(cylY(0.17, 0.55, 28), steel, x, y0 + s * 0.84, 0));
      const f = mesh(cylY(0.27, 0.06, 32), body, x, y0 + s * 1.1, 0);
      root.add(f);
    }
    /* shell flange */
    const shellF = flange(root, 1.61, y0, 0, 0.82, body, steel, 22);
    /* tube bundle, slides out in the exploded view */
    const bundle = new T.Group();
    const tsheet = mesh(cylX(0.62, 0.09, 56), steel, 1.68, 0, 0);
    bundle.add(tsheet);
    for (let r = 0.14; r < 0.56; r += 0.14) {
      const n = Math.round(r * 42);
      for (let i = 0; i < n; i++) {
        const a = (i / n) * Math.PI * 2;
        bundle.add(mesh(cylX(0.026, 3.2, 8), steel, 0.05, Math.cos(a) * r, Math.sin(a) * r));
      }
    }
    for (const x of [-1.2, -0.5, 0.2, 0.9]) bundle.add(mesh(cylX(0.6, 0.03, 48), light, x, 0, 0));
    bundle.position.set(0, y0, 0);
    root.add(bundle);
    /* channel head */
    const head = new T.Group();
    head.add(mesh(cylX(0.72, 0.62, 64), body, 0.42, 0, 0));
    flange(head, 0.08, 0, 0, 0.84, body, steel, 22);
    flange(head, 0.76, 0, 0, 0.84, body, steel, 22);
    head.add(mesh(cylY(0.2, 0.5, 28), steel, 0.42, 0.86, 0));
    head.add(mesh(cylY(0.3, 0.06, 32), body, 0.42, 1.12, 0));
    head.add(mesh(cylY(0.2, 0.5, 28), steel, 0.42, -0.86, 0));
    head.position.set(1.72, y0, 0);
    root.add(head);
    const blind = new T.Group();
    blind.add(mesh(cylX(0.84, 0.08, 64), body));
    for (let i = 0; i < 22; i++) {
      const a = (i / 22) * Math.PI * 2;
      blind.add(mesh(cylX(0.024, 0.2, 8), steel, 0.02, Math.cos(a) * 0.72, Math.sin(a) * 0.72));
    }
    blind.position.set(2.56, y0, 0);
    root.add(blind);
    void shellF;

    parts.push({ o: blind, d: new T.Vector3(1.05, 0, 0) });
    parts.push({ o: head, d: new T.Vector3(0.55, 0.0, 0) });
    parts.push({ o: bundle, d: new T.Vector3(0.0, 0, 0) });
    const a = (n, parent, x, y, z) => {
      const o = new T.Object3D();
      o.position.set(x, y, z);
      parent.add(o);
      anchors[n] = o;
    };
    a("head", head, 0.42, 0.72, 0.1);
    a("blind", blind, 0, 0.5, 0.5);
    a("bolts", root, 1.61, y0 + 0.75, 0.25);
    a("pipe", root, -1.05, y0 + 1.1, 0);
    root.position.set(-0.3, 0, 0);
    return { root, parts, anchors, cam: [2.3, 3.3, 9.5], look: [0.2, 1.15, 0], rot: -0.38 };
  }

  const BUILD = { pump: buildPump, furnace: buildFurnace, exchanger: buildExchanger };

  function setupStage(canvas, opt) {
    const renderer = new T.WebGLRenderer({ canvas, antialias: true, alpha: true, preserveDrawingBuffer: !!opt.keep });
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
    renderer.outputColorSpace = T.SRGBColorSpace;
    renderer.toneMapping = T.ACESFilmicToneMapping;
    renderer.toneMappingExposure = opt.exposure || 0.82;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = T.PCFSoftShadowMap;
    renderer.setClearColor(0, 0);
    return renderer;
  }

  function lights(scene, p) {
    const key = new T.DirectionalLight(p.key, 1.5);
    key.position.set(3.5, 8, 5);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    Object.assign(key.shadow.camera, { left: -7, right: 7, top: 7, bottom: -7, near: 0.5, far: 25 });
    key.shadow.radius = 7;
    key.shadow.bias = -0.0005;
    scene.add(key);
    const rim = new T.DirectionalLight(p.fill, 0.8);
    rim.position.set(-5, 3, -4);
    scene.add(rim);
    scene.add(new T.HemisphereLight(0xffffff, 0xcfc8bf, 0.15));
  }

  function floor(scene, p) {
    const f = new T.Mesh(new T.PlaneGeometry(40, 40), new T.ShadowMaterial({ opacity: p.floor }));
    f.rotation.x = -Math.PI / 2;
    f.receiveShadow = true;
    scene.add(f);
    const ring = new T.Mesh(new T.RingGeometry(3.9, 3.925, 128), new T.MeshBasicMaterial({ color: 0x000000, transparent: true, opacity: 0.13, side: T.DoubleSide }));
    ring.rotation.x = -Math.PI / 2;
    ring.position.y = 0.005;
    scene.add(ring);
  }

  /* Interactive machine stage. */
  function Machine(canvas, o) {
    const p = PAL[o.palette || "hall"];
    const renderer = setupStage(canvas, {});
    const scene = new T.Scene();
    scene.environment = envTexture(renderer, o.palette !== "deck");
    scene.environmentIntensity = p.env;
    lights(scene, p);
    floor(scene, p);
    const camera = new T.PerspectiveCamera(27, 1, 0.1, 80);
    const pivot = new T.Group();
    scene.add(pivot);
    let current = null, rotY = 0, target = 0, tilt = 0, explode = 0, explodeTo = 0, running = true, drag = null, idle = true, baseRot = 0, raf = 0, fit = 1;
    const dims = { w: 1, h: 1 };
    const v = new T.Vector3();

    const load = (name) => {
      while (pivot.children.length) pivot.remove(pivot.children[0]);
      current = BUILD[name](p);
      current.parts.forEach((q) => (q.home = q.o.position.clone()));
      pivot.add(current.root);
      baseRot = current.rot;
      target = rotY = baseRot;
      explode = explodeTo = current.open || 0;
      frame();
    };

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) return;
      dims.w = r.width;
      dims.h = r.height;
      renderer.setSize(r.width, r.height, false);
      camera.aspect = r.width / r.height;
      /* keep the machine in frame on narrow stages */
      fit = Math.max(1, (o.fitK || 1.45) / camera.aspect);
      camera.updateProjectionMatrix();
    };
    const ro = new ResizeObserver(resize);
    ro.observe(canvas);

    const frame = () => {
      if (!current) return;
      rotY += (target - rotY) * 0.08;
      explode += (explodeTo - explode) * 0.08;
      pivot.rotation.y = rotY;
      current.parts.forEach((q) => q.o.position.copy(q.home).addScaledVector(q.d, explode));
      camera.position.set(current.cam[0] * fit, current.cam[1] * fit + tilt, current.cam[2] * fit);
      camera.lookAt(current.look[0], current.look[1], current.look[2]);
      renderer.render(scene, camera);
      if (o.onFrame) o.onFrame(api);
    };
    const tick = (t) => {
      raf = requestAnimationFrame(tick);
      if (!running) return;
      if (idle && !reduce) target = baseRot + Math.sin(t * 0.00028) * 0.24;
      frame();
    };

    canvas.addEventListener("pointerdown", (e) => {
      drag = { x: e.clientX, y: e.clientY, r: target };
      idle = false;
      canvas.setPointerCapture(e.pointerId);
      canvas.style.cursor = "grabbing";
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!drag) return;
      target = drag.r + (e.clientX - drag.x) * 0.007;
      tilt = Math.max(-1.5, Math.min(2.5, (e.clientY - drag.y) * 0.012));
    });
    const up = () => {
      drag = null;
      canvas.style.cursor = "grab";
    };
    canvas.addEventListener("pointerup", up);
    canvas.addEventListener("pointercancel", up);
    canvas.style.cursor = "grab";
    canvas.style.touchAction = "pan-y";

    const api = {
      load,
      resize,
      toggleExplode() {
        const closed = current.open || 0;
        explodeTo = explodeTo > closed + 0.01 ? closed : 1;
        return explodeTo === 1;
      },
      isExploded: () => explodeTo === 1,
      project(name) {
        const a = current && current.anchors[name];
        if (!a) return null;
        a.getWorldPosition(v);
        v.project(camera);
        return { x: (v.x * 0.5 + 0.5) * dims.w, y: (-v.y * 0.5 + 0.5) * dims.h };
      },
      start() {
        running = true;
        resize();
      },
      stop() {
        running = false;
      },
    };
    resize();
    load(o.model || "pump");
    raf = requestAnimationFrame(tick);
    void raf;
    return api;
  }

  /* One still render per model, for the machine picker. */
  function thumbs(palette) {
    const p = PAL[palette || "hall"];
    const c = document.createElement("canvas");
    const renderer = setupStage(c, { keep: true });
    renderer.setPixelRatio(1);
    renderer.setSize(220, 220, false);
    const scene = new T.Scene();
    scene.environment = envTexture(renderer, palette !== "deck");
    scene.environmentIntensity = p.env;
    lights(scene, p);
    const camera = new T.PerspectiveCamera(27, 1, 0.1, 80);
    const out = {};
    for (const name of Object.keys(BUILD)) {
      const m = BUILD[name](p);
      m.root.rotation.y = m.rot;
      (m.parts || []).forEach((q) => q.o.position.addScaledVector(q.d, m.open || 0));
      scene.add(m.root);
      const k = name === "furnace" ? 1.15 : 1.25;
      camera.position.set(m.cam[0] * k, m.cam[1] * k, m.cam[2] * k);
      camera.lookAt(m.look[0], m.look[1], m.look[2]);
      renderer.render(scene, camera);
      out[name] = c.toDataURL("image/png");
      scene.remove(m.root);
    }
    renderer.dispose();
    renderer.forceContextLoss && renderer.forceContextLoss();
    return out;
  }

  /* ---------- Plant site for option B: a white clay model on a map, with shortage contours painted on the ground. ---------- */
  function heatTexture(zones) {
    const S = 1024;
    const c = document.createElement("canvas");
    c.width = c.height = S;
    const g = c.getContext("2d");
    /* map ground */
    g.fillStyle = "#e8eef0";
    g.fillRect(0, 0, S, S);
    /* water, the channel along the top and right, same pale blue as a road atlas */
    g.fillStyle = "#c7e0ee";
    g.beginPath();
    g.moveTo(0, 0); g.lineTo(S, 0); g.lineTo(S, 420);
    g.bezierCurveTo(900, 380, 860, 240, 720, 190);
    g.bezierCurveTo(600, 150, 480, 150, 340, 118);
    g.bezierCurveTo(200, 90, 90, 130, 0, 96);
    g.closePath(); g.fill();
    g.beginPath();
    g.moveTo(S, 780); g.bezierCurveTo(950, 800, 900, 880, 880, S); g.lineTo(S, S); g.closePath(); g.fill();
    /* green buffer belts */
    g.fillStyle = "#d9e8d3";
    [[60, 170, 170, 90], [50, 820, 230, 150], [700, 830, 150, 150]].forEach((b) => {
      g.beginPath(); g.roundRect(b[0], b[1], b[2], b[3], 40); g.fill();
    });
    /* roads */
    g.strokeStyle = "#ffffff"; g.lineWidth = 11; g.lineCap = "round";
    [[[60, 300], [960, 500]], [[60, 800], [940, 730]], [[250, 180], [190, 980]], [[770, 260], [720, 960]], [[60, 540], [950, 620]]].forEach((l) => {
      g.beginPath(); g.moveTo(l[0][0], l[0][1]); g.lineTo(l[1][0], l[1][1]); g.stroke();
    });
    g.lineWidth = 4;
    [[[250, 420], [770, 490]], [[230, 690], [730, 660]], [[470, 300], [430, 790]]].forEach((l) => {
      g.beginPath(); g.moveTo(l[0][0], l[0][1]); g.lineTo(l[1][0], l[1][1]); g.stroke();
    });
    /* contour field: sum of gaussians, weighted by the real shortage per zone */
    const N = 256, img = g.createImageData(N, N), field = new Float32Array(N * N);
    let max = 0;
    for (let y = 0; y < N; y++)
      for (let x = 0; x < N; x++) {
        let f = 0;
        for (const z of zones) {
          const dx = ((x / N) * S - z.x) / z.rx, dy = ((y / N) * S - z.y) / z.ry;
          f += z.w * Math.exp(-(dx * dx + dy * dy));
        }
        field[y * N + x] = f;
        if (f > max) max = f;
      }
    const bands = [
      [0.17, [120, 190, 110], 0.26],
      [0.34, [176, 208, 92], 0.42],
      [0.52, [246, 209, 77], 0.58],
      [0.72, [243, 151, 62], 0.68],
      [0.88, [233, 91, 62], 0.76],
    ];
    for (let i = 0; i < N * N; i++) {
      const f = field[i] / max;
      let col = null, al = 0, prev = null;
      for (const b of bands) {
        if (f >= b[0]) { prev = col; col = b; }
      }
      if (col) {
        const edge = Math.min(1, (f - col[0]) / 0.012);
        const c1 = prev ? prev[1] : col[1], a0 = prev ? prev[2] : 0;
        al = a0 + (col[2] - a0) * edge;
        for (let k = 0; k < 3; k++) img.data[i * 4 + k] = c1[k] + (col[1][k] - c1[k]) * edge;
        img.data[i * 4 + 3] = al * 255;
      }
    }
    const tmp = document.createElement("canvas");
    tmp.width = tmp.height = N;
    tmp.getContext("2d").putImageData(img, 0, 0);
    g.imageSmoothingEnabled = true;
    g.imageSmoothingQuality = "high";
    g.drawImage(tmp, 0, 0, S, S);
    const t = new T.CanvasTexture(c);
    t.colorSpace = T.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  }

  function Plant(canvas, o) {
    const renderer = setupStage(canvas, { exposure: 0.92 });
    const scene = new T.Scene();
    scene.environment = envTexture(renderer, false);
    scene.environmentIntensity = 0.8;
    const sun = new T.DirectionalLight(0xfff6e8, 1.25);
    sun.position.set(-7, 16, 7);
    sun.castShadow = true;
    sun.shadow.mapSize.set(4096, 4096);
    Object.assign(sun.shadow.camera, { left: -16, right: 16, top: 16, bottom: -16, near: 1, far: 50 });
    sun.shadow.radius = 4;
    sun.shadow.bias = -0.0004;
    scene.add(sun);
    scene.add(new T.HemisphereLight(0xffffff, 0xbfd4d8, 0.2));

    const W = 26; /* world size; ground texture is 1024 px */
    const w = (px, py) => [(px / 1024 - 0.5) * W, (py / 1024 - 0.5) * W];
    const fz = o.furnaces;
    const maxS = Math.max(...fz.map((f) => f.short));
    const zones = [];
    /* 12 furnaces in two rows; each adds a gaussian weighted by its real short count */
    fz.forEach((f, i) => {
      const col = i % 6, row = i < 6 ? 0 : 1;
      zones.push({ x: 400 + col * 44, y: 460 + row * 110, rx: 150, ry: 170, w: (f.short / maxS) * 0.3 });
    });
    const SITES = {
      Compressors: { x: 650, y: 400, rx: 190, ry: 170 },
      Pumps: { x: 320, y: 680, rx: 190, ry: 150 },
      Turbines: { x: 620, y: 650, rx: 160, ry: 140 },
      "Heat exchangers": { x: 760, y: 560, rx: 140, ry: 170 },
    };
    o.classes.forEach((c) => {
      if (SITES[c.cls]) zones.push(Object.assign({ w: (c.short / 58) * 1.1 }, SITES[c.cls]));
    });
    const groundMat = new T.MeshBasicMaterial({ map: heatTexture(zones), toneMapped: false });
    const ground = new T.Mesh(new T.PlaneGeometry(W, W), groundMat);
    ground.rotation.x = -Math.PI / 2;
    scene.add(ground);
    /* the atlas keeps going past the textured area */
    const beyond = new T.Mesh(new T.PlaneGeometry(200, 200), new T.MeshBasicMaterial({ color: 0xe8eef0, toneMapped: false }));
    beyond.rotation.x = -Math.PI / 2;
    beyond.position.y = -0.02;
    scene.add(beyond);
    const catcher = new T.Mesh(new T.PlaneGeometry(W, W), new T.ShadowMaterial({ opacity: 0.26 }));
    catcher.rotation.x = -Math.PI / 2;
    catcher.position.y = 0.01;
    catcher.receiveShadow = true;
    scene.add(catcher);

    const clay = std(0xf4f3ee, 0, 0.72, { envMapIntensity: 0.55 }), clay2 = std(0xd6dbdc, 0.05, 0.6, { envMapIntensity: 0.55 }), pipe = std(0xc8ced2, 0.6, 0.4), accent = std(0x1f6b45, 0.1, 0.5);
    const place = (geo, mat, px, py, y) => {
      const [x, z] = w(px, py);
      const m = mesh(geo, mat, x, y, z);
      scene.add(m);
      return m;
    };
    /* furnace bank: heights follow the real parts count */
    const maxT = Math.max(...fz.map((f) => f.total));
    fz.forEach((f, i) => {
      const col = i % 6, row = i < 6 ? 0 : 1, px = 400 + col * 44, py = 460 + row * 110;
      const h = 0.7 + (f.total / maxT) * 0.75;
      place(new T.BoxGeometry(0.72, h, 1.55), clay, px, py, h / 2);
      place(new T.BoxGeometry(0.46, 0.34, 0.8), clay2, px, py, h + 0.17);
      place(cylY(0.09, 1.0, 14), clay, px, py, h + 0.8);
    });
    /* pipe racks */
    place(new T.BoxGeometry(8.2, 0.08, 0.35), pipe, 512, 505, 0.95);
    place(new T.BoxGeometry(0.35, 0.08, 10.5), pipe, 640, 560, 0.95);
    place(new T.BoxGeometry(11, 0.08, 0.35), pipe, 500, 620, 0.75);
    for (let i = 0; i < 14; i++) place(new T.BoxGeometry(0.06, 0.95, 0.4), clay2, 350 + i * 28, 505, 0.47);
    /* compressors: halls with stepped roofs */
    [[640, 370], [690, 370], [640, 425], [690, 425]].forEach((p) => {
      place(new T.BoxGeometry(1.0, 0.65, 1.1), clay, p[0], p[1], 0.32);
      place(new T.BoxGeometry(0.55, 0.26, 0.7), clay2, p[0], p[1], 0.78);
    });
    /* pumps row */
    for (let i = 0; i < 9; i++) {
      const px = 240 + i * 26, py = 680;
      place(new T.BoxGeometry(0.42, 0.2, 0.28), clay, px, py, 0.1);
      place(new T.CylinderGeometry(0.1, 0.1, 0.3, 10).rotateZ(Math.PI / 2), clay2, px, py, 0.25);
    }
    /* turbines */
    [[600, 650], [650, 650]].forEach((p) => {
      place(new T.CylinderGeometry(0.42, 0.42, 1.2, 28).rotateZ(Math.PI / 2), clay, p[0], p[1], 0.55);
      place(new T.BoxGeometry(1.3, 0.18, 0.95), clay2, p[0], p[1], 0.09);
    });
    /* exchangers: horizontal drums */
    for (let i = 0; i < 6; i++) {
      place(new T.CylinderGeometry(0.2, 0.2, 1.2, 18).rotateX(Math.PI / 2), clay, 730 + (i % 2) * 58, 495 + Math.floor(i / 2) * 58, 0.4);
    }
    /* columns */
    [[560, 530, 3.1, 0.3], [590, 540, 2.3, 0.22], [545, 575, 2.5, 0.26]].forEach((c) => {
      place(cylY(c[3], c[2], 22), clay, c[0], c[1], c[2] / 2);
      place(new T.SphereGeometry(c[3], 22, 12), clay, c[0], c[1], c[2]);
    });
    /* tank farm */
    [[270, 390], [330, 370], [260, 460], [320, 450], [170, 420]].forEach((p, i) => {
      place(cylY(0.8 - (i % 2) * 0.1, 0.75, 36), clay, p[0], p[1], 0.37);
      place(new T.CylinderGeometry(0.1, 0.8 - (i % 2) * 0.1, 0.14, 36), clay2, p[0], p[1], 0.82);
    });
    /* cooling towers */
    [[820, 680], [870, 660]].forEach((p) => {
      const pts = [];
      for (let i = 0; i <= 12; i++) { const t = i / 12; pts.push(new T.Vector2(0.56 - 0.28 * Math.sin(t * Math.PI * 0.85), t * 1.6)); }
      place(new T.LatheGeometry(pts, 30), clay, p[0], p[1], 0);
    });
    /* flare */
    place(cylY(0.05, 3.8, 10), clay2, 150, 300, 1.9);
    place(new T.SphereGeometry(0.11, 14, 10), accent, 150, 300, 3.85);

    const anchors = {};
    const anchor = (n, px, py, y) => {
      const o2 = new T.Object3D();
      const [x, z] = w(px, py);
      o2.position.set(x, y, z);
      scene.add(o2);
      anchors[n] = o2;
    };
    anchor("Furnaces", 370, 475, 2.2);
    anchor("Compressors", 700, 400, 1.2);
    anchor("Pumps", 300, 660, 0.5);
    anchor("Turbines", 625, 650, 1.1);
    anchor("Heat exchangers", 800, 530, 0.8);
    anchor("pin", 520, 520, 3.2);

    const camera = new T.PerspectiveCamera(26, 1, 0.5, 160);
    const dims = { w: 1, h: 1 };
    let running = true, tx = 0, ty = 0, sx = 0, sy = 0, base = 0;
    const v = new T.Vector3();
    const resize = () => {
      const r = canvas.getBoundingClientRect();
      if (r.width < 2) return;
      dims.w = r.width; dims.h = r.height;
      renderer.setSize(r.width, r.height, false);
      camera.aspect = r.width / r.height;
      base = camera.aspect > 1.5 ? 1 : 1.5 / camera.aspect;
      camera.updateProjectionMatrix();
    };
    new ResizeObserver(resize).observe(canvas);
    resize();
    const render = (t) => {
      sx += (tx - sx) * 0.05;
      sy += (ty - sy) * 0.05;
      const k = base;
      camera.position.set((1.5 + sx * 1.6) * k, (25.5 + sy) * k, (18.5 + (reduce ? 0 : Math.sin(t * 0.00018) * 0.25)) * k);
      camera.lookAt(0.6, 0, 2.5);
      renderer.render(scene, camera);
      if (o.onFrame) o.onFrame(api);
    };
    const loop = (t) => {
      requestAnimationFrame(loop);
      if (running) render(t || 0);
    };
    canvas.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      tx = (e.clientX - r.left) / r.width - 0.5;
      ty = (e.clientY - r.top) / r.height - 0.5;
    });
    const api = {
      resize,
      project(name) {
        const a = anchors[name];
        if (!a) return null;
        a.getWorldPosition(v);
        v.project(camera);
        return { x: (v.x * 0.5 + 0.5) * dims.w, y: (-v.y * 0.5 + 0.5) * dims.h };
      },
      start() { running = true; resize(); },
      stop() { running = false; },
    };
    requestAnimationFrame(loop);
    return api;
  }

  window.SKScenes = { Machine, Plant, thumbs };
})();
