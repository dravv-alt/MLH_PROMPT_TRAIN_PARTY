import React, { useRef, useEffect, useState } from "react";
import * as THREE from "three";
import soundEngine from "../services/soundEngine";

/**
 * Procedural texture generator for Sanctuary's official Pebble mascot.
 * Renders riverstone granite base with micro-stippling flecks and
 * the signature diagonal quartz mineral vein.
 */
let cachedTextures = null;
function getPebbleTextures() {
  if (cachedTextures) return cachedTextures;

  const width = 1024;
  const height = 1024;

  const colorCanvas = document.createElement("canvas");
  colorCanvas.width = width;
  colorCanvas.height = height;
  const ctx = colorCanvas.getContext("2d");

  // Base stone gradient: weathered riverbed limestone to sunlit warm crown
  const grad = ctx.createLinearGradient(0, height, 0, 0);
  grad.addColorStop(0.0, "#BAAF9F");
  grad.addColorStop(0.4, "#CBC1B2");
  grad.addColorStop(0.85, "#DDD4C6");
  grad.addColorStop(1.0, "#E6DFC8");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  // Micro-stippling mineral flecks
  const rng = (seed) => {
    let s = seed % 2147483647;
    return () => (s = (s * 16807) % 2147483647) / 2147483647;
  };
  const rand = rng(42);

  ctx.fillStyle = "rgba(75, 65, 55, 0.12)";
  for (let i = 0; i < 14000; i++) {
    const x = rand() * width;
    const y = rand() * height;
    const r = rand() * 1.6 + 0.5;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  ctx.fillStyle = "rgba(255, 252, 245, 0.22)";
  for (let i = 0; i < 10000; i++) {
    const x = rand() * width;
    const y = rand() * height;
    const r = rand() * 1.4 + 0.4;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  // Signature Diagonal Quartz Vein
  const drawVein = (glowCtx, isBump = false) => {
    glowCtx.save();
    glowCtx.lineCap = "round";
    glowCtx.lineJoin = "round";

    const points = [
      { x: 140, y: 220 },
      { x: 260, y: 320 },
      { x: 380, y: 440 },
      { x: 490, y: 530 },
      { x: 620, y: 620 },
      { x: 740, y: 710 },
      { x: 880, y: 800 },
    ];
    const branch = [
      { x: 620, y: 620 },
      { x: 690, y: 740 },
      { x: 730, y: 820 },
    ];

    // Translucent quartz halo
    glowCtx.strokeStyle = isBump ? "rgba(255, 255, 255, 0.4)" : "rgba(255, 248, 235, 0.45)";
    glowCtx.lineWidth = 26;
    glowCtx.beginPath();
    points.forEach((p, idx) => {
      const jx = p.x + (rand() - 0.5) * 8;
      const jy = p.y + (rand() - 0.5) * 8;
      if (idx === 0) glowCtx.moveTo(jx, jy);
      else glowCtx.lineTo(jx, jy);
    });
    glowCtx.stroke();

    // Solid ivory crystalline vein core
    glowCtx.strokeStyle = isBump ? "rgba(255, 255, 255, 0.9)" : "rgba(255, 252, 240, 0.88)";
    glowCtx.lineWidth = 10;
    glowCtx.beginPath();
    points.forEach((p, idx) => {
      const jx = p.x + (rand() - 0.5) * 5;
      const jy = p.y + (rand() - 0.5) * 5;
      if (idx === 0) glowCtx.moveTo(jx, jy);
      else glowCtx.lineTo(jx, jy);
    });
    glowCtx.stroke();

    // Secondary vein branch
    glowCtx.lineWidth = 6;
    glowCtx.beginPath();
    branch.forEach((p, idx) => {
      const jx = p.x + (rand() - 0.5) * 4;
      const jy = p.y + (rand() - 0.5) * 4;
      if (idx === 0) glowCtx.moveTo(jx, jy);
      else glowCtx.lineTo(jx, jy);
    });
    glowCtx.stroke();

    // Core hairline
    glowCtx.strokeStyle = "#ffffff";
    glowCtx.lineWidth = 3;
    glowCtx.beginPath();
    points.forEach((p, idx) => {
      if (idx === 0) glowCtx.moveTo(p.x, p.y);
      else glowCtx.lineTo(p.x, p.y);
    });
    glowCtx.stroke();

    glowCtx.restore();
  };

  drawVein(ctx, false);

  const bumpCanvas = document.createElement("canvas");
  bumpCanvas.width = 512;
  bumpCanvas.height = 512;
  const bCtx = bumpCanvas.getContext("2d");
  bCtx.fillStyle = "#808080";
  bCtx.fillRect(0, 0, 512, 512);
  bCtx.scale(0.5, 0.5);
  drawVein(bCtx, true);

  const diffuseTexture = new THREE.CanvasTexture(colorCanvas);
  diffuseTexture.wrapS = THREE.RepeatWrapping;
  diffuseTexture.wrapT = THREE.ClampToEdgeWrapping;

  const bumpTexture = new THREE.CanvasTexture(bumpCanvas);
  bumpTexture.wrapS = THREE.RepeatWrapping;
  bumpTexture.wrapT = THREE.ClampToEdgeWrapping;

  cachedTextures = { diffuseTexture, bumpTexture };
  return cachedTextures;
}

/**
 * Creates the organic river pebble body geometry.
 */
function createRiverPebbleGeometry() {
  const geom = new THREE.SphereGeometry(1.0, 48, 48);
  const pos = geom.attributes.position;

  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);

    const normY = (y + 1) * 0.5;
    const taper = 1.08 - 0.32 * Math.pow(normY, 1.3);
    x *= taper;
    z *= taper * 0.86;

    const lean = Math.sin(normY * Math.PI) * 0.08;
    x += lean;

    if (y < -0.55) {
      const bottomFlatten = (-0.55 - y) / 0.45;
      y += bottomFlatten * 0.12;
      x *= 1.0 + bottomFlatten * 0.08;
      z *= 1.0 + bottomFlatten * 0.08;
    }

    const erosion = Math.sin(x * 3.2 + y * 2.5) * 0.02 + Math.cos(z * 3.8 + y * 2.2) * 0.015;
    x += erosion * x;
    y += erosion * 0.6;
    z += erosion * z;

    x *= 1.1;
    y *= 1.32;
    z *= 0.96;

    pos.setXYZ(i, x, y, z);
  }

  geom.computeVertexNormals();
  return geom;
}

