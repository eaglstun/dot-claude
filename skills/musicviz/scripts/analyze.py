#!/usr/bin/env python3
"""
musicviz phase doctor — inspect the stereo field / phase health of any audio file.

Answers "is this phasey?" with numbers instead of vibes: L/R correlation, stereo
width (mid/side), mono fold-down cancellation, a per-section timeline (to catch a
bad passage inside an otherwise-fine mix), and inter-channel delay detection — then
a plain-English verdict and, if warranted, the ffmpeg command to fix it.

    ./analyze.py song.mp3
    ./analyze.py track.wav --segments 20
    ./analyze.py mix.flac --json

Reads only — it NEVER writes to or modifies the input. Fix commands are printed for
you to run against a COPY. Uses numpy if present (fast), else a stdlib fallback.

WHAT THE NUMBERS MEAN
  L/R correlation   +1 = identical (mono)     0 = independent/wide     -1 = inverted
  side/mid ratio    ~0 centered/narrow    ~0.3–0.7 healthy wide    >1 very wide/phasey
  mono fold-down    dB lost when summed to mono; near 0 = safe, very negative = cancels
"""
import argparse, json, math, os, shlex, subprocess, sys

def sh(cmd):
    return subprocess.run(cmd, capture_output=True).stdout

def probe(path):
    out = sh(["ffprobe","-hide_banner","-loglevel","error","-select_streams","a:0",
              "-show_entries","stream=channels,sample_rate:format=duration",
              "-of","json", path])
    try:
        j = json.loads(out)
        st = j["streams"][0]
        return int(st["channels"]), int(st["sample_rate"]), float(j["format"]["duration"])
    except Exception:
        sys.exit(f"couldn't probe {path} — is it an audio file? is ffmpeg installed?")

def decode(path, sr):
    raw = sh(["ffmpeg","-hide_banner","-loglevel","error","-i",path,
              "-ac","2","-ar",str(sr),"-f","f32le","-"])
    return raw

