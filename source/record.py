"""Scripted demo recording for Elective Navigator.
Captures frames via CDP screencast, logs caption + zoom timings to timeline.json.
"""
import base64, json, os, time, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
APP = "file://" + os.path.abspath(os.path.join(HERE, "..", "index.html"))
OUT = os.path.join(HERE, "build")
FR = os.path.join(OUT, "frames")
os.makedirs(FR, exist_ok=True)
for f in os.listdir(FR): os.remove(os.path.join(FR, f))
W, H = 1440, 900
WPS = 2.55          # narration speed estimate (words per second)
TEAM = os.environ.get("TEAM", "Group project · SE Course Registration Assignment")

CURSOR_JS = r"""
(() => {
  if (window.__cur) return;
  const c = document.createElement('div');
  c.innerHTML = '<svg width="26" height="26" viewBox="0 0 24 24"><path d="M4 2.5l15 9.2-6.6 1.4 3.9 7.3-2.6 1.4-3.9-7.3L4.9 19z" fill="#111" stroke="#fff" stroke-width="1.4" stroke-linejoin="round"/></svg>';
  Object.assign(c.style,{position:'fixed',left:'0',top:'0',zIndex:2147483647,pointerEvents:'none',transform:'translate(720px,450px)',filter:'drop-shadow(0 2px 3px rgba(0,0,0,.25))'});
  const r = document.createElement('div');
  Object.assign(r.style,{position:'fixed',width:'36px',height:'36px',borderRadius:'50%',border:'3px solid rgba(47,91,234,.7)',zIndex:2147483646,pointerEvents:'none',opacity:0,left:0,top:0});
  document.documentElement.append(c, r);
  window.__cur = {x:720,y:450,el:c,ring:r};
  window.__move = (x,y,ms) => new Promise(res => {
    const s = performance.now(), x0 = __cur.x, y0 = __cur.y;
    const step = now => {
      let p = Math.min(1,(now-s)/ms); const e = p<.5 ? 4*p*p*p : 1-Math.pow(-2*p+2,3)/2;
      __cur.x = x0+(x-x0)*e; __cur.y = y0+(y-y0)*e;
      c.style.transform = `translate(${__cur.x-4}px,${__cur.y-2}px)`;
      p<1 ? requestAnimationFrame(step) : res();
    }; requestAnimationFrame(step);
  });
  window.__ripple = () => { r.animate([{opacity:1,transform:`translate(${__cur.x-18}px,${__cur.y-18}px) scale(.4)`},{opacity:0,transform:`translate(${__cur.x-18}px,${__cur.y-18}px) scale(1.3)`}],{duration:450,easing:'ease-out'}); };
  window.__card = (html, show) => {
    let d = document.getElementById('__card');
    if (!d) { d = document.createElement('div'); d.id='__card';
      Object.assign(d.style,{position:'fixed',inset:0,zIndex:2147483640,display:'grid',placeItems:'center',background:'radial-gradient(1000px 600px at 50% 30%,#1c2f6b,#0b1430)',color:'#fff',fontFamily:'Inter,system-ui,sans-serif',transition:'opacity .7s',opacity:0});
      document.documentElement.append(d); }
    if (html !== null) d.innerHTML = html;
    c.style.transition = 'opacity .4s'; c.style.opacity = show ? 0 : 1;
    requestAnimationFrame(()=>{ d.style.opacity = show ? 1 : 0; d.style.pointerEvents = show ? 'auto':'none'; });
  };
})();
"""

INTRO = f"""
<div style="text-align:center;max-width:900px">
  <div style="width:96px;height:96px;margin:0 auto 26px;border-radius:28px;background:linear-gradient(135deg,#2f5bea,#5b7cff);display:grid;place-items:center;box-shadow:0 20px 50px rgba(47,91,234,.45)">
   <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2"><circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/></svg></div>
  <div style="font-size:64px;font-weight:800;letter-spacing:-.02em">Elective Navigator</div>
  <div style="font-size:24px;color:#b9c6ee;margin-top:12px">Choosing electives at Yaşar Software Engineering, without the guesswork</div>
  <div style="font-size:16px;color:#7f8fbf;margin-top:34px">{TEAM}</div>
</div>"""

