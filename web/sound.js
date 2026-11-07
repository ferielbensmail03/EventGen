/* EventGen — sound design.
   Every sound is synthesised live with the Web Audio API (no audio files, no
   third-party or copyrighted material). The AudioContext is only created after
   an explicit user gesture (turning sound on), so nothing ever autoplays. */
(function () {
  const S = { enabled: false, ambient: false, volume: 0.45, ctx: null, master: null, amb: null, last: {} };

  function ensure() {
    if (S.ctx) { if (S.ctx.state === "suspended") S.ctx.resume(); return S.ctx; }
    const AC = window.AudioContext || window.webkitAudioContext;
    if (!AC) return null;
    S.ctx = new AC();
    S.master = S.ctx.createGain();
    S.master.gain.value = S.volume;
    const comp = S.ctx.createDynamicsCompressor();
    S.master.connect(comp).connect(S.ctx.destination);
    return S.ctx;
  }

  // throttle so repeated interactions never become annoying
  function allowed(name, gap) {
    const now = performance.now();
    if (S.last[name] && now - S.last[name] < gap) return false;
    S.last[name] = now;
    return true;
  }

  function tone({ f0, f1 = f0, type = "sine", dur = 0.12, gain = 0.12, delay = 0, attack = 0.004 }) {
    const ctx = S.ctx, t = ctx.currentTime + delay;
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f0, t);
    o.frequency.exponentialRampToValueAtTime(f1, t + dur);
    g.gain.setValueAtTime(0.0001, t);
    g.gain.exponentialRampToValueAtTime(gain, t + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
    o.connect(g).connect(S.master);
    o.start(t); o.stop(t + dur + 0.05);
  }

  const sounds = {
    click() {
      if (!allowed("click", 70)) return;
      const j = 1 + (Math.random() - 0.5) * 0.06;           // tiny variation: never identical
      tone({ f0: 1250 * j, f1: 780 * j, type: "sine", dur: 0.07, gain: 0.07 });
    },
    select() {
      if (!allowed("select", 60)) return;
      tone({ f0: 660, f1: 990, type: "triangle", dur: 0.09, gain: 0.05 });
    },
    transition() {
      if (!allowed("transition", 350)) return;
      const ctx = S.ctx, t = ctx.currentTime, dur = 0.55;
      const buf = ctx.createBuffer(1, ctx.sampleRate * dur, ctx.sampleRate);
      const d = buf.getChannelData(0);
      for (let i = 0; i < d.length; i++) d[i] = (Math.random() * 2 - 1) * 0.5;
      const src = ctx.createBufferSource(); src.buffer = buf;
      const bp = ctx.createBiquadFilter(); bp.type = "bandpass"; bp.Q.value = 1.4;
      bp.frequency.setValueAtTime(380, t); bp.frequency.exponentialRampToValueAtTime(2600, t + dur);
      const g = ctx.createGain();
      g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.05, t + 0.18); g.gain.exponentialRampToValueAtTime(0.0001, t + dur);
      src.connect(bp).connect(g).connect(S.master); src.start(t);
    },
    success() {
      if (!allowed("success", 800)) return;
      // soft major-ninth chime: E5, B5, F#6 with a slow tail
      [[659.25, 0], [987.77, 0.09], [1479.98, 0.18]].forEach(([f, d]) =>
        tone({ f0: f, type: "sine", dur: 1.4, gain: 0.06, delay: d, attack: 0.01 }));
      tone({ f0: 329.63, type: "triangle", dur: 1.2, gain: 0.03, attack: 0.02 });
    },
    error() {
      if (!allowed("error", 600)) return;
      tone({ f0: 330, f1: 247, type: "triangle", dur: 0.28, gain: 0.06 });
    },
  };

  function startAmbient() {
    if (S.amb || !ensure()) return;
    const ctx = S.ctx, out = ctx.createGain();
    out.gain.setValueAtTime(0.0001, ctx.currentTime);
    out.gain.exponentialRampToValueAtTime(0.16, ctx.currentTime + 3);     // slow fade-in
    const lp = ctx.createBiquadFilter(); lp.type = "lowpass"; lp.frequency.value = 520; lp.Q.value = 0.4;
    const lfo = ctx.createOscillator(), lfoGain = ctx.createGain();
    lfo.frequency.value = 0.05; lfoGain.gain.value = 180; lfo.connect(lfoGain).connect(lp.frequency);
    const oscs = [110, 164.81, 220.5, 277.18].map((f, i) => {
      const o = ctx.createOscillator(), g = ctx.createGain();
      o.type = i % 2 ? "triangle" : "sine"; o.frequency.value = f; o.detune.value = (i - 1.5) * 4;
      g.gain.value = [0.5, 0.25, 0.22, 0.12][i];
      o.connect(g).connect(lp); o.start(); return o;
    });
    lp.connect(out).connect(S.master); lfo.start();
    S.amb = { out, oscs, lfo };
  }
  function stopAmbient() {
    if (!S.amb) return;
    const { out, oscs, lfo } = S.amb, t = S.ctx.currentTime;
    out.gain.cancelScheduledValues(t); out.gain.setValueAtTime(out.gain.value, t);
    out.gain.exponentialRampToValueAtTime(0.0001, t + 1.2);
    setTimeout(() => { oscs.forEach(o => o.stop()); lfo.stop(); }, 1400);
    S.amb = null;
  }

  window.EGSound = {
    play(name) { if (S.enabled && ensure() && sounds[name]) sounds[name](); },
    setEnabled(on) {
      S.enabled = on;
      if (on) ensure();
      if (on && S.ambient) startAmbient();
      if (!on) stopAmbient();
    },
    setAmbient(on) { S.ambient = on; if (on && S.enabled) startAmbient(); else stopAmbient(); },
    setVolume(v) { S.volume = v; if (S.master) S.master.gain.setTargetAtTime(v, S.ctx.currentTime, 0.05); },
    get enabled() { return S.enabled; },
  };
})();
