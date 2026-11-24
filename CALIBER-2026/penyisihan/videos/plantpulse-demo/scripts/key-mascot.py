"""Key the PlantPulse mascot off its flat cream background.

The source art is a flat cartoon on a known cream (~#f2f2e8) with a thick navy outline,
and the dial face is the SAME cream as the background, so a colour key or a person-seg
model cannot work. Instead:

  1. background = cream-like pixels (plus the grey floor shadow) CONNECTED to the frame border,
     so the enclosed dial face stays opaque;
  2. edge band = the 3 px of foreground next to that background, un-mixed against the cream:
     alpha = projection of (pixel - cream) onto (nearest interior colour - cream), colour = that
     interior colour (no cream fringe on a dark ground);
  3. the floor shadow becomes a soft black contact shadow (alpha = how much darker than cream).

The lockup clip (mode "lockup") is also re-timed and re-scaled: from 6.0 s the generated source
shrinks the mascot and fades a wordmark in under it. We drop the wordmark and scale every later
frame back to the walk-in size (feet pinned), so one continuous take runs walk -> wave -> idle ->
jump -> wink at a constant size, then hold the last frame for the fade-out.

Usage:
  python scripts/key-mascot.py image   assets/mascot/logo-src.jpg  assets/mascot/logo-cut.png
  python scripts/key-mascot.py lockup  assets/mascot/wave-src.mp4  <frames_dir>
  then: ffmpeg -framerate 24 -i <frames_dir>/f%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p
        -b:v 0 -crf 22 -auto-alt-ref 0 assets/mascot/mascot-lockup.webm
"""
import sys, os
import cv2
import numpy as np

BG_TOL = 24.0     # RGB distance still counted as cream (connectivity seed)
BAND = 3          # px of edge band to un-mix


def key(rgb, drop_below=None):
    f = rgb.astype(np.float32)
    h, w, _ = f.shape
    border = np.concatenate([f[0], f[-1], f[:, 0], f[:, -1]])
    B = np.median(border, 0)
    d = np.linalg.norm(f - B, axis=2)

    # Shadow: same chromaticity as cream, just darker (k = brightness ratio).
    k = (f @ B) / float(B @ B)
    chroma = np.linalg.norm(f - k[..., None] * B, axis=2)
    shadow = (k > 0.70) & (k < 0.995) & (chroma < 9)

    seed = ((d < BG_TOL) | shadow).astype(np.uint8)
    n, lab = cv2.connectedComponents(seed, connectivity=4)
    edge_labels = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    edge_labels = edge_labels[edge_labels != 0]
    bg = np.isin(lab, edge_labels)
    fg = ~bg
    if drop_below is not None:
        fg[drop_below:] = False
        bg[drop_below:] = True

    # Interior colours: nearest pixel at least BAND px inside the foreground.
    interior = cv2.erode(fg.astype(np.uint8), np.ones((3, 3), np.uint8), iterations=BAND).astype(bool)
    rgb_out = f.copy()
    alpha = fg.astype(np.float32)
    if interior.any():
        inv = (~interior).astype(np.uint8)
        _, labels = cv2.distanceTransformWithLabels(inv, cv2.DIST_L2, 5, labelType=cv2.DIST_LABEL_PIXEL)
        ys, xs = np.nonzero(interior)
        # label ids for zero pixels are assigned in scan order of the zero pixels
        lut = np.zeros((labels.max() + 1, 3), np.float32)
        zero_lab = labels[ys, xs]
        lut[zero_lab] = f[ys, xs]
        F = lut[labels]
        band = fg & ~interior
        diff = F - B
        den = np.maximum((diff * diff).sum(2), 1.0)
        a = ((f - B) * diff).sum(2) / den
        a = np.clip(a, 0, 1)
        # Only trust the un-mix where the interior colour is clearly not cream.
        far = np.sqrt(den) > 60
        alpha = np.where(band & far, a, alpha)
        rgb_out = np.where((band & far)[..., None], F, rgb_out)

    # Soft black contact shadow from the cream floor shadow.
    sh = bg & shadow
    if drop_below is not None:
        sh[drop_below:] = False
    sa = np.clip((1 - k) * 2.2, 0, 0.55)
    alpha = np.where(sh, sa, alpha)
    rgb_out = np.where(sh[..., None], 0, rgb_out)

    out = np.dstack([np.clip(rgb_out, 0, 255), alpha * 255]).astype(np.uint8)
    return out


