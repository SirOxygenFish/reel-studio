"""Picture checks on the cut. They make the contact sheets Claude must look at, and record that it did.

reel-tool jump <job>             visual jump at every join: "<-- JUMP" (jump > 4 and > 3x normal motion) = a cut in the middle of
                                 a hand gesture. Keep that pause whole or move the cut (reel-tool bestcut).
reel-tool bestcut <job> K [W]    the calmest cut point near join K: frame pairs with the smallest body difference within W s
reel-tool sheets <job>           qf/eyes.jpg (eye-level strips of every face piece at 2.5 fps) and qf/mouth.jpg (the frames of each
                                 pause longer than 0.35 s, cropped on the mouth), with the eye and mouth height found by the
                                 face detector, so a crop can never miss them
reel-tool segsheet <job> [K]     K frames inside every animation segment -> qf/segs.jpg
reel-tool mark <job> eyes|mouth "what was seen"    record the review (the gate requires both, with a note)
"""
import json, os, subprocess, sys, time
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import common as C

FF = C.FF


def frame(file, t, w=270, h=480):
    r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{max(0, t):.3f}", "-i", str(file), "-frames:v", "1",
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
    return np.frombuffer(r, np.uint8).reshape(h, w).astype(np.float32)[int(h * .25):int(h * .83)]        # shoulders, arms, hands


def d(x, y):
    return float(np.mean(np.abs(x - y)))


def jump(job):
    cut = C.load_json(job / "cut.json"); P = cut["pieces"]; flags = []
    for k in range(len(P) - 1):
        p, q = P[k], P[k + 1]
        last, prev, first = frame(p["file"], p["b"] - 0.04), frame(p["file"], p["b"] - 0.07), frame(q["file"], q["a"])
        j, n = d(last, first), d(prev, last); bad = j > 4 and j > 3 * n
        print(f"join {k:2d}->{k + 1:2d}  {p['b']:7.2f} | {q['a']:7.2f}  jump={j:5.1f}  normal={n:4.1f}  {'<-- JUMP' if bad else ''}")
        if bad:
            flags.append(k)
    C.save_json(job / "jump_report.json", {"joins": len(P) - 1, "jumps": flags})
    print(f"JUMPS: {len(flags)}")


def bestcut(job, k, win=0.5, fps=15):
    cut = C.load_json(job / "cut.json"); P = cut["pieces"]; p, q = P[k], P[k + 1]

    def frames(f, a, b):
        r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", str(f), "-vf",
                            f"fps={fps},scale=270:480,format=gray", "-f", "rawvideo", "-"], capture_output=True).stdout
        x = np.frombuffer(r, np.uint8).reshape(-1, 480, 270).astype(np.float32)[:, 120:400]
        return [(a + i / fps, x[i]) for i in range(len(x))]
    A, B = frames(p["file"], p["b"] - win, p["b"]), frames(q["file"], q["a"], q["a"] + win)
    best = sorted(((float(np.mean(np.abs(x - y))), ta, tb) for ta, x in A for tb, y in B), key=lambda z: z[0])[:3]
    for dv, ta, tb in best:
        print(f"diff={dv:4.1f}  out of piece {k} at {ta:.2f}, into piece {k + 1} at {tb:.2f}   (under 2.5 = invisible; 6 is normal between two takes)")


def face_landmarks(frame_bgr, det):
    _, fs = det.detect(np.ascontiguousarray(frame_bgr))
    if fs is None or not len(fs):
        return None
    b = max(fs, key=lambda q: q[2] * q[3])
    return b


