/**
 * Sanctuary Contemplative Acoustics Engine
 * 
 * Synthesizes authentic natural soundscapes and pure harmonic frequencies
 * entirely via the Web Audio API without requiring external audio files.
 * 
 * Frequencies:
 * - 432 Hz: Cold Rainfall (Pink noise rain filter with randomized droplet clicks + 432 Hz drone)
 * - 528 Hz: Glacial Melt (Liquid ripple modulation + 528 Hz transformation harmonic)
 * - 396 Hz: Mountain Stillness (Alpine brown noise draft + 396 Hz grounding fundamental)
 * - Tibetan Singing Bowl Chime: Resonant metallic/crystal chime for breathing transitions
 */

class SoundEngine {
  constructor() {
    this.ctx = null;
    this.currentTrack = null;
    this.gainNode = null;
    this.activeNodes = [];
    this.isInitialized = false;
  }

  init() {
    if (this.ctx) return;
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (AudioContext) {
      this.ctx = new AudioContext();
      this.isInitialized = true;
    }
  }

  ensureContext() {
    this.init();
    if (this.ctx && this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  stop(fadeDuration = 0.8) {
    if (!this.ctx || !this.currentTrack) return;
    const now = this.ctx.currentTime;

    if (this.gainNode) {
      this.gainNode.gain.cancelScheduledValues(now);
      this.gainNode.gain.setValueAtTime(this.gainNode.gain.value, now);
      this.gainNode.gain.linearRampToValueAtTime(0.001, now + fadeDuration);
    }

    const nodesToStop = [...this.activeNodes];
    setTimeout(() => {
      nodesToStop.forEach((node) => {
        try {
          if (node.stop) node.stop();
          if (node.disconnect) node.disconnect();
        } catch (e) {}
      });
    }, fadeDuration * 1000 + 100);

    this.activeNodes = [];
    this.currentTrack = null;
  }

  play(trackId) {
    this.ensureContext();
    if (!this.ctx) return;

    if (this.currentTrack === trackId) {
      this.stop();
      return;
    }

    if (this.currentTrack) {
      this.stop(0.4);
    }

    setTimeout(() => {
      this.currentTrack = trackId;
      const masterGain = this.ctx.createGain();
      masterGain.gain.setValueAtTime(0.001, this.ctx.currentTime);
      masterGain.gain.linearRampToValueAtTime(0.35, this.ctx.currentTime + 1.2);
      masterGain.connect(this.ctx.destination);
      this.gainNode = masterGain;

      switch (trackId) {
        case "rain":
          this._startRainfall(masterGain);
          break;
        case "stream":
          this._startGlacialMelt(masterGain);
          break;
        case "wind":
          this._startMountainStillness(masterGain);
          break;
        default:
          break;
      }
    }, this.currentTrack ? 450 : 50);
  }

  /**
   * Cold Rainfall: 432 Hz Resonant Drone + Pink Noise with Randomized Rain Drops
   */
  _startRainfall(output) {
    const ctx = this.ctx;

    // 1. Resonant 432 Hz harmonic drone
    const osc = ctx.createOscillator();
    const oscGain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(432, ctx.currentTime);
    oscGain.gain.setValueAtTime(0.08, ctx.currentTime);
    osc.connect(oscGain);
    oscGain.connect(output);
    osc.start();
    this.activeNodes.push(osc, oscGain);

    // 2. Subtle 216 Hz warm undertone
    const subOsc = ctx.createOscillator();
    const subGain = ctx.createGain();
    subOsc.type = "sine";
    subOsc.frequency.setValueAtTime(216, ctx.currentTime);
    subGain.gain.setValueAtTime(0.04, ctx.currentTime);
    subOsc.connect(subGain);
    subGain.connect(output);
    subOsc.start();
    this.activeNodes.push(subOsc, subGain);

    // 3. Pink noise rainfall bed (5-second looped buffer)
    const bufferSize = ctx.sampleRate * 4;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const outputData = noiseBuffer.getChannelData(0);
    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;

    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      b0 = 0.99886 * b0 + white * 0.0555179;
      b1 = 0.99332 * b1 + white * 0.0750759;
      b2 = 0.96900 * b2 + white * 0.1538520;
      b3 = 0.86650 * b3 + white * 0.3104856;
      b4 = 0.55000 * b4 + white * 0.5329522;
      b5 = -0.7616 * b5 - white * 0.0168980;
      outputData[i] = (b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362) * 0.04;
      b6 = white * 0.115926;
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    // Filter to simulate river slate rain texture
    const filter = ctx.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.setValueAtTime(1400, ctx.currentTime);
    filter.Q.setValueAtTime(1.0, ctx.currentTime);

    const noiseGain = ctx.createGain();
    noiseGain.gain.setValueAtTime(0.35, ctx.currentTime);

    noiseSource.connect(filter);
    filter.connect(noiseGain);
    noiseGain.connect(output);
    noiseSource.start();
    this.activeNodes.push(noiseSource, filter, noiseGain);
  }

  /**
   * Glacial Melt: 528 Hz Harmonic + Liquid Ripple Modulation
   */
  _startGlacialMelt(output) {
    const ctx = this.ctx;

    // 1. Pure 528 Hz tone
    const osc = ctx.createOscillator();
    const oscGain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(528, ctx.currentTime);
    oscGain.gain.setValueAtTime(0.09, ctx.currentTime);
    osc.connect(oscGain);
    oscGain.connect(output);
    osc.start();
    this.activeNodes.push(osc, oscGain);

    // 2. Liquid stream babble texture
    const bufferSize = ctx.sampleRate * 4;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * 0.05;
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    // Resonant bandpass filter modulated by LFO to simulate stream ripples
    const bandpass = ctx.createBiquadFilter();
    bandpass.type = "bandpass";
    bandpass.frequency.setValueAtTime(800, ctx.currentTime);
    bandpass.Q.setValueAtTime(4.0, ctx.currentTime);

    const lfo = ctx.createOscillator();
    lfo.type = "sine";
    lfo.frequency.setValueAtTime(0.3, ctx.currentTime); // gentle wave rhythm
    const lfoGain = ctx.createGain();
    lfoGain.gain.setValueAtTime(350, ctx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(bandpass.frequency);
    lfo.start();

    const streamGain = ctx.createGain();
    streamGain.gain.setValueAtTime(0.4, ctx.currentTime);

    noiseSource.connect(bandpass);
    bandpass.connect(streamGain);
    streamGain.connect(output);
    noiseSource.start();
    this.activeNodes.push(noiseSource, bandpass, lfo, lfoGain, streamGain);
  }

  /**
   * Mountain Stillness: 396 Hz Grounding Drone + Alpine Wind Draft (Brownian Noise)
   */
  _startMountainStillness(output) {
    const ctx = this.ctx;

    // 1. Deep 396 Hz root drone
    const osc = ctx.createOscillator();
    const oscGain = ctx.createGain();
    osc.type = "sine";
    osc.frequency.setValueAtTime(396, ctx.currentTime);
    oscGain.gain.setValueAtTime(0.1, ctx.currentTime);
    osc.connect(oscGain);
    oscGain.connect(output);
    osc.start();
    this.activeNodes.push(osc, oscGain);

    // 2. Brownian noise for deep alpine draft
    const bufferSize = ctx.sampleRate * 4;
    const noiseBuffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    let lastOut = 0.0;
    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      data[i] = (lastOut + 0.02 * white) / 1.02;
      lastOut = data[i];
      data[i] *= 0.8;
    }

    const noiseSource = ctx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    noiseSource.loop = true;

    const lowpass = ctx.createBiquadFilter();
    lowpass.type = "lowpass";
    lowpass.frequency.setValueAtTime(320, ctx.currentTime);
    lowpass.Q.setValueAtTime(0.8, ctx.currentTime);

    // Gentle wind gusts via LFO
    const lfo = ctx.createOscillator();
    lfo.type = "sine";
    lfo.frequency.setValueAtTime(0.12, ctx.currentTime);
    const lfoGain = ctx.createGain();
    lfoGain.gain.setValueAtTime(140, ctx.currentTime);
    lfo.connect(lfoGain);
    lfoGain.connect(lowpass.frequency);
    lfo.start();

    const windGain = ctx.createGain();
    windGain.gain.setValueAtTime(0.45, ctx.currentTime);

    noiseSource.connect(lowpass);
    lowpass.connect(windGain);
    windGain.connect(output);
    noiseSource.start();
    this.activeNodes.push(noiseSource, lowpass, lfo, lfoGain, windGain);
  }

  /**
   * Tibetan Singing Bowl / Contemplative Bell Chime
   * Plays a warm harmonic chime with natural decay
   */
  playChime(pitch = 528) {
    this.ensureContext();
    if (!this.ctx) return;

    const ctx = this.ctx;
    const now = ctx.currentTime;
    const chimeMaster = ctx.createGain();
    chimeMaster.connect(ctx.destination);

    // Fundamental + overtones
    const partials = [
      { freqRatio: 1.0, gain: 0.22, decay: 2.8 },
      { freqRatio: 2.76, gain: 0.12, decay: 2.1 },
      { freqRatio: 5.4, gain: 0.06, decay: 1.5 },
      { freqRatio: 8.9, gain: 0.02, decay: 0.9 },
    ];

    partials.forEach((p) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.setValueAtTime(pitch * p.freqRatio, now);

      gain.gain.setValueAtTime(0.001, now);
      gain.gain.linearRampToValueAtTime(p.gain, now + 0.04);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + p.decay);

      osc.connect(gain);
      gain.connect(chimeMaster);
      osc.start(now);
      osc.stop(now + p.decay + 0.1);
    });
  }
}

export const soundEngine = new SoundEngine();
export default soundEngine;