PROBLEM = """
<div style="max-width:1000px;width:100%;padding:0 60px">
  <div style="font-size:16px;letter-spacing:.14em;text-transform:uppercase;color:#f08a4b;font-weight:700">The problem</div>
  <div style="font-size:44px;font-weight:800;margin:10px 0 34px;letter-spacing:-.01em">Electives are the hardest part of registration</div>
  <div style="display:grid;gap:16px">
   <div style="display:flex;gap:18px;align-items:center;background:rgba(255,255,255,.07);border-radius:16px;padding:20px 24px"><b style="font-size:30px;color:#8fb0ff;width:46px">1</b><div><b style="font-size:21px">70+ department and 150+ university electives</b><div style="color:#aab7de;margin-top:4px">listed by code and title only, with no way to search by interest</div></div></div>
   <div style="display:flex;gap:18px;align-items:center;background:rgba(255,255,255,.07);border-radius:16px;padding:20px 24px"><b style="font-size:30px;color:#8fb0ff;width:46px">2</b><div><b style="font-size:21px">Each elective counts only for certain slots</b><div style="color:#aab7de;margin-top:4px">A pool, B pool or University pool, in a specific semester</div></div></div>
   <div style="display:flex;gap:18px;align-items:center;background:rgba(255,255,255,.07);border-radius:16px;padding:20px 24px"><b style="font-size:30px;color:#8fb0ff;width:46px">3</b><div><b style="font-size:21px">Mistakes show up late</b><div style="color:#aab7de;margin-top:4px">a wrong-pool pick is often discovered only at the graduation check</div></div></div>
  </div>
</div>"""

OUTRO = f"""
<div style="text-align:center">
  <div style="font-size:54px;font-weight:800;letter-spacing:-.02em">Elective Navigator</div>
  <div style="display:flex;gap:14px;justify-content:center;margin-top:28px;font-size:18px">
    <span style="background:rgba(255,255,255,.1);padding:10px 18px;border-radius:30px">Search by interest</span>
    <span style="background:rgba(255,255,255,.1);padding:10px 18px;border-radius:30px">Right pool, right slot</span>
    <span style="background:rgba(255,255,255,.1);padding:10px 18px;border-radius:30px">No clashes, no full sections</span>
  </div>
  <div style="font-size:16px;color:#7f8fbf;margin-top:40px">{TEAM}</div>
</div>"""


class Rec:
    def __init__(s, page, cdp):
        s.page, s.cdp = page, cdp
        s.t0 = None; s.caps = []; s.zooms = []; s.n = 0
        cdp.on("Page.screencastFrame", s.on_frame)

    def on_frame(s, ev):
        ts = ev["metadata"]["timestamp"]
        if s.t0 is None: s.t0 = ts
        with open(os.path.join(FR, f"{s.n:06d}_{ts:.4f}.jpg"), "wb") as f:
            f.write(base64.b64decode(ev["data"]))
        s.n += 1
        try: s.cdp.send("Page.screencastFrameAck", {"sessionId": ev["sessionId"]})
        except Exception: pass

    def now(s): return time.time() - s.t0
    def wait(s, sec): s.page.wait_for_timeout(int(sec * 1000))

    # --- narration ---
    def say(s, text, min_hold=0.0):
        """Start a caption; returns a handle used by end()."""
        dur = max(len(text.split()) / WPS + 0.5, min_hold)
        h = {"text": text, "start": s.now(), "est": dur}
        s.caps.append(h); return h
    def end(s, h, gap=0.7):
        remaining = h["start"] + h["est"] - s.now()
        if remaining > 0: s.wait(remaining)
        h["end"] = s.now(); s.wait(gap)
    def line(s, text, gap=0.7):
        s.end(s.say(text), gap)

    # --- cursor ---
    def box(s, sel):
        el = s.page.locator(sel).first
        el.scroll_into_view_if_needed(); b = el.bounding_box(); return b
    def move(s, sel=None, xy=None, ms=750, dx=0.5, dy=0.5):
        if sel:
            b = s.box(sel); x, y = b["x"] + b["width"] * dx, b["y"] + b["height"] * dy
        else: x, y = xy
        s.page.evaluate(f"__move({x},{y},{ms})")
        s.page.mouse.move(x, y); return x, y
    def click(s, sel, ms=750, pause=0.25, **kw):
        x, y = s.move(sel, ms=ms, **kw); s.wait(pause)
        s.page.evaluate("__ripple()"); s.page.mouse.click(x, y); s.wait(0.35)
    def scroll(s, y, ms=900):
        s.page.evaluate(f"window.scrollTo({{top:{y},behavior:'smooth'}})"); s.wait(ms / 1000)

    # --- camera (applied in post) ---
    def zoom(s, sel=None, xy=None, z=1.35):
        if sel:
            b = s.box(sel); cx, cy = b["x"] + b["width"] / 2, b["y"] + b["height"] / 2
        else: cx, cy = xy
        h = {"start": s.now(), "cx": cx, "cy": cy, "z": z}; s.zooms.append(h); return h
    def unzoom(s, h): h["end"] = s.now()

    def card(s, html, show=True):
        s.page.evaluate("([h,v])=>__card(h,v)", [html, show])