def locate(job, cut):
    """per piece: eye line and mouth centre in 1080x1920 piece coordinates, from the YuNet landmarks"""
    import cv2
    det = cv2.FaceDetectorYN.create(str(C.ENVD / "models" / "face_detection_yunet_2023mar.onnx"), "", (540, 960), 0.6)
    out = []
    for k, p in enumerate(cut["pieces"]):
        f = piece_file(job, p)
        raw = subprocess.run([FF, "-v", "error", "-i", str(f), "-vf", "fps=2,scale=540:960", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, 960, 540, 3); pts = []
        for g in fr:
            b = face_landmarks(g, det)
            if b is not None:
                pts.append(b[:14] * 2)
        if pts:
            m = np.median(np.array(pts), 0)
            eye_y = (m[5] + m[7]) / 2; eye_x = (m[4] + m[6]) / 2; mouth = ((m[10] + m[12]) / 2, (m[11] + m[13]) / 2); fw = m[2]
            out.append({"eye": (float(eye_x), float(eye_y)), "mouth": (float(mouth[0]), float(mouth[1])), "w": float(fw)})
        else:
            out.append(None)
    return out


def piece_file(job, p):
    import hashlib
    f = ((C.load_json(job / "job.json", {}) or {}).get("stab") or {}).get(p["file"], p["file"])
    return job / "pieces" / ("p_" + hashlib.sha1(f"{f}|{p['a']}|{p['b']}|2".encode("utf-8")).hexdigest()[:12] + ".mkv")


def tile(paths_labels, cols, cw, ch, out):
    F = ImageFont.truetype(C.sub_font()[1], 15)
    rows = (len(paths_labels) + cols - 1) // cols
    S = Image.new("RGB", (cols * cw, rows * ch), (20, 20, 20)); D = ImageDraw.Draw(S)
    for i, (im, lab) in enumerate(paths_labels):
        x, y = i % cols * cw, i // cols * ch
        r = min((cw - 2) / im.width, (ch - 2) / im.height); im2 = im.resize((int(im.width * r), int(im.height * r)))
        S.paste(im2, (x + 1, y + 1)); D.text((x + 4, y + 3), lab, fill=(255, 230, 60), font=F)
    S.save(out, quality=88)


def crop_frames(file, ts, box):
    x0, y0, x1, y1 = [int(v) // 2 * 2 for v in box]; ims = []
    for t in ts:
        r = subprocess.run([FF, "-hide_banner", "-loglevel", "error", "-ss", f"{t:.3f}", "-i", str(file), "-frames:v", "1", "-vf",
                            f"crop={x1 - x0}:{y1 - y0}:{x0}:{y0}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
        if len(r) == (x1 - x0) * (y1 - y0) * 3:
            ims.append(Image.frombuffer("RGB", (x1 - x0, y1 - y0), r))
        else:
            print(f"WARNING: no frame at {t:.2f} s of {Path(file).name}")
    return ims


def sheets(job):
    cut = C.load_json(job / "cut.json"); V = C.load_json(job / "visuals.json", {}) or {}
    if not all(piece_file(job, p).exists() for p in cut["pieces"]):
        C.fail("pieces not built yet: run reel-tool pieces " + job.name)
    (job / "qf").mkdir(exist_ok=True)
    segs = (V.get("hybrid") or {}).get("segments", [])
    loc = locate(job, cut); eyes, o = [], 0.0
    for k, (p, L) in enumerate(zip(cut["pieces"], loc)):
        n = p["b"] - p["a"]
        if L:
            ey = L["eye"][1]; ex = L["eye"][0]; hw = max(300, L["w"] * 1.05); hh = hw * 0.36
            box = (max(0, ex - hw), max(0, ey - hh), min(1080, ex + hw), min(1920, ey + hh))
            ts = list(np.arange(0.05, max(0.1, n - 0.05), 0.4))
            keep = [t for t in ts if not any(s["t0"] <= o + t <= s["t1"] for s in segs)]
            ims = crop_frames(piece_file(job, p), keep, box)
            if len(ims) < len(keep):
                C.fail(f"could not read frames of piece {k}: the eye sheet would be incomplete")
            for t, im in zip(keep, ims):
                eyes.append((im.resize((220, int(220 * im.height / im.width))), f"{o + t:.1f}"))
        o += n
    if eyes:
        tile(eyes, 8, 220, 92, job / "qf" / "eyes.jpg")
    mouths, o = [], 0.0
    pauses = []
    ws = []
    for k, p in enumerate(cut["pieces"]):
        for w in p["words"]:
            ws.append((k, w[0], w[1]))
    for (k1, s1, e1), (k2, s2, e2) in zip(ws, ws[1:]):
        if k1 == k2 and s2 - e1 >= 0.2:
            pauses.append((k1, max(e1, s2 - 0.4), s2))
    for k, a, b in pauses[:24]:
        p = cut["pieces"][k]; L = loc[k]
        if not L:
            continue
        mx, my = L["mouth"]; hw = max(120, L["w"] * 0.42)
        box = (max(0, mx - hw), max(0, my - hw * 0.62), min(1080, mx + hw), min(1920, my + hw * 0.62))
        ts = list(np.arange(a - p["a"], b - p["a"] + 0.001, 0.1))[:5]
        off = sum(q["b"] - q["a"] for q in cut["pieces"][:k])
        for t, im in zip(ts, crop_frames(piece_file(job, p), ts, box)):
            mouths.append((im, f"{off + t:.2f}"))
    if mouths:
        tile(mouths, 8, 200, 130, job / "qf" / "mouth.jpg")
    print(f"qf/eyes.jpg: {len(eyes)} frames of {sum(1 for x in loc if x)} face pieces (of {len(loc)}); "
          f"qf/mouth.jpg: {len(mouths)} frames of {len(pauses)} pauses from 0.2 s (the last 0.4 s before each word)" + ("" if mouths else " (no long pause left: nothing to check)"))
    print("Eyes: a blink is 1 frame; several frames in a row with lids half down = looking away (reading). Mouth: lips parted and still for more "
          "than 0.15 s (2 tiles) before a word = an idle mouth: move the in-point closer to the word without touching it, or name it in the report.")


def segsheet(job, kk=3):
    V = C.load_json(job / "visuals.json"); ts = []
    for s in (V.get("hybrid") or {}).get("segments", []):
        ts += [round(s["t0"] + (s["t1"] - s["t0"]) * (i + 0.6) / (kk + 0.2), 2) for i in range(kk)]
    ims = []
    for t in ts:
        ims.append((crop_frames(job / "final.mp4", [t], (0, 0, 1080, 1920))[0].resize((240, 427)), f"{t}"))
    (job / "qf").mkdir(exist_ok=True)
    tile(ims, kk * 3 if len(ts) >= kk * 3 else max(1, len(ts)), 240, 427, job / "qf" / "segs.jpg")
    print(job / "qf" / "segs.jpg")


def mark(job, what, note):
    M = C.load_json(job / "reviews.json", {}) or {}
    M[what] = note; M[what + "_at"] = time.time(); C.save_json(job / "reviews.json", M)
    print("recorded", what)


def main(cmd, argv):
    job = C.job_dir(argv[0])
    if cmd == "jump":
        jump(job)
    elif cmd == "bestcut":
        bestcut(job, int(argv[1]), float(argv[2]) if len(argv) > 2 else 0.5)
    elif cmd == "sheets":
        sheets(job)
    elif cmd == "segsheet":
        segsheet(job, int(argv[1]) if len(argv) > 1 else 3)
    elif cmd == "mark":
        mark(job, argv[1], " ".join(argv[2:]))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