def mmss(sec):
    m=int(sec//60); s=sec-60*m; return f"{m:d}:{s:05.2f}"

# ---------------- numpy path ----------------
def analyze_np(raw, sr, segments):
    import numpy as np
    x = np.frombuffer(raw, dtype=np.float32)
    x = x[:len(x)-(len(x)%2)].reshape(-1,2)
    L = x[:,0].astype(np.float64); R = x[:,1].astype(np.float64)
    n = len(L)
    def corr(a,b):
        a=a-a.mean(); b=b-b.mean()
        d=math.sqrt(float((a*a).sum())*float((b*b).sum()))
        return float((a*b).sum())/d if d>0 else float('nan')
    overall = corr(L,R)
    rmsL=math.sqrt(float((L*L).mean())); rmsR=math.sqrt(float((R*R).mean()))
    mid=(L+R)*0.5; side=(L-R)*0.5
    rmsM=math.sqrt(float((mid*mid).mean())); rmsS=math.sqrt(float((side*side).mean()))
    ratio = rmsS/rmsM if rmsM>0 else float('inf')
    ref=math.sqrt((rmsL**2+rmsR**2)/2)
    mono_db = 20*math.log10(rmsM/ref) if ref>0 and rmsM>0 else float('-inf')
    # per-section
    segs=[]
    step=n//segments
    for i in range(segments):
        s=i*step; e=n if i==segments-1 else (i+1)*step
        segs.append((i*step/sr, corr(L[s:e],R[s:e])))
    # inter-channel delay via FFT cross-correlation, searched within +-10ms
    maxlag=int(sr*0.010)
    a=L-L.mean(); b=R-R.mean()
    N=1
    while N < 2*n: N<<=1
    fa=np.fft.rfft(a,N); fb=np.fft.rfft(b,N)
    cc=np.fft.irfft(fa*np.conj(fb),N)
    cc=np.concatenate((cc[-maxlag:],cc[:maxlag+1]))
    lags=np.arange(-maxlag,maxlag+1)
    k=int(np.argmax(cc)); best_lag=int(lags[k])
    denom=math.sqrt(float((a*a).sum())*float((b*b).sum()))
    corr_at=float(cc[k])/denom if denom>0 else 0.0
    return dict(n=n,sr=sr,overall=overall,rmsL=rmsL,rmsR=rmsR,ratio=ratio,
                mono_db=mono_db,segments=segs,best_lag=best_lag,
                best_lag_ms=1000*best_lag/sr,corr_at_lag=corr_at)

# ---------------- stdlib fallback ----------------
def analyze_std(raw, sr, segments):
    import array
    a=array.array('f'); a.frombytes(raw[:len(raw)-(len(raw)%8)])
    L=a[0::2]; R=a[1::2]; n=len(L)
    def corr(lo,hi):
        sl=sr_=sll=srr=slr=0.0
        for i in range(lo,hi):
            x=L[i]; y=R[i]; sl+=x; sr_+=y; sll+=x*x; srr+=y*y; slr+=x*y
        m=hi-lo; mL=sl/m; mR=sr_/m
        vL=sll/m-mL*mL; vR=srr/m-mR*mR; cov=slr/m-mL*mR
        return cov/math.sqrt(vL*vR) if vL>0 and vR>0 else float('nan')
    overall=corr(0,n)
    rmsL=math.sqrt(sum(v*v for v in L)/n); rmsR=math.sqrt(sum(v*v for v in R)/n)
    mid=[(L[i]+R[i])*0.5 for i in range(n)]; side=[(L[i]-R[i])*0.5 for i in range(n)]
    rmsM=math.sqrt(sum(v*v for v in mid)/n); rmsS=math.sqrt(sum(v*v for v in side)/n)
    ratio=rmsS/rmsM if rmsM>0 else float('inf')
    ref=math.sqrt((rmsL**2+rmsR**2)/2)
    mono_db=20*math.log10(rmsM/ref) if ref>0 and rmsM>0 else float('-inf')
    segs=[]; step=n//segments
    for i in range(segments):
        s=i*step; e=n if i==segments-1 else (i+1)*step
        segs.append((i*step/sr, corr(s,e)))
    # bounded lag search +-3ms (no FFT)
    maxlag=int(sr*0.003); best_lag=0; best=-2.0
    mL=sum(L)/n; mR=sum(R)/n
    for lag in range(-maxlag,maxlag+1):
        s=0.0; cnt=0
        for i in range(max(0,-lag), min(n, n-lag)):
            s+=(L[i]-mL)*(R[i+lag]-mR); cnt+=1
        c=s/cnt if cnt else 0
        if c>best: best=c; best_lag=lag
    denom=math.sqrt(sum((v-mL)**2 for v in L)*sum((v-mR)**2 for v in R))/n
    return dict(n=n,sr=sr,overall=overall,rmsL=rmsL,rmsR=rmsR,ratio=ratio,
                mono_db=mono_db,segments=segs,best_lag=best_lag,
                best_lag_ms=1000*best_lag/sr,corr_at_lag=best/denom if denom else 0.0)

def bar(c):
    # correlation -1..1 -> a little glyph
    if c!=c: return "?"
    if c< -0.2: return "!"          # anti-correlated section
    blocks="▁▂▃▄▅▆▇█"
    return blocks[min(7,max(0,int((c+1)/2*8-0.001)))]

def verdict(a, path):
    q=shlex.quote(path)
    o=a["overall"]; ratio=a["ratio"]; mono=a["mono_db"]; lagms=a["best_lag_ms"]
    gain=a["corr_at_lag"]-o
    segs=[c for _,c in a["segments"] if c==c]
    bad=[(t,c) for t,c in a["segments"] if c==c and c<0]
    frac_bad=len(bad)/len(segs) if segs else 0
    recs=[]
    if o <= -0.4:
        head="⚠  POLARITY-INVERTED — the channels are pushing against each other."
        recs.append(("invert one channel's polarity",
                     f'ffmpeg -i {q} -af "aeval=val(0)|-1*val(1):c=same" fixed.wav'))
    elif a["corr_at_lag"] >= 0.6 and gain >= 0.10 and a["best_lag"] != 0:
        # only a real delay if aligning genuinely makes them correlate strongly
        earlier = "right" if a["best_lag"]>0 else "left"
        d=abs(a["best_lag"])
        ch = f"0|{d}S" if a["best_lag"]>0 else f"{d}S|0"
        head=f"⚠  INTER-CHANNEL DELAY ≈ {abs(lagms):.2f} ms — the {earlier} channel leads."
        recs.append((f"time-align by delaying the leading channel {d} samples",
                     f'ffmpeg -i {q} -af "adelay={ch}" fixed.wav'))
    elif mono <= -3.0 or frac_bad >= 0.25:
        why = (f"mono fold-down loses {mono:.1f} dB" if mono <= -3.0
               else f"{len(bad)} of {len(segs)} sections cancel in mono")
        head=f"⚠  PHASEY / MONO-INCOMPATIBLE — {why}."
        recs.append(("narrow the sides (tame a widener/reverb) — then re-check",
                     f'ffmpeg -i {q} -af "stereotools=slev=0.6" fixed.wav'))
    elif ratio > 1.0 or o < 0.2:
        head=(f"◐  VERY WIDE — correlation {o:+.2f}, but mono fold-down only {mono:+.1f} dB "
              f"(likely intentional/fine). Sanity-check it in mono on your target device.")
    else:
        head="✓  HEALTHY — well-correlated, mono-safe. Nothing to fix."
    if bad and o > 0 and "PHASEY" not in head:
        head += f"\n   (note: {len(bad)} section(s) dip anti-correlated — see the timeline ✱)"
    return head, recs

def main():
    ap=argparse.ArgumentParser(description="Stereo phase / correlation doctor for audio.",
        formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument("audio")
    ap.add_argument("--segments", type=int, default=16, help="timeline resolution (default 16)")
    ap.add_argument("--sr", type=int, default=44100, help="analysis sample rate (default 44100)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--force-stdlib", action="store_true", help="skip numpy even if present")
    args=ap.parse_args()
    if not os.path.isfile(args.audio): sys.exit(f"no such file: {args.audio}")

    ch,native_sr,dur = probe(args.audio)
    if ch < 2:
        msg=f"{os.path.basename(args.audio)} is mono ({ch}ch) — no stereo phase to analyze."
        print(json.dumps({"mono":True,"channels":ch}) if args.json else "✓  "+msg)
        return
    sr=min(args.sr, native_sr)
    raw=decode(args.audio, sr)
    if not raw: sys.exit("ffmpeg produced no audio — bad file or decode error.")

    use_np = not args.force_stdlib
    if use_np:
        try: a=analyze_np(raw, sr, args.segments)
        except ImportError: a=analyze_std(raw, sr, args.segments); use_np=False
    else:
        a=analyze_std(raw, sr, args.segments)

    head, recs = verdict(a, args.audio)

    if args.json:
        a2=dict(a); a2["segments"]=[{"t":t,"corr":c} for t,c in a["segments"]]
        a2["verdict"]=head; a2["fixes"]=[{"what":w,"cmd":c} for w,c in recs]
        print(json.dumps(a2, indent=2)); return

    print(f"\n  {os.path.basename(args.audio)}   {dur:.1f}s · {native_sr} Hz · analyzed @ {sr} Hz"
          f"{'' if use_np else ' (stdlib)'}")
    print(f"  {'─'*58}")
    print(f"  L/R correlation   {a['overall']:+.3f}")
    print(f"  stereo width      side/mid {a['ratio']:.3f}")
    print(f"  mono fold-down    {a['mono_db']:+.1f} dB")
    if abs(a['best_lag_ms']) >= 0.02 and a['corr_at_lag'] >= 0.5:
        print(f"  best alignment    {a['best_lag']:+d} samples ({a['best_lag_ms']:+.2f} ms), "
              f"corr→{a['corr_at_lag']:+.3f}")
    tl="".join(bar(c) for _,c in a["segments"])
    print(f"  timeline          {tl}   (✱=! anti-corr)")
    print(f"                    {mmss(0)} {'→'*max(1,args.segments-8)} {mmss(dur)}")
    print(f"  {'─'*58}")
    print(f"  {head}")
    for w,c in recs:
        print(f"\n  → {w}:\n    {c}")
    print(f"\n  (analysis only — input untouched; fix commands write a new file)\n")

if __name__=="__main__":
    main()
