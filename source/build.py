"""Assemble frames -> CFR video, apply camera zooms, burn captions, optionally mix narration.
Usage: python3 build.py [narration_dir]
narration_dir may contain 01.(aiff|wav|m4a|mp3) ... one file per caption line.
"""
import json, os, subprocess, sys, glob

HERE = os.path.dirname(os.path.abspath(__file__))
B = os.path.join(HERE, "build")
FR = os.path.join(B, "frames")
W, H, FPS = 1440, 900, 30
UP = 2  # upscale factor before zoompan (reduces jitter)
tl = json.load(open(os.path.join(B, "timeline.json")))
nd = sys.argv[1] if len(sys.argv) > 1 else None
if nd:
    clips_ = sorted(glob.glob(os.path.join(nd, "[0-9][0-9].*")))
    for c, f in zip(tl["caps"], clips_):
        d = float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f]))
        c["end"] = max(c["end"], c["start"] + 0.15 + d + 0.2)

def run(cmd):
    print(">", " ".join(cmd)[:160]); subprocess.run(cmd, check=True)

# 1) frames -> CFR
files = sorted(os.listdir(FR))
ts = [float(f.split("_")[1][:-4]) for f in files]
t0 = ts[0]
with open(os.path.join(B, "frames.txt"), "w") as f:
    for i, name in enumerate(files):
        d = (ts[i + 1] - ts[i]) if i + 1 < len(files) else 4.0
        f.write(f"file 'frames/{name}'\nduration {d:.4f}\n")
    f.write(f"file 'frames/{files[-1]}'\n")
raw = os.path.join(B, "raw.mp4")
os.environ.get("MIXONLY") or run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", os.path.join(B, "frames.txt"),
     "-vf", f"fps={FPS},scale={W}:{H}:flags=lanczos,format=yuv420p", "-c:v", "libx264", "-crf", "12", "-preset", "medium", raw])

# timeline times are relative to first frame timestamp already (t0 = first frame)
R = 0.75  # ramp seconds
T = f"(in/{FPS})"
zexpr, xexpr, yexpr = ["st(1,0)"], ["st(1,0);st(2,0);st(3,0)"], ["st(1,0);st(2,0);st(3,0)"]
for z in tl["zooms"]:
    s, e, Z = z["start"], z.get("end", tl["total"]), z["z"]
    E = f"st(0,clip(min(({T}-{s:.3f})/{R},({e:.3f}-{T})/{R}),0,1));st(0,ld(0)*ld(0)*(3-2*ld(0)))"
    zexpr += [E, f"st(1,ld(1)+{Z-1:.3f}*ld(0))"]
    for ex, f_ in ((xexpr, z["cx"]), (yexpr, z["cy"])):
        ex += [E, f"st(1,ld(1)+gt(ld(0),0))", f"st(2,ld(2)+{f_*UP:.1f}*gt(ld(0),0))", f"st(3,ld(3)+ld(0))"]
zexpr.append("1+ld(1)")
# x = clip(f - (f/W + (0.5 - f/W)*E) * W/zoom, 0, W - W/zoom), in upscaled coords
def fin(dim):
    D = dim * UP
    return f"if(ld(1),clip(ld(2)-(ld(2)/{D}+(0.5-ld(2)/{D})*ld(3)*0.6)*{D}/zoom,0,{D}-{D}/zoom),0)"
xexpr.append(fin(W)); yexpr.append(fin(H))

# 2) captions (ASS)
def ts_ass(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"
ass = os.path.join(B, "captions.ass")
with open(ass, "w") as f:
    f.write(f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,Inter,29,&H00FFFFFF,&H00FFFFFF,&H5A2A2420,&H00000000,0,0,0,0,100,100,0,0,3,9,0,2,250,250,46,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
""")
    for c in tl["caps"]:
        f.write(f"Dialogue: 0,{ts_ass(c['start'])},{ts_ass(c['end'])},Cap,,0,0,0,,{c['text']}\n")

# 3) zoom + captions
vf = (f"scale={W*UP}:{H*UP}:flags=lanczos,"
      f"zoompan=z='{';'.join(zexpr)}':x='{';'.join(xexpr)}':y='{';'.join(yexpr)}':d=1:s={W}x{H}:fps={FPS},"
      f"subtitles={ass}:fontsdir=/usr/share/fonts,format=yuv420p")
silent = os.path.join(B, "elective-navigator-demo-silent.mp4")
os.environ.get("MIXONLY") or run(["ffmpeg", "-y", "-v", "error", "-i", raw, "-vf", vf, "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-movflags", "+faststart", silent])

# 4) optional narration
if nd:
    clips = sorted(glob.glob(os.path.join(nd, "[0-9][0-9].*")))
    assert len(clips) == len(tl["caps"]), f"{len(clips)} clips vs {len(tl['caps'])} lines"
    inputs, parts = [], []
    for i, (c, cap) in enumerate(zip(clips, tl["caps"])):
        inputs += ["-i", c]; ms = int(cap["start"] * 1000) + 150
        parts.append(f"[{i+1}:a]aresample=48000,adelay={ms}|{ms}[a{i}]")
    mix = ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(clips))) + f"amix=inputs={len(clips)}:normalize=0,loudnorm=I=-16[aout]"
    out = os.path.join(B, "elective-navigator-demo.mp4")
    run(["ffmpeg", "-y", "-v", "error", "-i", silent, *inputs, "-filter_complex", mix, "-map", "0:v", "-map", "[aout]",
         "-vf", "tpad=stop_mode=clone:stop_duration=2.5", "-c:v", "libx264", "-crf", "17", "-preset", "medium", "-c:a", "aac", "-b:a", "192k", "-t", str(round(tl["caps"][-1]["end"] + 1.5, 2)), "-movflags", "+faststart", out])
print("done")