def run():
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--force-device-scale-factor=1"])
        ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1)
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        page.goto(APP); page.wait_for_load_state("load")
        page.evaluate(CURSOR_JS)
        cdp = ctx.new_cdp_session(page)
        r = Rec(page, cdp)
        r.card(INTRO, True); page.wait_for_timeout(900)
        cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": W, "maxHeight": H, "everyNthFrame": 1})
        page.wait_for_timeout(400)
        # keep frames flowing even when static: tiny invisible animation
        page.evaluate("""(()=>{const d=document.createElement('div');Object.assign(d.style,{position:'fixed',left:0,top:0,width:'1px',height:'1px',zIndex:2147483647,pointerEvents:'none'});document.documentElement.append(d);let k=0;setInterval(()=>{d.style.background=(k++%2)?'rgba(0,0,0,.01)':'rgba(0,0,0,.02)'},33)})()""")
        r.wait(0.8)

        # 1 intro
        r.line("This is Elective Navigator, our course registration prototype for Yaşar University Software Engineering.", gap=0.6)
        # 2 problem
        r.card(PROBLEM, True); r.wait(0.9)
        r.line("When we asked classmates about registration, electives came up first.", gap=0.4)
        r.line("There are dozens of them, each one only counts for certain slots, and a wrong pick is often discovered at the graduation check.", gap=0.8)
        r.card(None, False); r.wait(0.9)

        # 3 sign in
        h = r.say("We sign in as a demo student in the fourth year.")
        r.click("#btn-signin", ms=1100); r.end(h)

        # 4 home
        z = r.zoom("#home-elec", z=1.45); r.wait(0.4)
        page.evaluate("document.getElementById('home-elec').classList.add('glow')")
        r.move("#home-dots", ms=900)
        r.line("The home page now shows elective progress at a glance: two slots completed, three due this term, and three more in spring.", gap=0.3)
        page.evaluate("document.getElementById('home-elec').classList.remove('glow')")
        r.unzoom(z); r.wait(0.8)

        # 5 planner
        h = r.say("The Elective Planner lays out every elective slot in the curriculum, which pool it accepts, and when it's due.")
        r.click("#btn-open-planner", ms=900); r.wait(0.5)
        z = r.zoom("#slots", z=1.3); r.wait(0.6)
        r.move("#slot-U1", ms=900); r.wait(0.4); r.move("#slot-A2", ms=900); r.wait(0.4); r.move("#slot-B1", ms=900)
        r.end(h, gap=0.2); r.unzoom(z); r.wait(0.9)

        # 6 interests
        h = r.say("We pick our interests: AI and data, and robotics.")
        r.click("[data-topic=ai]", ms=900); r.wait(0.3); r.click("[data-topic=robo]", ms=700)
        r.end(h, gap=0.4)

        # 7 ranking + why
        h = r.say("Electives are ranked by interest, and by how well this student did in the courses they build on. Every card explains why.")
        r.scroll(560); r.wait(0.3)
        r.move("#cc-COMP4462 .match", ms=900); r.wait(0.8)
        r.move("#cc-COMP4462 .why", ms=700, dx=0.35)
        z = r.zoom("#cc-COMP4462", z=1.6)
        r.end(h, gap=0.2); r.unzoom(z); r.wait(0.8)

        # 8 filters
        h = r.say("Two switches hide everything that clashes with a compulsory course, or is already full.")
        r.move("#cc-SE4488 .tag.tBad", ms=900); r.wait(0.8)
        r.click("#tg-fit", ms=900); r.wait(0.4); r.click("#tg-seat", ms=600); r.wait(0.3)
        r.move("#count", ms=600)
        r.end(h)

        # 9 details + add
        h = r.say("Details show the schedule, what the course builds on, and exactly which slots it counts toward.")
        r.click("[data-info='COMP 4350']", ms=900); r.wait(0.6)
        r.move("#drawer .counts", ms=900, dy=0.3); r.wait(0.5); r.move("#drawer .counts", ms=900, dy=0.85)
        r.end(h, gap=0.3)
        h = r.say("We add Machine Learning to slot A2.")
        r.click("#drawer [data-add='COMP 4350']", ms=800); r.wait(0.5)
        r.click("#modal [data-slot='A2']", ms=800); r.wait(0.3)
        r.scroll(0, 700); r.end(h, gap=0.4)

        # 10 the classic mistake
        h = r.say("Now, a classic mistake: Robot Mechanics sounds perfect for a robotics fan.")
        r.scroll(560, 700)
        r.click("#q", ms=800); page.keyboard.type("robot", delay=140); r.wait(0.5)
        r.move("#cc-ME4240", ms=800, dy=0.2)
        r.end(h, gap=0.2)
        h = r.say("But it belongs to the B pool and is only offered in spring, so it wouldn't count this term. The planner explains why, and offers robotics courses that do count.")
        r.click("#cc-ME4240 [data-add]", ms=700); r.wait(0.6)
        z = r.zoom("#modal .why-box", z=1.3)
        r.move("#modal .why-box", ms=900, dx=0.6); r.wait(1.2)
        r.move("#modal .alt", ms=900, dx=0.4)
        r.end(h, gap=0.0); r.unzoom(z); r.wait(0.6)
        r.click("#modal [data-put='SE 4406']", ms=700); r.wait(0.4)

        # 11 auto-fill
        page.fill("#q", ""); page.evaluate("document.getElementById('q').dispatchEvent(new Event('input'))")
        r.scroll(0, 800)
        h = r.say("The last open slot is filled automatically, with the best clash-free match.")
        r.click("#btn-autofill", ms=900); r.wait(0.5)
        r.move("#slot-A3", ms=800)
        r.end(h, gap=0.4)

        # 12 spring
        h = r.say("One more click drafts next spring too, including Robot Mechanics, in the slot where it actually counts.")
        r.click("#btn-spring", ms=900); r.wait(0.4)
        z = r.zoom("#slot-B2", z=1.35)
        r.move("#slot-B2", ms=900)
        r.end(h, gap=0.2); r.unzoom(z); r.wait(0.8)

        # 13 summary + submit
        h = r.say("The summary checks every rule: the right pools, no clashes, open seats, and thirty-seven of forty ECTS.")
        r.click("#btn-review", ms=900); r.wait(0.6)
        r.move("#modal .checks", ms=900, dx=0.3)
        z = r.zoom("#modal .checks", z=1.3)
        r.end(h, gap=0.2); r.unzoom(z); r.wait(0.7)
        h = r.say("We send it to the advisor, and download the plan.")
        r.click("#btn-confirm", ms=800); r.wait(0.8)
        r.click("#btn-png", ms=800); r.wait(0.5)
        r.move(xy=(1300, 700), ms=900)
        r.end(h, gap=0.3)

        # 14 result
        z = r.zoom(xy=(840, 330), z=1.4)
        r.line("From scattered course codes to a complete, valid elective plan in under two minutes.", gap=0.3)
        r.unzoom(z); r.wait(0.8)

        # 15 outro
        r.card(OUTRO, True); r.wait(0.9)
        r.line("That's Elective Navigator. Thanks for watching.", gap=1.5)
        r.wait(0.6)
        cdp.send("Page.stopScreencast"); page.wait_for_timeout(300)
        total = r.now()
        json.dump({"caps": r.caps, "zooms": r.zooms, "total": total}, open(os.path.join(OUT, "timeline.json"), "w"), indent=1)
        print("frames", r.n, "duration", round(total, 1))
        b.close()

if __name__ == "__main__":
    run()