/**
 * Creates tapered arm geometry.
 */
function createArmGeometry() {
  const geom = new THREE.CapsuleGeometry(0.18, 0.45, 16, 16);
  const pos = geom.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);
    const tipFactor = (y + 0.4) * 0.6;
    x *= 1.0 - tipFactor * 0.2;
    z *= 1.0 - tipFactor * 0.2;
    pos.setXYZ(i, x, y, z);
  }
  geom.computeVertexNormals();
  return geom;
}

/**
 * Creates 3-leaf sprout on crown.
 */
function createSproutGroup() {
  const sprout = new THREE.Group();
  const stemCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0.04, 0.18, 0.01),
    new THREE.Vector3(0.08, 0.36, -0.02),
  ]);
  const stemGeom = new THREE.TubeGeometry(stemCurve, 12, 0.022, 8, false);
  const stemMat = new THREE.MeshStandardMaterial({ color: 0x637048, roughness: 0.6 });
  const stemMesh = new THREE.Mesh(stemGeom, stemMat);
  sprout.add(stemMesh);

  const createLeaf = (scale = 1.0, rot = [0, 0, 0], pos = [0, 0, 0]) => {
    const leafGeom = new THREE.SphereGeometry(0.14, 12, 12);
    leafGeom.scale(0.48 * scale, 1.2 * scale, 0.08 * scale);
    const leafMat = new THREE.MeshStandardMaterial({
      color: 0x7a8a5b,
      roughness: 0.5,
      side: THREE.DoubleSide,
    });
    const leafMesh = new THREE.Mesh(leafGeom, leafMat);
    leafMesh.position.set(...pos);
    leafMesh.rotation.set(...rot);
    return leafMesh;
  };

  sprout.add(createLeaf(1.15, [0.3, 0.1, -0.3], [0.08, 0.36, -0.02]));
  sprout.add(createLeaf(0.95, [0.1, 0.4, 0.6], [0.13, 0.31, 0.04]));
  sprout.add(createLeaf(0.85, [-0.4, -0.2, -0.5], [0.02, 0.28, -0.06]));

  return sprout;
}

/**
 * PebblePet3D — Freely Roaming 3D Companion for Sanctuary Chat
 * 
 * - Unboxed: Renders directly onto the chat dock ledge.
 * - Freely roams and hops back and forth along the full runway width.
 * - Click anywhere along the ledge: Pebble hops to that location.
 * - Tap/poke on Pebble: Spring squash bounce and friendly greeting emote.
 * - Attentive when typing: stops wandering, turns toward composer, eyes track cursor.
 * - Thinking: Thoughtful head tilt and reflective presence.
 * - Speaking: Explanatory gentle gestures in resonance.
 * - Nap: Closed eyelids and slow peaceful breath during inactivity.
 */