# Lockup clip geometry (source px). Measured: walk-in standing height 495, feet at y 614;
# after the source's shrink (frame >= 164) standing height 413, feet 518.5, centre x 632.
SRC_START = 6          # 0.25 s: the mascot is still fully off the left edge
MORPH = (143, 164)     # frames where the source shrinks the mascot
LATE_SCALE = 495 / 413
OUT_SCALE = 1.134      # baked display scale -> 1452x816 shown 1:1 in the lockup
HOLD_TO = 270          # freeze the last source frame until here (fade-out covers it)


def mascot_extent(alpha):
    a = (alpha > 200).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(a, 8)
    k = 1 + int(np.argmax(st[1:, 4]))
    x, y, w, h, _ = st[k]
    return y, y + h


def lockup_frame(i, rgba):
    h0, w0 = rgba.shape[:2]
    if i >= MORPH[0]:
        top, bot = mascot_extent(rgba[:, :, 3])
        rgba = rgba.copy()
        rgba[bot + 16:, :, 3] = 0          # the source's wordmark sits below the feet
        if i < MORPH[1]:
            p = (i - MORPH[0]) / (MORPH[1] - MORPH[0])
            s, cx, fb = 495 / (bot - top), 645 + (632 - 645) * p, bot
        else:
            s, cx, fb = LATE_SCALE, 632, 518.5
        # x' = (x - cx) * s + 645 ; y' = (y - fb) * s + 614
        M = np.float32([[s, 0, 645 - cx * s], [0, s, 614 - fb * s]])
        rgba = warp(rgba, M, (w0, h0))
    M = np.float32([[OUT_SCALE, 0, 0], [0, OUT_SCALE, 0]])
    return warp(rgba, M, (round(w0 * OUT_SCALE / 2) * 2, round(h0 * OUT_SCALE / 2) * 2))


def warp(rgba, M, size):
    # premultiply so edges don't pick up dark fringes from transparent neighbours
    f = rgba.astype(np.float32)
    a = f[:, :, 3:] / 255
    pm = np.dstack([f[:, :, :3] * a, f[:, :, 3:]])
    o = cv2.warpAffine(pm, M, size, flags=cv2.INTER_CUBIC, borderValue=0)
    o = np.clip(o, 0, 255)
    oa = o[:, :, 3:] / 255
    rgb = np.where(oa > 1e-3, o[:, :, :3] / np.maximum(oa, 1e-3), 0)
    return np.dstack([np.clip(rgb, 0, 255), o[:, :, 3:]]).astype(np.uint8)


def main():
    mode, src, dst = sys.argv[1:4]
    if mode == "image":
        img = cv2.imread(src)[:, :, ::-1]
        out = key(img)
        cv2.imwrite(dst, cv2.cvtColor(out, cv2.COLOR_RGBA2BGRA))
    else:
        os.makedirs(dst, exist_ok=True)
        cap = cv2.VideoCapture(src)
        i, n, last = 0, 0, None
        while True:
            ok, fr = cap.read()
            if not ok:
                break
            if i >= SRC_START:
                last = lockup_frame(i, key(fr[:, :, ::-1]))
                cv2.imwrite(os.path.join(dst, f"f{n:04d}.png"), cv2.cvtColor(last, cv2.COLOR_RGBA2BGRA))
                n += 1
            i += 1
        while n < HOLD_TO - SRC_START:
            cv2.imwrite(os.path.join(dst, f"f{n:04d}.png"), cv2.cvtColor(last, cv2.COLOR_RGBA2BGRA))
            n += 1
        print("frames", n)


if __name__ == "__main__":
    main()
