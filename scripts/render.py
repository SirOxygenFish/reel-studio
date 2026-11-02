"""reel-tool render <job> [--limit SEC] [--no-visuals] [--no-sfx] [--music file --music-db -24]

cut.json -> final.mp4 in the job folder:
  pieces/  every piece once, 1080x1920 30 fps, near-lossless, cached by (file, in, out): a re-render after a small recut is fast
  _base.mkv   the pieces joined, 20/30 ms fades at the joins, raw voice as PCM
  visuals.py  (when visuals.json exists) zooms, stickers, animation segments, then the subtitles on top
  voice chain once, on the raw voice; ring.wav (skits) mixed inside it; sound effects after it
  final.mp4   H.264 crf 20, yuv420p, 30 fps, AAC 192k, faststart, bt709 tags
A brief is mandatory: render refuses a job whose job.md still has TODO lines.
"""
import hashlib, json, os, re, subprocess, sys
from pathlib import Path

import common as C
import voice_chain

W, H, FPS, SR = 1080, 1920, 30, 48000
TONEMAP = "zscale=w={w}:h={h}:filter=spline36:t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p"
TAG709 = "setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"


def face_x(path, sw, sh):
    """median face centre (0..1 of the width), for cropping sources that are not 9:16"""
    try:
        import cv2, numpy as np
        det = cv2.FaceDetectorYN.create(str(C.ENVD / "models" / "face_detection_yunet_2023mar.onnx"), "", (480, 270 if sw > sh else 853), 0.7)
        w, h = (480, 270) if sw > sh else (480, 853)
        det.setInputSize((w, h))
        raw = subprocess.run([C.FF, "-v", "error", "-t", "60", "-i", str(path), "-vf", f"fps=0.5,scale={w}:{h}", "-pix_fmt", "bgr24", "-f", "rawvideo", "-"],
                             capture_output=True).stdout
        fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3); xs = []
        for g in fr:
            _, fs = det.detect(np.ascontiguousarray(g))
            if fs is not None and len(fs):
                b = max(fs, key=lambda q: q[2] * q[3]); xs.append((b[0] + b[2] / 2) / w)
        return float(np.median(xs)) if xs else 0.5
    except Exception:
        return 0.5


def chain(info, path):
    """fps, then HDR -> SDR, then cover 1080x1920 around the face (9:16 sources are only resized)"""
    sw, sh = info["width"], info["height"]; hdr = info["hdr"]
    ar = sw / sh if sh else 9 / 16
    if abs(ar - 9 / 16) <= 0.02:
        sc = TONEMAP.format(w=W, h=H) if hdr else f"scale={W}:{H}:flags=lanczos"
        return f"fps={FPS},{sc},setsar=1,{TAG709}"
    if ar > 9 / 16:
        nh, nw = H, int(round(sw * H / sh / 2)) * 2
        x = int(max(0, min(nw - W, face_x(path, sw, sh) * nw - W / 2)))
        crop = f"crop={W}:{H}:{x}:0"
    else:
        nw, nh = W, int(round(sh * W / sw / 2)) * 2
        crop = f"crop={W}:{H}:0:{(nh - H) // 2}"
    sc = TONEMAP.format(w=nw, h=nh) if hdr else f"scale={nw}:{nh}:flags=lanczos"
    return f"fps={FPS},{sc},{crop},setsar=1,{TAG709}"