export default function PebblePet3D({
  lifecycleState = "idle",
  isTyping = false,
  emotionalState = "neutral",
  keystrokeTrigger = 0,
  statusText = "",
  className = "",
  style = {},
}) {
  const mountRef = useRef(null);
  const [activeEmote, setActiveEmote] = useState(null);
  const [emotePos, setEmotePos] = useState(50);

  const isTypingRef = useRef(isTyping);
  useEffect(() => {
    isTypingRef.current = isTyping;
  }, [isTyping]);

  const lifecycleRef = useRef(lifecycleState);
  useEffect(() => {
    lifecycleRef.current = lifecycleState;
  }, [lifecycleState]);

  // Persistent pet state across animation frames
  const petRef = useRef({
    x: 0,
    targetX: 0,
    baseY: -0.14,
    hopProgress: 0,
    isHopping: false,
    hopSpeed: 4.8,
    hopHeight: 0.52,
    hopDistance: 0.65,
    facingDir: 1,
    facingRotY: 0,
    targetRotY: 0,
    maxRoamingX: 3.2,

    // State Machine
    state: "IDLE", // IDLE, HOPPING, ATTENTIVE, THINKING, SPEAKING, AWAITING, UNBURDEN, SAVED, NAP, EMPATHY, EPIPHANY, CURIOUS, GROUNDING, CELEBRATING
    stateTimer: 2.5,
    idleLookTilt: 0,

    // Emotional Cadence & Interactive extensions
    emotionalState: "neutral",
    keystrokeBob: 0,
    isPetting: false,
    pettingIntensity: 0,

    // Physics & breathing
    bounceVelocity: 0,
    bounceScaleY: 1.0,
    blinkTimer: 3.0,
    isBlinking: false,
    isNapping: false,
    napCounter: 0,

    // Pointer
    mouseNorm: { x: 0, y: 0 },
    containerBounds: { width: 640, height: 76 },
  });

  // React to semantic emotional cadence updates
  const emotionalRef = useRef(emotionalState);
  useEffect(() => {
    emotionalRef.current = emotionalState;
    const pet = petRef.current;
    if (!pet) return;

    pet.napCounter = 0;
    pet.isNapping = false;

    if (emotionalState === "empathy") {
      pet.state = "EMPATHY";
      pet.stateTimer = 5.0;
    } else if (emotionalState === "epiphany") {
      pet.state = "EPIPHANY";
      pet.stateTimer = 4.5;
      pet.bounceVelocity = 0.35;
    } else if (emotionalState === "curious") {
      pet.state = "CURIOUS";
      pet.stateTimer = 4.0;
    } else if (emotionalState === "grounding") {
      pet.state = "GROUNDING";
      pet.stateTimer = 5.0;
    } else if (emotionalState === "celebrating") {
      pet.state = "CELEBRATING";
      pet.stateTimer = 4.5;
      pet.bounceVelocity = 0.42;
    }
  }, [emotionalState]);

  // Keystroke bob micro-animation
  useEffect(() => {
    if (keystrokeTrigger > 0 && petRef.current) {
      petRef.current.keystrokeBob = 0.08;
      petRef.current.isNapping = false;
      petRef.current.napCounter = 0;
      if (petRef.current.state === "IDLE" || petRef.current.state === "NAP") {
        petRef.current.state = "ATTENTIVE";
      }
    }
  }, [keystrokeTrigger]);

  // React to lifecycle changes
  useEffect(() => {
    const pet = petRef.current;
    pet.napCounter = 0;
    pet.isNapping = false;

    if (lifecycleState === "celebrating") {
      pet.state = "CELEBRATING";
      pet.stateTimer = 4.5;
      pet.bounceVelocity = 0.42;
    } else if (lifecycleState === "empathy") {
      pet.state = "EMPATHY";
      pet.stateTimer = 5.0;
    } else if (lifecycleState === "epiphany") {
      pet.state = "EPIPHANY";
      pet.stateTimer = 4.5;
      pet.bounceVelocity = 0.35;
    } else if (lifecycleState === "curious") {
      pet.state = "CURIOUS";
      pet.stateTimer = 4.0;
    } else if (lifecycleState === "grounding") {
      pet.state = "GROUNDING";
      pet.stateTimer = 5.0;
    } else if (lifecycleState === "thinking") {
      pet.state = "THINKING";
      pet.stateTimer = 4.0;
      pet.targetRotY = 0.22;
      pet.idleLookTilt = 0.15;
    } else if (lifecycleState === "speaking") {
      pet.state = "SPEAKING";
      pet.stateTimer = 6.0;
      pet.targetRotY = -0.15;
    } else if (lifecycleState === "awaiting_followup") {
      pet.state = "AWAITING";
      pet.stateTimer = 4.0;
      pet.targetRotY = 0;
      pet.idleLookTilt = 0;
    } else if (lifecycleState === "unburden") {
      pet.state = "UNBURDEN";
      pet.stateTimer = 4.0;
      pet.bounceVelocity = 0.3;
    } else if (lifecycleState === "saved") {
      pet.state = "SAVED";
      pet.stateTimer = 3.5;
      pet.bounceVelocity = 0.22;
    } else if (lifecycleState === "attentive" || isTyping) {
      pet.state = "ATTENTIVE";
      pet.targetRotY = 0;
    } else if (lifecycleState === "nap") {
      pet.state = "NAP";
      pet.isNapping = true;
    } else {
      pet.state = "IDLE";
      pet.targetRotY = 0;
      pet.idleLookTilt = 0;
    }
  }, [lifecycleState]);

  // When user is typing, be attentive
  useEffect(() => {
    if (isTyping && lifecycleRef.current !== "thinking" && lifecycleRef.current !== "speaking") {
      petRef.current.state = "ATTENTIVE";
      petRef.current.isNapping = false;
      petRef.current.napCounter = 0;
      petRef.current.targetRotY = 0;
    }
  }, [isTyping]);

  const triggerEmote = (emoji) => {
    const pet = petRef.current;
    const roam = pet?.maxRoamingX || 2.5;
    const pct = Math.max(12, Math.min(88, ((pet.x / roam) * 0.5 + 0.5) * 100));
    setEmotePos(pct);
    setActiveEmote(emoji);
    setTimeout(() => {
      setActiveEmote(null);
    }, 1600);
  };

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const width = Math.max(200, Math.round(rect.width || container.clientWidth || 640));
    const height = Math.max(50, Math.round(rect.height || container.clientHeight || 76));
    petRef.current.containerBounds = { width, height };

    // 1. Scene & Camera setup for wide landscape unboxed runway
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(30, width / height, 0.1, 50);
    camera.position.set(0, 0.18, 4.4);
    camera.lookAt(0, 0, 0);

    // 2. WebGL Renderer with alpha transparency
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch (e) {
      console.warn("WebGL renderer init failed:", e);
      return;
    }

    renderer.domElement.style.width = "100%";
    renderer.domElement.style.height = "100%";
    renderer.domElement.style.display = "block";
    renderer.setSize(width, height, false);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    container.innerHTML = "";
    container.appendChild(renderer.domElement);

    // 3. Lighting Rig (Soft, restrained studio light)
    const ambientLight = new THREE.AmbientLight(0xfffaed, 1.4);
    scene.add(ambientLight);

    const keyLight = new THREE.DirectionalLight(0xfff6ea, 1.5);
    keyLight.position.set(3.0, 4.0, 2.5);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0xe4ece6, 0.7);
    fillLight.position.set(-3.0, 2.0, 1.5);
    scene.add(fillLight);

    const rimLight = new THREE.DirectionalLight(0xdbe7dc, 0.5);
    rimLight.position.set(0, 2.5, -2.5);
    scene.add(rimLight);

    // 4. Pet Master Rig
    const petMaster = new THREE.Group();
    petMaster.scale.set(0.46, 0.46, 0.46);
    petMaster.position.set(0, petRef.current.baseY, 0);
    scene.add(petMaster);

    // Dynamic ground shadow disc
    const shadowCanvas = document.createElement("canvas");
    shadowCanvas.width = 128;
    shadowCanvas.height = 128;
    const sCtx = shadowCanvas.getContext("2d");
    const shadowGrad = sCtx.createRadialGradient(64, 64, 0, 64, 64, 60);
    shadowGrad.addColorStop(0, "rgba(23, 52, 41, 0.28)");
    shadowGrad.addColorStop(0.5, "rgba(46, 75, 63, 0.12)");
    shadowGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
    sCtx.fillStyle = shadowGrad;
    sCtx.fillRect(0, 0, 128, 128);

    const shadowTex = new THREE.CanvasTexture(shadowCanvas);
    const shadowMat = new THREE.MeshBasicMaterial({
      map: shadowTex,
      transparent: true,
      opacity: 0.3,
      depthWrite: false,
    });
    const shadowMesh = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 1.1), shadowMat);
    shadowMesh.rotation.x = -Math.PI / 2;
    shadowMesh.position.y = petRef.current.baseY - 0.44;
    petMaster.add(shadowMesh);

    // 5. Build Volumetric Mesh Anatomy
    const { diffuseTexture, bumpTexture } = getPebbleTextures();
    const pebbleMaterial = new THREE.MeshStandardMaterial({
      map: diffuseTexture,
      bumpMap: bumpTexture,
      bumpScale: 0.025,
      roughness: 0.88,
      metalness: 0.02,
    });

    const bodyGroup = new THREE.Group();
    const pebbleGeometry = createRiverPebbleGeometry();
    const pebbleMesh = new THREE.Mesh(pebbleGeometry, pebbleMaterial);
    pebbleMesh.castShadow = true;
    pebbleMesh.receiveShadow = true;
    bodyGroup.add(pebbleMesh);
    petMaster.add(bodyGroup);

    // Eyes
    const eyeGeometry = new THREE.SphereGeometry(0.09, 16, 16);
    const eyeMaterial = new THREE.MeshStandardMaterial({
      color: 0x141414,
      roughness: 0.1,
      metalness: 0.9,
    });

    const leftEyeGroup = new THREE.Group();
    leftEyeGroup.position.set(-0.31, 0.18, 0.86);
    const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEyeGroup.add(leftEye);

    const glintGeom = new THREE.SphereGeometry(0.026, 8, 8);
    const glintMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const leftGlint = new THREE.Mesh(glintGeom, glintMat);
    leftGlint.position.set(-0.026, 0.026, 0.075);
    leftEyeGroup.add(leftGlint);

    const rightEyeGroup = new THREE.Group();
    rightEyeGroup.position.set(0.35, 0.13, 0.84);
    const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEyeGroup.add(rightEye);

    const rightGlint = new THREE.Mesh(glintGeom, glintMat);
    rightGlint.position.set(-0.026, 0.026, 0.075);
    rightEyeGroup.add(rightGlint);

    bodyGroup.add(leftEyeGroup);
    bodyGroup.add(rightEyeGroup);

    // Serene Closed Eyelids for napping
    const closedEyeCurve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(-0.08, 0, 0),
      new THREE.Vector3(0, -0.05, 0),
      new THREE.Vector3(0.08, 0, 0)
    );
    const closedEyeGeom = new THREE.TubeGeometry(closedEyeCurve, 12, 0.016, 6, false);
    const closedEyeMat = new THREE.MeshStandardMaterial({ color: 0x2d2924, roughness: 0.8 });
    const leftClosed = new THREE.Mesh(closedEyeGeom, closedEyeMat);
    leftClosed.position.set(-0.31, 0.18, 0.88);
    leftClosed.visible = false;
    bodyGroup.add(leftClosed);

    const rightClosed = new THREE.Mesh(closedEyeGeom, closedEyeMat);
    rightClosed.position.set(0.35, 0.13, 0.86);
    rightClosed.visible = false;
    bodyGroup.add(rightClosed);

    // Minimal curved smile
    const smileCurve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(-0.10, 0.015, 0),
      new THREE.Vector3(0.0, -0.035, 0),
      new THREE.Vector3(0.10, 0.01, 0)
    );
    const smileGeom = new THREE.TubeGeometry(smileCurve, 16, 0.015, 6, false);
    const smileMat = new THREE.MeshStandardMaterial({ color: 0x483f36, roughness: 0.85 });
    const smileMesh = new THREE.Mesh(smileGeom, smileMat);
    smileMesh.position.set(0.02, 0.04, 0.92);
    bodyGroup.add(smileMesh);

    // Cheeks
    const blushGeom = new THREE.CircleGeometry(0.08, 16);
    const blushMat = new THREE.MeshBasicMaterial({
      color: 0xd99b8b,
      transparent: true,
      opacity: 0.22,
      depthWrite: false,
    });
    const leftBlush = new THREE.Mesh(blushGeom, blushMat);
    leftBlush.position.set(-0.46, 0.07, 0.8);
    leftBlush.rotation.set(-0.1, -0.4, 0);
    bodyGroup.add(leftBlush);

    const rightBlush = new THREE.Mesh(blushGeom, blushMat);
    rightBlush.position.set(0.48, 0.03, 0.77);
    rightBlush.rotation.set(-0.1, 0.4, 0);
    bodyGroup.add(rightBlush);

    // Arms
    const leftArmPivot = new THREE.Group();
    leftArmPivot.position.set(-0.92, -0.12, 0.08);
    const armGeom = createArmGeometry();
    const leftArmMesh = new THREE.Mesh(armGeom, pebbleMaterial);
    leftArmMesh.position.set(-0.15, -0.15, 0);
    leftArmMesh.rotation.set(0, 0, 0.7);
    leftArmPivot.add(leftArmMesh);
    bodyGroup.add(leftArmPivot);

    const rightArmPivot = new THREE.Group();
    rightArmPivot.position.set(0.96, -0.16, 0.08);
    const rightArmMesh = new THREE.Mesh(armGeom, pebbleMaterial);
    rightArmMesh.position.set(0.15, -0.15, 0);
    rightArmMesh.rotation.set(0, 0, -0.7);
    rightArmPivot.add(rightArmMesh);
    bodyGroup.add(rightArmPivot);

    // Top Leaf Sprout
    const sproutPivot = new THREE.Group();
    sproutPivot.position.set(0.34, 1.28, -0.04);
    sproutPivot.add(createSproutGroup());
    bodyGroup.add(sproutPivot);

    // Pointer Raycasting (Gentle poke or call-over hop)
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    const handlePointerMove = (e) => {
      const b = container.getBoundingClientRect();
      const normX = ((e.clientX - b.left) / b.width) * 2 - 1;
      const normY = -(((e.clientY - b.top) / b.height) * 2 - 1);
      petRef.current.mouseNorm = { x: normX, y: normY };

      mouse.x = normX;
      mouse.y = normY;
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObject(pebbleMesh, true);
      petRef.current.isPetting = intersects.length > 0;
    };

    const handleGlobalPointer = (e) => {
      const normX = (e.clientX / window.innerWidth) * 2 - 1;
      const normY = -(e.clientY / window.innerHeight) * 2 + 1;
      // Soft influence from across the screen
      petRef.current.globalMouse = { x: normX, y: normY };
    };
    window.addEventListener("pointermove", handleGlobalPointer);

    const handlePetClick = (e) => {
      const b = container.getBoundingClientRect();
      mouse.x = ((e.clientX - b.left) / b.width) * 2 - 1;
      mouse.y = -(((e.clientY - b.top) / b.height) * 2 - 1);
      raycaster.setFromCamera(mouse, camera);

      const intersects = raycaster.intersectObject(pebbleMesh, true);
      if (intersects.length > 0) {
        // Poked/Pet! Gentle spring bounce and mineral acoustic chime
        petRef.current.bounceVelocity = 0.44;
        petRef.current.isNapping = false;
        petRef.current.napCounter = 0;
        petRef.current.state = "EPIPHANY";
        petRef.current.stateTimer = 2.2;
        try {
          soundEngine.playChime(660);
        } catch (err) {}
      } else {
        // Clicked along the runway: call Pebble over to this position!
        const rawNormX = ((e.clientX - b.left) / b.width) * 2 - 1;
        const normClickX = Math.max(-1, Math.min(1, rawNormX));
        const clickedX = normClickX * petRef.current.maxRoamingX;
        petRef.current.isNapping = false;
        petRef.current.napCounter = 0;
        petRef.current.state = "HOPPING";
        petRef.current.targetX = Math.max(-petRef.current.maxRoamingX, Math.min(petRef.current.maxRoamingX, clickedX));
        petRef.current.facingDir = petRef.current.targetX >= petRef.current.x ? 1 : -1;
        petRef.current.targetRotY = petRef.current.facingDir === 1 ? 0.25 : -0.25;
        petRef.current.hopProgress = 0;
        petRef.current.hopsRemainingInBurst = Math.max(1, Math.min(4, Math.round(Math.abs(petRef.current.targetX - petRef.current.x) * 1.5)));
      }
    };

    container.addEventListener("pointermove", handlePointerMove);
    container.addEventListener("click", handlePetClick);

    // Roaming bounds calculator based on visible viewport width
    const updateRoamingBounds = () => {
      const vFOV = (camera.fov * Math.PI) / 180;
      const visibleHeight = 2 * Math.tan(vFOV / 2) * Math.abs(camera.position.z);
      const visibleWidth = visibleHeight * camera.aspect;
      petRef.current.maxRoamingX = Math.max(2.2, Math.min(4.0, (visibleWidth / 2) - 0.5));
    };
    updateRoamingBounds();

    // Resizer
    const handleResize = () => {
      if (!container) return;
      const b = container.getBoundingClientRect();
      const newW = Math.max(200, Math.round(b.width || container.clientWidth));
      const newH = Math.max(50, Math.round(b.height || container.clientHeight));
      petRef.current.containerBounds = { width: newW, height: newH };
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH, false);
      updateRoamingBounds();
    };

    let resizeObserver = null;
    if (typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(() => handleResize());
      resizeObserver.observe(container);
    }
    window.addEventListener("resize", handleResize);

    // 8. Animation Loop
    let animId;
    const clock = new THREE.Clock();

    const petLoop = () => {
      animId = requestAnimationFrame(petLoop);
      const rawDelta = clock.getDelta();
      const delta = Math.min(Math.max(rawDelta, 0.0001), 0.05);
      const time = clock.getElapsedTime();
      const pet = petRef.current;

      // Always synchronize master horizontal position
      petMaster.position.x = pet.x;

      // Organic subtle breathing
      const naturalBreath = Math.sin(time * 1.8) * 0.02;

      // State handling
      if (pet.state === "IDLE") {
        pet.napCounter += delta;
        // Inactivity nap after 60 seconds
        if (pet.napCounter > 60.0 && !isTypingRef.current) {
          pet.state = "NAP";
          pet.isNapping = true;
          pet.stateTimer = 8.0;
        } else {
          petMaster.position.y = pet.baseY + naturalBreath;
          bodyGroup.rotation.x = 0;
          bodyGroup.rotation.z = pet.idleLookTilt;
          leftArmPivot.rotation.z = 0.35 + naturalBreath;
          rightArmPivot.rotation.z = -0.35 - naturalBreath;
          sproutPivot.rotation.z = Math.sin(time * 1.5) * 0.05;

          // Free roaming hops along the wide ledge on top of chatbox
          pet.stateTimer -= delta;
          if (pet.stateTimer <= 0) {
            pet.stateTimer = 1.2 + Math.random() * 1.8;
            if (Math.random() < 0.82) {
              pet.state = "HOPPING";
              const targetX = (Math.random() * 2 - 1) * pet.maxRoamingX; // freely roams across top of chatbox!
              pet.targetX = targetX;
              pet.facingDir = targetX >= pet.x ? 1 : -1;
              pet.targetRotY = pet.facingDir === 1 ? 0.25 : -0.25;
              pet.hopProgress = 0;
              pet.hopsRemainingInBurst = Math.floor(Math.random() * 3) + 1;
            } else {
              pet.idleLookTilt = (Math.random() - 0.5) * 0.25;
            }
          }
        }
      } else if (pet.state === "HOPPING") {
        pet.napCounter = 0;
        pet.isNapping = false;
        pet.hopProgress += delta * pet.hopSpeed;

        if (pet.hopProgress < Math.PI) {
          const hopArc = Math.sin(pet.hopProgress);
          petMaster.position.y = pet.baseY + hopArc * pet.hopHeight;
          const hopStep = (pet.facingDir * pet.hopDistance * delta * pet.hopSpeed) / Math.PI;
          pet.x = Math.max(-pet.maxRoamingX, Math.min(pet.maxRoamingX, pet.x + hopStep));
          petMaster.position.x = pet.x;

          const stretch = Math.sin(pet.hopProgress * 2);
          bodyGroup.scale.set(1.0 - stretch * 0.1, 1.0 + stretch * 0.14, 1.0 - stretch * 0.1);
          leftArmPivot.rotation.z = 0.45 + hopArc * 0.25;
          rightArmPivot.rotation.z = -0.45 - hopArc * 0.25;
          sproutPivot.rotation.z = -pet.facingDir * hopArc * 0.2;
        } else {
          petMaster.position.y = pet.baseY;
          bodyGroup.scale.set(1.08, 0.92, 1.08); // soft landing squash
          pet.bounceVelocity = 0.18;
          pet.hopProgress = 0;
          pet.hopsRemainingInBurst -= 1;

          if (pet.hopsRemainingInBurst <= 0 || Math.abs(pet.x) >= pet.maxRoamingX) {
            pet.state = "IDLE";
            pet.stateTimer = 3.0 + Math.random() * 2.0;
            pet.targetRotY = 0;
          }
        }
      } else if (pet.state === "ATTENTIVE") {
        // Listening / Typing
        pet.napCounter = 0;
        pet.isNapping = false;
        pet.targetRotY = 0;
        petMaster.position.y = pet.baseY + Math.sin(time * 2.2) * 0.015;
        bodyGroup.rotation.x = -0.12; // tilt forward attentively
        bodyGroup.rotation.z = 0;
        leftArmPivot.rotation.z = 0.32;
        rightArmPivot.rotation.z = -0.32;
        sproutPivot.rotation.z = Math.sin(time * 2.5) * 0.04;

        if (!isTypingRef.current && lifecycleRef.current !== "attentive") {
          pet.state = "IDLE";
          pet.stateTimer = 2.0;
          bodyGroup.rotation.x = 0;
        }
      } else if (pet.state === "THINKING") {
        // Thoughtful contemplative posture
        pet.napCounter = 0;
        pet.isNapping = false;
        pet.targetRotY = 0.25;
        petMaster.position.y = pet.baseY + Math.sin(time * 1.4) * 0.015;
        bodyGroup.rotation.x = -0.05;
        bodyGroup.rotation.z = 0.12;
        leftArmPivot.rotation.z = 0.55;
        rightArmPivot.rotation.z = -0.3;
        sproutPivot.rotation.z = Math.sin(time * 1.8) * 0.06;
      } else if (pet.state === "SPEAKING") {
        // Explaining gesture in sync with streaming response
        pet.napCounter = 0;
        pet.isNapping = false;
        pet.targetRotY = -0.15;
        petMaster.position.y = pet.baseY + Math.sin(time * 2.5) * 0.02;
        bodyGroup.rotation.x = Math.sin(time * 3.0) * 0.04;
        bodyGroup.rotation.z = 0;
        rightArmPivot.rotation.z = -0.45 - Math.sin(time * 3.5) * 0.15;
        leftArmPivot.rotation.z = 0.35 + Math.sin(time * 1.8) * 0.05;
        sproutPivot.rotation.z = Math.sin(time * 2.0) * 0.05;
      } else if (pet.state === "AWAITING") {
        pet.targetRotY = 0;
        petMaster.position.y = pet.baseY + naturalBreath;
        bodyGroup.rotation.x = 0;
        bodyGroup.rotation.z = 0;
        leftArmPivot.rotation.z = 0.35;
        rightArmPivot.rotation.z = -0.35;
        pet.stateTimer -= delta;
        if (pet.stateTimer <= 0) {
          pet.state = "IDLE";
          pet.stateTimer = 3.0;
        }
      } else if (pet.state === "UNBURDEN") {
        // Gentle exhale & open arms
        petMaster.position.y = pet.baseY + Math.sin(time * 1.2) * 0.02;
        bodyGroup.scale.set(1.03, 0.98, 1.03);
        leftArmPivot.rotation.z = 0.2;
        rightArmPivot.rotation.z = -0.2;
        sproutPivot.rotation.z = 0.08;
      } else if (pet.state === "SAVED") {
        // Hands over heart confirmation nod
        bodyGroup.rotation.x = Math.sin(time * 3.0) * 0.08;
        leftArmPivot.rotation.z = 0.75;
        rightArmPivot.rotation.z = -0.75;
      } else if (pet.state === "EMPATHY") {
        // Burden / Stress response: soothing sway, gentle forward lean, warm arms
        pet.napCounter = 0;
        pet.isNapping = false;
        pet.targetRotY = 0;
        petMaster.position.y = pet.baseY + Math.sin(time * 1.6) * 0.015;
        bodyGroup.rotation.x = -0.14; // empathetic forward lean
        bodyGroup.rotation.z = Math.sin(time * 1.4) * 0.06; // soothing sway
        leftArmPivot.rotation.z = 0.6 + Math.sin(time * 1.4) * 0.05; // open warm arms
        rightArmPivot.rotation.z = -0.6 - Math.sin(time * 1.4) * 0.05;
        sproutPivot.rotation.z = Math.sin(time * 1.2) * 0.08;
        leftBlush.material.opacity = 0.38;
        rightBlush.material.opacity = 0.38;
        pet.stateTimer -= delta;
        if (pet.stateTimer <= 0) pet.state = "ATTENTIVE";
      } else if (pet.state === "EPIPHANY") {
        // Insight / Clarity response: joyful energetic bounce, arms lifted, flutter
        pet.napCounter = 0;
        pet.isNapping = false;
        const bounceHop = Math.abs(Math.sin(time * 6.5)) * 0.16;
        petMaster.position.y = pet.baseY + bounceHop;
        bodyGroup.rotation.x = -0.05;
        bodyGroup.rotation.z = Math.sin(time * 8.0) * 0.1;
        leftArmPivot.rotation.z = 1.05 + Math.sin(time * 8.0) * 0.15; // arms up in joy
        rightArmPivot.rotation.z = -1.05 - Math.sin(time * 8.0) * 0.15;
        sproutPivot.rotation.z = Math.sin(time * 10.0) * 0.25;
        leftBlush.material.opacity = 0.45;
        rightBlush.material.opacity = 0.45;
        pet.stateTimer -= delta;
        if (pet.stateTimer <= 0) pet.state = "ATTENTIVE";
      } else if (pet.state === "CURIOUS") {
        // Questioning / Wonder response: inquisitive side head tilt and perked ear
        pet.napCounter = 0;
        pet.isNapping = false;
        pet.targetRotY = 0.18;
        petMaster.position.y = pet.baseY + Math.sin(time * 1.8) * 0.01;
        bodyGroup.rotation.x = -0.12;
        bodyGroup.rotation.z = 0.26 + Math.sin(time * 1.8) * 0.04; // curious side head tilt
        leftArmPivot.rotation.z = 0.55;
        rightArmPivot.rotation.z = -0.25;
        sproutPivot.rotation.z = 0.22 + Math.sin(time * 2.0) * 0.05;
        pet.stateTimer -= delta;
        if (pet.stateTimer <= 0) pet.state = "ATTENTIVE";
      } else if (pet.state === "GROUNDING") {
        // Stillness / Nature response: deep meditative breath expansion
        pet.napCounter = 0;
        pet.isNapping = false;
        const breath = Math.sin(time * 1.2);
        petMaster.position.y = pet.baseY + breath * 0.025;
        bodyGroup.scale.set(1.0 + breath * 0.05, 1.0 - breath * 0.03, 1.0 + breath * 0.05);
        bodyGroup.rotation.x = 0;
        bodyGroup.rotation.z = 0;
        leftArmPivot.rotation.z = 0.25;
        rightArmPivot.rotation.z = -0.25;
        sproutPivot.rotation.z = Math.sin(time * 1.2) * 0.04;
        pet.stateTimer -= delta;
        if (pet.stateTimer <= 0) pet.state = "IDLE";
      } else if (pet.state === "CELEBRATING") {
        // Cairns memory consecrated: celebratory 360-degree victory spin!
        pet.napCounter = 0;
        pet.isNapping = false;
        petMaster.rotation.y += delta * 6.5;
        petMaster.position.y = pet.baseY + Math.abs(Math.sin(time * 7.0)) * 0.22;
        bodyGroup.scale.set(1.05, 0.95, 1.05);
        leftArmPivot.rotation.z = 1.2;
        rightArmPivot.rotation.z = -1.2;
        sproutPivot.rotation.z = Math.sin(time * 12.0) * 0.3;
        leftBlush.material.opacity = 0.5;
        rightBlush.material.opacity = 0.5;
        pet.stateTimer -= delta;
        if (pet.stateTimer <= 0) pet.state = "IDLE";
      } else if (pet.state === "NAP") {
        pet.isNapping = true;
        const napBreath = Math.sin(time * 0.8) * 0.03;
        petMaster.position.y = pet.baseY - 0.03 + napBreath;
        bodyGroup.scale.set(1.03 + napBreath * 0.3, 0.97 + napBreath * 0.6, 1.03);
        leftArmPivot.rotation.z = 0.75;
        rightArmPivot.rotation.z = -0.75;

        if (isTypingRef.current || lifecycleRef.current !== "nap") {
          pet.isNapping = false;
          pet.state = "IDLE";
          pet.stateTimer = 2.0;
          pet.bounceVelocity = 0.2;
        }
      }

      // Interactive Petting reaction (mouse hover directly over mascot)
      if (pet.isPetting) {
        bodyGroup.scale.set(1.12, 0.88, 1.12);
        bodyGroup.rotation.z = Math.sin(time * 14.0) * 0.08;
        leftEyeGroup.scale.y = 0.25;
        rightEyeGroup.scale.y = 0.25;
        leftBlush.material.opacity = 0.55;
        rightBlush.material.opacity = 0.55;
      }

      // Keyboard keystroke bob micro-animation
      if (pet.keystrokeBob > 0) {
        bodyGroup.position.y += pet.keystrokeBob;
        bodyGroup.rotation.x -= pet.keystrokeBob * 0.8;
        pet.keystrokeBob = Math.max(0, pet.keystrokeBob - delta * 0.6);
      }

      // Smooth whole-body gaze tracking following mouse position across the screen
      const targetBodyTiltY = pet.mouseNorm.x * 0.28;
      const targetBodyTiltX = -pet.mouseNorm.y * 0.16;
      bodyGroup.rotation.y += (targetBodyTiltY - bodyGroup.rotation.y) * 0.12;
      bodyGroup.rotation.x += (targetBodyTiltX - bodyGroup.rotation.x) * 0.08;

      // Smooth Orientation
      pet.facingRotY += (pet.targetRotY - pet.facingRotY) * 0.1;
      petMaster.rotation.y = pet.facingRotY;

      // Spring physics on body squash/stretch
      const springK = 140;
      const damp = 12;
      const disp = pet.bounceScaleY - 1.0;
      pet.bounceVelocity += (-springK * disp - damp * pet.bounceVelocity) * delta;
      pet.bounceScaleY += pet.bounceVelocity * delta;

      // Numerical stability guards against NaN or runaway oscillation
      if (isNaN(pet.bounceScaleY) || !isFinite(pet.bounceScaleY)) pet.bounceScaleY = 1.0;
      if (isNaN(pet.bounceVelocity) || !isFinite(pet.bounceVelocity)) pet.bounceVelocity = 0;
      pet.bounceScaleY = Math.max(0.65, Math.min(1.35, pet.bounceScaleY));

      if (pet.state !== "HOPPING" && !pet.isPetting) {
        bodyGroup.scale.set(1.0, pet.bounceScaleY, 1.0);
      }

      // Eyelids & Gaze Tracking
      if (pet.isNapping) {
        leftEyeGroup.visible = false;
        rightEyeGroup.visible = false;
        leftClosed.visible = true;
        rightClosed.visible = true;
      } else {
        leftClosed.visible = false;
        rightClosed.visible = false;
        leftEyeGroup.visible = true;
        rightEyeGroup.visible = true;

        pet.blinkTimer -= delta;
        if (pet.blinkTimer <= 0) {
          pet.isBlinking = true;
          pet.blinkTimer = 3.0 + Math.random() * 3.5;
        }

        if (pet.isBlinking) {
          leftEyeGroup.scale.y = 0.1;
          rightEyeGroup.scale.y = 0.1;
          if (pet.blinkTimer < 2.85) {
            pet.isBlinking = false;
            leftEyeGroup.scale.y = 1.0;
            rightEyeGroup.scale.y = 1.0;
          }
        }

        // Restrained gaze tracking
        const lookX = pet.mouseNorm.x * 0.02;
        const lookY = pet.mouseNorm.y * 0.015;
        leftEyeGroup.position.x = -0.31 + lookX;
        leftEyeGroup.position.y = 0.18 + lookY;
        rightEyeGroup.position.x = 0.35 + lookX;
        rightEyeGroup.position.y = 0.13 + lookY;
      }

      renderer.render(scene, camera);
    };

    petLoop();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      if (resizeObserver) resizeObserver.disconnect();
      container.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointermove", handleGlobalPointer);
      container.removeEventListener("click", handlePetClick);
      pebbleGeometry.dispose();
      pebbleMaterial.dispose();
      eyeGeometry.dispose();
      eyeMaterial.dispose();
      renderer.dispose();
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, []);

  return (
    <div
      className={`relative w-full h-full select-none flex items-center justify-center overflow-hidden ${className}`}
      style={style}
      title="Sanctuary 3D Pebble Companion · Tap gently to greet or click along the ledge"
    >
      {/* 3D WebGL Canvas Viewport — completely transparent and unboxed */}
      <div
        ref={mountRef}
        className="w-full h-full cursor-pointer relative"
      />
    </div>
  );
}