def build_piece(job, k, file, a, b, info):
    n = max(1, int(round((b - a) * FPS))); ns = int(round(n * SR / FPS))
    key = hashlib.sha1(f"{file}|{a}|{b}|2".encode("utf-8")).hexdigest()[:12]
    out = job / "pieces" / f"p_{key}.mkv"
    if not out.exists():
        out.parent.mkdir(exist_ok=True)
        tmp = out.with_suffix(".tmp.mkv")
        vf = f"{chain(info, file)},trim=end_frame={n},setpts=PTS-STARTPTS"
        af = f"aresample={SR},atrim=end_sample={ns},asetpts=PTS-STARTPTS,afade=t=in:d=0.02,afade=t=out:st={n / FPS - 0.03:.3f}:d=0.03"
        r = C.ff("-ss", f"{a:.3f}", "-i", file, "-t", f"{b - a + 0.2:.3f}", "-vf", vf, "-af", af, "-map", "0:v:0", "-map", "0:a:0",
                 "-c:v", "libx264", "-preset", "fast", "-crf", "12", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", str(tmp))
        if r.returncode:
            C.fail(f"piece {k} failed: {r.stderr[-600:]}")
        os.replace(tmp, out)
    return out, n


def ass_filter(job, subs):
    """relative paths from the job folder: no drive-letter or non-ASCII escaping problems in the filter string"""
    name, ttf = C.sub_font(subs)
    d = job / "_fonts"; d.mkdir(exist_ok=True)
    if ttf:
        import shutil
        t = d / Path(ttf).name
        if not t.exists():
            shutil.copy(ttf, t)
    return "ass=subs.ass:fontsdir=_fonts"


def main(argv):
    job = C.job_dir(argv[0]).resolve(); os.chdir(job)
    opt = lambda k, d=None: argv[argv.index(k) + 1] if k in argv else d
    J = C.job_sync(job); cut = C.load_json("cut.json") or C.fail("no cut.json: run reel-tool analyze")
    brief = Path("job.md")
    if not brief.exists():
        C.fail("no job.md: the brief is mandatory. Run reel-tool brief, complete it, then render.")
    todo = [l for l in brief.read_text(encoding="utf-8").splitlines() if "TODO" in l]
    if todo:
        C.fail("job.md is not complete:\n  " + "\n  ".join(todo[:12]))
    if not Path("subs.ass").exists():
        C.fail("no subs.ass: run reel-tool subs first")
    infos = {x["file"]: x for x in J.get("info", [])}
    B = C.brand(J.get("brand")); subs = B["subs"]
    pieces, n_total = [], 0
    print(f"pieces: {len(cut['pieces'])}", flush=True)
    stab = J.get("stab") or {}
    for k, p in enumerate(cut["pieces"]):
        f, nf = build_piece(job, k, stab.get(p["file"], p["file"]), p["a"], p["b"], infos[p["file"]])
        pieces.append(f); n_total += nf
    Path("_list.txt").write_text("".join(f"file 'pieces/{p.name}'\n" for p in pieces), encoding="utf-8")
    base = "_base.mkv"
    limit = opt("--limit")
    args = ["-f", "concat", "-safe", "0", "-i", "_list.txt", "-c", "copy"] + (["-t", limit] if limit else []) + [base]
    r = C.ff(*args)
    if r.returncode:
        C.fail("join failed: " + r.stderr[-500:])
    py = sys.executable; here = Path(__file__).parent
    draft, voice = "_draft.mkv", "_voice.wav"
    ev = C.run_env()
    if Path("visuals.json").exists() and "--no-visuals" not in argv:
        rc = subprocess.run([py, str(here / "visuals.py"), base, "visuals.json", "subs.ass", draft], env=ev).returncode
        if rc:
            C.fail("visuals failed")
    else:
        vf = ass_filter(job, subs)
        r = C.ff("-i", base, "-vf", vf, "-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-c:a", "copy", draft)
        if r.returncode:
            C.fail("subtitle burn failed: " + r.stderr[-500:])
    atten = (C.config().get("voice") or {}).get("atten_db", "auto")
    if (B.get("voice") or {}).get("atten_db"):
        atten = B["voice"]["atten_db"]
    vr = voice_chain.run(draft, voice, atten, "ring.wav" if Path("ring.wav").exists() else None, preset=J.get("voice_preset"))
    C.save_json("voice_report.json", vr)
    sj = "_draft_sfx.json"
    if Path(sj).exists():
        if C.load_json(sj, []) and "--no-sfx" not in argv:
            r = subprocess.run([py, str(C.MOTION / "tools" / "sfx.py"), sj, voice, "_voice_sfx.wav"], env=ev)
            if r.returncode == 0:
                os.replace("_voice_sfx.wav", voice)
        os.remove(sj)
    music = opt("--music")
    if music:                                               # music sits on the finished voice, never before the chain
        db = float(opt("--music-db", "-24"))
        r = C.ff("-i", voice, "-stream_loop", "-1", "-i", music, "-filter_complex",
                 f"[1:a]aresample=48000,volume={db + 14:.1f}dB,afade=t=out:st={max(0, C.duration(voice) - 1.5):.2f}:d=1.5[m];[0:a][m]amix=inputs=2:duration=first:normalize=0,alimiter=limit=0.84[o]",
                 "-map", "[o]", "-c:a", "pcm_s16le", "_voice_music.wav")
        if r.returncode == 0:
            os.replace("_voice_music.wav", voice)
    tmp = "final.tmp.mp4"
    r = C.ff("-i", draft, "-i", voice, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-ac", "2", "-c:a", "aac", "-b:a", "192k",
             "-shortest", "-movflags", "+faststart", "-metadata", "comment=Reel Studio render", tmp)
    if r.returncode:
        C.fail("mux failed: " + r.stderr[-500:])
    os.replace(tmp, "final.mp4")
    for f in (base, draft, voice, "_list.txt"):
        Path(f).unlink(missing_ok=True)
    Path("gate.json").unlink(missing_ok=True)
    print(f"final.mp4: {C.duration('final.mp4'):.2f} s, {Path('final.mp4').stat().st_size / 1048576:.1f} MB. next: reel-tool gate {job.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
