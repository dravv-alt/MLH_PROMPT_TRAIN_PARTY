import React, { useRef, useEffect, useState, useCallback } from "react";
import * as THREE from "three";

/**
 * Procedural texture generator for Sanctuary's official Pebble mascot.
 * Renders:
 * 1. Warm riverstone granite base with micro-stippling flecks.
 * 2. Distinctive diagonal quartz mineral vein with crystal margins.
 * 3. Soft mineral gradient.
 */
function createPebbleTextures() {
  const width = 1024;
  const height = 1024;

  // 1. Diffuse / Color Map
  const colorCanvas = document.createElement("canvas");
  colorCanvas.width = width;
  colorCanvas.height = height;
  const ctx = colorCanvas.getContext("2d");

  // Base stone gradient: slightly darker warm granite at base, luminous warm taupe at crown
  const grad = ctx.createLinearGradient(0, height, 0, 0);
  grad.addColorStop(0.0, "#BAAF9F"); // Deep weathered riverbed limestone
  grad.addColorStop(0.4, "#CBC1B2"); // Mid-body warm sandstone
  grad.addColorStop(0.85, "#DDD4C6"); // Luminous sunlit crown
  grad.addColorStop(1.0, "#E6DFC8");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  // Micro-stippling: thousands of tiny mineral grains (granite flecks)
  const rng = (seed) => {
    let s = seed % 2147483647;
    return () => (s = (s * 16807) % 2147483647) / 2147483647;
  };
  const rand = rng(42);

  // Dark specks
  ctx.fillStyle = "rgba(75, 65, 55, 0.12)";
  for (let i = 0; i < 14000; i++) {
    const x = rand() * width;
    const y = rand() * height;
    const r = rand() * 1.6 + 0.5;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  // Light quartz crystalline specks
  ctx.fillStyle = "rgba(255, 252, 245, 0.22)";
  for (let i = 0; i < 10000; i++) {
    const x = rand() * width;
    const y = rand() * height;
    const r = rand() * 1.4 + 0.4;
    ctx.beginPath();
    ctx.arc(x, y, r, 0, Math.PI * 2);
    ctx.fill();
  }

  // Signature Diagonal Quartz Vein: runs diagonally across the stone face
  // Starts upper-left (x ~ 180, y ~ 260) to lower-right (x ~ 840, y ~ 780)
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

    // Branching sub-fissure
    const branch = [
      { x: 620, y: 620 },
      { x: 690, y: 740 },
      { x: 730, y: 820 },
    ];

    // Soft outer translucent quartz halo
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

    // Secondary vein branch
    glowCtx.beginPath();
    branch.forEach((p, idx) => {
      const jx = p.x + (rand() - 0.5) * 6;
      const jy = p.y + (rand() - 0.5) * 6;
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

    // Core branch
    glowCtx.lineWidth = 6;
    glowCtx.beginPath();
    branch.forEach((p, idx) => {
      const jx = p.x + (rand() - 0.5) * 4;
      const jy = p.y + (rand() - 0.5) * 4;
      if (idx === 0) glowCtx.moveTo(jx, jy);
      else glowCtx.lineTo(jx, jy);
    });
    glowCtx.stroke();

    // Fine crystalline hairline center
    glowCtx.strokeStyle = isBump ? "#ffffff" : "#ffffff";
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

  // 2. Bump / Height Map
  const bumpCanvas = document.createElement("canvas");
  bumpCanvas.width = 512;
  bumpCanvas.height = 512;
  const bCtx = bumpCanvas.getContext("2d");
  bCtx.fillStyle = "#808080";
  bCtx.fillRect(0, 0, 512, 512);

  // Texture scale down for bump
  bCtx.scale(0.5, 0.5);
  drawVein(bCtx, true);

  const diffuseTexture = new THREE.CanvasTexture(colorCanvas);
  diffuseTexture.wrapS = THREE.RepeatWrapping;
  diffuseTexture.wrapT = THREE.ClampToEdgeWrapping;

  const bumpTexture = new THREE.CanvasTexture(bumpCanvas);
  bumpTexture.wrapS = THREE.RepeatWrapping;
  bumpTexture.wrapT = THREE.ClampToEdgeWrapping;

  return { diffuseTexture, bumpTexture };
}

/**
 * Creates the organic river pebble body geometry by deforming a high-poly sphere.
 */
function createRiverPebbleGeometry() {
  const geom = new THREE.SphereGeometry(1.0, 72, 72);
  const pos = geom.attributes.position;

  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);

    // 1. Organic Tapering: broader rounded base, narrower crown
    const normY = (y + 1) * 0.5; // 0 (bottom) to 1 (top)
    const taper = 1.08 - 0.32 * Math.pow(normY, 1.3);
    x *= taper;
    // River stones are naturally flattened front-to-back
    z *= taper * 0.86;

    // 2. Organic natural asymmetric tilt (slightly leaning left like the Stitch illustration)
    const lean = Math.sin(normY * Math.PI) * 0.08;
    x += lean;

    // 3. Stable flat bottom curve
    if (y < -0.55) {
      const bottomFlatten = (-0.55 - y) / 0.45;
      y += bottomFlatten * 0.12;
      x *= 1.0 + bottomFlatten * 0.08;
      z *= 1.0 + bottomFlatten * 0.08;
    }

    // 4. Subtle micro-waviness of water erosion
    const erosion = Math.sin(x * 3.2 + y * 2.5) * 0.02 + Math.cos(z * 3.8 + y * 2.2) * 0.015;
    x += erosion * x;
    y += erosion * 0.6;
    z += erosion * z;

    // 5. Final scale proportions
    x *= 1.1;
    y *= 1.32;
    z *= 0.96;

    pos.setXYZ(i, x, y, z);
  }

  geom.computeVertexNormals();
  return geom;
}

/**
 * Creates arm geometry (smooth tapered water-tumbled stone)
 */
function createArmGeometry(isLeft = true) {
  const geom = new THREE.CapsuleGeometry(0.18, 0.45, 24, 24);
  const pos = geom.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    let x = pos.getX(i);
    let y = pos.getY(i);
    let z = pos.getZ(i);

    // Taper towards the rounded tip
    const tipFactor = (y + 0.4) * 0.6;
    x *= 1.0 - tipFactor * 0.2;
    z *= 1.0 - tipFactor * 0.2;

    pos.setXYZ(i, x, y, z);
  }
  geom.computeVertexNormals();
  return geom;
}

/**
 * Creates sprout geometry with 3 delicate sage green leaves
 */
function createSproutGroup() {
  const sprout = new THREE.Group();

  // Slender organic stem
  const stemCurve = new THREE.CatmullRomCurve3([
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0.04, 0.18, 0.01),
    new THREE.Vector3(0.08, 0.36, -0.02),
  ]);
  const stemGeom = new THREE.TubeGeometry(stemCurve, 16, 0.022, 8, false);
  const stemMat = new THREE.MeshStandardMaterial({
    color: 0x637048,
    roughness: 0.6,
  });
  const stemMesh = new THREE.Mesh(stemGeom, stemMat);
  sprout.add(stemMesh);

  // Leaf creator
  const createLeaf = (scale = 1.0, rot = [0, 0, 0], pos = [0, 0, 0]) => {
    const leafGeom = new THREE.SphereGeometry(0.14, 16, 16);
    leafGeom.scale(0.48 * scale, 1.2 * scale, 0.08 * scale);
    const leafMat = new THREE.MeshStandardMaterial({
      color: 0x7a8a5b,
      roughness: 0.5,
      metalness: 0.05,
      side: THREE.DoubleSide,
    });
    const leafMesh = new THREE.Mesh(leafGeom, leafMat);
    leafMesh.position.set(...pos);
    leafMesh.rotation.set(...rot);
    return leafMesh;
  };

  // 3 Leaves matching official Stitch illustration
  const leaf1 = createLeaf(1.15, [0.3, 0.1, -0.3], [0.08, 0.36, -0.02]); // Top leaf
  const leaf2 = createLeaf(0.95, [0.1, 0.4, 0.6], [0.13, 0.31, 0.04]);  // Right leaf
  const leaf3 = createLeaf(0.85, [-0.4, -0.2, -0.5], [0.02, 0.28, -0.06]); // Left-back leaf

  sprout.add(leaf1);
  sprout.add(leaf2);
  sprout.add(leaf3);

  return sprout;
}

/**
 * PebbleMascot3D
 * 
 * High-fidelity, real-time 3D model of Sanctuary's official Pebble Mascot.
 * Features:
 * - Procedural river stone geometry with authentic mineral quartz vein & granite stippling.
 * - Interactive cursor tracking (tilts head & looks towards pointer).
 * - Interactive click-to-poke (squash & stretch physics bounce).
 * - Multiple poses: "welcome", "breathing" (meditative closed eyes), "wave", "epiphany".
 * - Dynamic breathing cycle with zen halo.
 * - Orbit drag rotation to inspect the 3D model 360 degrees.
 */
export default function PebbleMascot3D({
  pose = "welcome",       // "welcome", "breathing", "wave", "epiphany"
  interactive = true,
  showControls = true,
  showRipples = true,
  autoRotate = false,
  className = "",
  style = {},
  onPoke,
}) {
  const mountRef = useRef(null);
  const stateRef = useRef({
    pose,
    isHovered: false,
    isDragging: false,
    dragStart: { x: 0, y: 0 },
    rotationTarget: { x: 0, y: 0 },
    rotationCurrent: { x: 0, y: 0 },
    mouseNormalized: { x: 0, y: 0 },
    bounceVelocity: 0,
    bounceScale: 1,
    time: 0,
    isWaving: pose === "wave",
    isBreathingPose: pose === "breathing",
    isBlinking: false,
    blinkProgress: 0,
    sparkScale: 0,
  });

  const [activePose, setActivePose] = useState(pose);
  const [isZenSpin, setIsZenSpin] = useState(autoRotate);
  const [pokeCount, setPokeCount] = useState(0);
  const [isReady, setIsReady] = useState(false);

  // Keep stateRef in sync with active pose
  useEffect(() => {
    stateRef.current.pose = activePose;
    stateRef.current.isWaving = activePose === "wave";
    stateRef.current.isBreathingPose = activePose === "breathing";
  }, [activePose]);

  useEffect(() => {
    stateRef.current.isZenSpin = isZenSpin;
  }, [isZenSpin]);

  // Main Three.js Lifecycle
  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    const rect = container.getBoundingClientRect();
    const width = Math.max(32, Math.round(rect.width || container.clientWidth || 360));
    const height = Math.max(32, Math.round(rect.height || container.clientHeight || 360));

    // 1. Scene & Camera
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(36, width / height, 0.1, 100);
    // Frame closer when ripples are hidden (e.g. compact avatar or chat box companion)
    if (!showRipples) {
      camera.position.set(0, 0.02, 4.3);
    } else {
      camera.position.set(0, 0.2, 5.0);
    }
    camera.lookAt(0, 0, 0);

    // 2. WebGL Renderer with anti-aliasing and pixel ratio optimization
    let renderer;
    try {
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: "high-performance",
      });
    } catch (e) {
      console.warn("WebGL initialization failed:", e);
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

    // 3. Lighting: Contemplative Studio Rig
    // Warm ambient light
    const ambientLight = new THREE.AmbientLight(0xfffaed, 1.25);
    scene.add(ambientLight);

    // Main warm sunlight key light
    const keyLight = new THREE.DirectionalLight(0xfff6ea, 1.6);
    keyLight.position.set(3.5, 4.5, 4.0);
    scene.add(keyLight);

    // Cool skylight fill
    const fillLight = new THREE.DirectionalLight(0xe4ece6, 0.75);
    fillLight.position.set(-3.5, 2.0, 3.0);
    scene.add(fillLight);

    // Back / Rim light for silhouette definition
    const rimLight = new THREE.DirectionalLight(0xdbe7dc, 0.9);
    rimLight.position.set(-2.0, 3.5, -3.5);
    scene.add(rimLight);

    // Ground bounce light
    const groundBounce = new THREE.HemisphereLight(0xfffaed, 0x988f82, 0.4);
    scene.add(groundBounce);

    // 4. Pebble Mascot Assembly
    const mascotRoot = new THREE.Group();
    mascotRoot.position.set(0, -0.08, 0);
    scene.add(mascotRoot);

    // Body Group (for breathing and squash/stretch physics)
    const bodyGroup = new THREE.Group();
    mascotRoot.add(bodyGroup);

    // Procedural Textures
    const { diffuseTexture, bumpTexture } = createPebbleTextures();

    // Body Material
    const pebbleMaterial = new THREE.MeshStandardMaterial({
      map: diffuseTexture,
      bumpMap: bumpTexture,
      bumpScale: 0.024,
      roughness: 0.84,
      metalness: 0.03,
      color: 0xffffff,
    });

    // Body Mesh
    const pebbleGeometry = createRiverPebbleGeometry();
    const pebbleMesh = new THREE.Mesh(pebbleGeometry, pebbleMaterial);
    bodyGroup.add(pebbleMesh);

    // 5. Facial Features: Eyes & Smile
    // Eyes: Two glossy obsidian river pebbles
    const eyeGeometry = new THREE.SphereGeometry(0.095, 32, 32);
    const eyeMaterial = new THREE.MeshStandardMaterial({
      color: 0x141312,
      roughness: 0.12,
      metalness: 0.18,
    });

    // Left Eye
    const leftEyeGroup = new THREE.Group();
    leftEyeGroup.position.set(-0.31, 0.18, 0.86);
    const leftEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    leftEye.scale.set(1.0, 1.0, 0.7);
    leftEyeGroup.add(leftEye);

    // Catchlight Glint (tiny specular reflection sphere)
    const glintGeom = new THREE.SphereGeometry(0.024, 16, 16);
    const glintMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const leftGlint = new THREE.Mesh(glintGeom, glintMat);
    leftGlint.position.set(-0.026, 0.026, 0.075);
    leftEyeGroup.add(leftGlint);

    // Right Eye
    const rightEyeGroup = new THREE.Group();
    rightEyeGroup.position.set(0.35, 0.13, 0.84);
    const rightEye = new THREE.Mesh(eyeGeometry, eyeMaterial);
    rightEye.scale.set(1.0, 1.0, 0.7);
    rightEyeGroup.add(rightEye);

    const rightGlint = new THREE.Mesh(glintGeom, glintMat);
    rightGlint.position.set(-0.026, 0.026, 0.075);
    rightEyeGroup.add(rightGlint);

    bodyGroup.add(leftEyeGroup);
    bodyGroup.add(rightEyeGroup);

    // Serene Curved Eyelids for Meditation / Breathe pose
    const closedEyeCurveLeft = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(-0.08, 0, 0),
      new THREE.Vector3(0, -0.05, 0),
      new THREE.Vector3(0.08, 0, 0)
    );
    const closedEyeGeomLeft = new THREE.TubeGeometry(closedEyeCurveLeft, 16, 0.016, 8, false);
    const closedEyeMat = new THREE.MeshStandardMaterial({
      color: 0x2d2924,
      roughness: 0.8,
    });
    const leftClosedEye = new THREE.Mesh(closedEyeGeomLeft, closedEyeMat);
    leftClosedEye.position.set(-0.31, 0.18, 0.88);
    leftClosedEye.visible = false;
    bodyGroup.add(leftClosedEye);

    const closedEyeCurveRight = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(-0.08, 0, 0),
      new THREE.Vector3(0, -0.05, 0),
      new THREE.Vector3(0.08, 0, 0)
    );
    const closedEyeGeomRight = new THREE.TubeGeometry(closedEyeCurveRight, 16, 0.016, 8, false);
    const rightClosedEye = new THREE.Mesh(closedEyeGeomRight, closedEyeMat);
    rightClosedEye.position.set(0.35, 0.13, 0.86);
    rightClosedEye.visible = false;
    bodyGroup.add(rightClosedEye);

    // Smile: Gentle curved groove tube
    const smileCurve = new THREE.QuadraticBezierCurve3(
      new THREE.Vector3(-0.11, 0.02, 0),
      new THREE.Vector3(0.0, -0.04, 0),
      new THREE.Vector3(0.12, 0.01, 0)
    );
    const smileGeom = new THREE.TubeGeometry(smileCurve, 20, 0.016, 8, false);
    const smileMat = new THREE.MeshStandardMaterial({
      color: 0x483f36,
      roughness: 0.85,
    });
    const smileMesh = new THREE.Mesh(smileGeom, smileMat);
    smileMesh.position.set(0.02, 0.04, 0.92);
    bodyGroup.add(smileMesh);

    // Rosy Mineral Blush Discs
    const blushGeom = new THREE.CircleGeometry(0.09, 24);
    const blushMat = new THREE.MeshBasicMaterial({
      color: 0xd99b8b,
      transparent: true,
      opacity: 0.28,
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

    // 6. Arms with Shoulder Pivot Groups
    const leftArmPivot = new THREE.Group();
    leftArmPivot.position.set(-0.92, -0.12, 0.08);
    leftArmPivot.rotation.set(0, 0, 0.45); // resting angle

    const leftArmGeom = createArmGeometry(true);
    const leftArmMesh = new THREE.Mesh(leftArmGeom, pebbleMaterial);
    leftArmMesh.position.set(-0.15, -0.15, 0);
    leftArmMesh.rotation.set(0, 0, 0.7);
    leftArmPivot.add(leftArmMesh);
    bodyGroup.add(leftArmPivot);

    const rightArmPivot = new THREE.Group();
    rightArmPivot.position.set(0.96, -0.16, 0.08);
    rightArmPivot.rotation.set(0, 0, -0.45); // resting angle

    const rightArmGeom = createArmGeometry(false);
    const rightArmMesh = new THREE.Mesh(rightArmGeom, pebbleMaterial);
    rightArmMesh.position.set(0.15, -0.15, 0);
    rightArmMesh.rotation.set(0, 0, -0.7);
    rightArmPivot.add(rightArmMesh);
    bodyGroup.add(rightArmPivot);

    // 7. Top Leaf Sprout (3 leaves with spring inertia)
    const sproutPivot = new THREE.Group();
    sproutPivot.position.set(0.34, 1.28, -0.04);
    const sproutMesh = createSproutGroup();
    sproutPivot.add(sproutMesh);
    bodyGroup.add(sproutPivot);

    // 8. Epiphany Celestial Spark Group (for epiphany pose / joyful click)
    const sparkGroup = new THREE.Group();
    sparkGroup.position.set(0.42, 1.85, 0);
    const sparkCoreGeom = new THREE.OctahedronGeometry(0.12, 0);
    const sparkMat = new THREE.MeshBasicMaterial({
      color: 0xffe279,
      wireframe: false,
    });
    const sparkMesh = new THREE.Mesh(sparkCoreGeom, sparkMat);
    sparkGroup.add(sparkMesh);

    // Tiny orbital spark points
    const sparkOrbitGeom = new THREE.SphereGeometry(0.03, 8, 8);
    const sparkOrbitMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
    const orbiter1 = new THREE.Mesh(sparkOrbitGeom, sparkOrbitMat);
    orbiter1.position.set(0.2, 0.05, 0);
    const orbiter2 = new THREE.Mesh(sparkOrbitGeom, sparkOrbitMat);
    orbiter2.position.set(-0.18, -0.08, 0.1);
    sparkGroup.add(orbiter1);
    sparkGroup.add(orbiter2);
    sparkGroup.scale.set(0, 0, 0);
    mascotRoot.add(sparkGroup);

    // 9. Ground Zen Sand Bed & Ripples
    let groundGroup = null;
    if (showRipples) {
      groundGroup = new THREE.Group();
      groundGroup.position.set(0, -1.35, 0);

      // Soft contact shadow disk directly under stone
      const shadowCanvas = document.createElement("canvas");
      shadowCanvas.width = 256;
      shadowCanvas.height = 256;
      const sCtx = shadowCanvas.getContext("2d");
      const shadowGrad = sCtx.createRadialGradient(128, 128, 0, 128, 128, 120);
      shadowGrad.addColorStop(0, "rgba(23, 52, 41, 0.42)");
      shadowGrad.addColorStop(0.4, "rgba(46, 75, 63, 0.22)");
      shadowGrad.addColorStop(0.8, "rgba(80, 100, 90, 0.05)");
      shadowGrad.addColorStop(1.0, "rgba(0, 0, 0, 0)");
      sCtx.fillStyle = shadowGrad;
      sCtx.fillRect(0, 0, 256, 256);

      const shadowTex = new THREE.CanvasTexture(shadowCanvas);
      const shadowPlaneGeom = new THREE.PlaneGeometry(2.8, 2.8);
      const shadowPlaneMat = new THREE.MeshBasicMaterial({
        map: shadowTex,
        transparent: true,
        depthWrite: false,
      });
      const shadowMesh = new THREE.Mesh(shadowPlaneGeom, shadowPlaneMat);
      shadowMesh.rotation.x = -Math.PI / 2;
      groundGroup.add(shadowMesh);

      // Concentric Zen Sand Rake Rings
      const ringRadii = [1.2, 1.55, 1.95];
      ringRadii.forEach((rad) => {
        const ringGeom = new THREE.RingGeometry(rad - 0.012, rad + 0.012, 64);
        const ringMat = new THREE.MeshBasicMaterial({
          color: 0xbaa894,
          transparent: true,
          opacity: 0.35,
          side: THREE.DoubleSide,
        });
        const ringMesh = new THREE.Mesh(ringGeom, ringMat);
        ringMesh.rotation.x = -Math.PI / 2;
        groundGroup.add(ringMesh);
      });

      // 3 Tiny River Pebbles on the sand bed
      const miniPebbleMat = new THREE.MeshStandardMaterial({
        color: 0xb5aa9b,
        roughness: 0.9,
      });
      const addMiniPebble = (x, z, s) => {
        const pGeom = new THREE.DodecahedronGeometry(0.12 * s, 1);
        pGeom.scale(1.2, 0.6, 0.9);
        const pMesh = new THREE.Mesh(pGeom, miniPebbleMat);
        pMesh.position.set(x, 0.04 * s, z);
        groundGroup.add(pMesh);
      };
      addMiniPebble(-1.4, 0.6, 0.9);
      addMiniPebble(1.6, 0.4, 1.1);
      addMiniPebble(-0.8, 1.3, 0.7);

      scene.add(groundGroup);
    }

    setIsReady(true);

    // 10. Pointer & Mouse Event Listeners
    const handlePointerMove = (e) => {
      const rect = container.getBoundingClientRect();
      const normX = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      const normY = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      stateRef.current.mouseNormalized = { x: normX, y: normY };

      if (stateRef.current.isDragging) {
        const deltaX = e.clientX - stateRef.current.dragStart.x;
        const deltaY = e.clientY - stateRef.current.dragStart.y;
        stateRef.current.rotationTarget.y += deltaX * 0.012;
        stateRef.current.rotationTarget.x = Math.max(
          -0.5,
          Math.min(0.5, stateRef.current.rotationTarget.x + deltaY * 0.008)
        );
        stateRef.current.dragStart = { x: e.clientX, y: e.clientY };
      }
    };

    const handlePointerDown = (e) => {
      stateRef.current.isDragging = true;
      stateRef.current.dragStart = { x: e.clientX, y: e.clientY };
    };

    const handlePointerUp = () => {
      stateRef.current.isDragging = false;
    };

    // Raycast click detection for poking Pebble
    const raycaster = new THREE.Raycaster();
    const mouseVector = new THREE.Vector2();

    const handleClick = (e) => {
      const rect = container.getBoundingClientRect();
      mouseVector.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouseVector.y = -(((e.clientY - rect.top) / rect.height) * 2 - 1);
      raycaster.setFromCamera(mouseVector, camera);

      const intersects = raycaster.intersectObject(pebbleMesh);
      if (intersects.length > 0) {
        // Poke triggered! Squash and stretch physics
        stateRef.current.bounceVelocity = 0.35;
        stateRef.current.isBlinking = true;
        stateRef.current.blinkProgress = 0;
        setPokeCount((c) => c + 1);
        if (onPoke) onPoke();
      }
    };

    if (interactive) {
      container.addEventListener("pointermove", handlePointerMove);
      container.addEventListener("pointerdown", handlePointerDown);
      window.addEventListener("pointerup", handlePointerUp);
      container.addEventListener("click", handleClick);
    }

    // Resize Handler with ResizeObserver
    const handleResize = () => {
      if (!container) return;
      const rect = container.getBoundingClientRect();
      const newW = Math.max(32, Math.round(rect.width || container.clientWidth));
      const newH = Math.max(32, Math.round(rect.height || container.clientHeight));
      camera.aspect = newW / newH;
      camera.updateProjectionMatrix();
      renderer.setSize(newW, newH, false);
    };

    let resizeObserver = null;
    if (typeof ResizeObserver !== "undefined") {
      resizeObserver = new ResizeObserver(() => {
        handleResize();
      });
      resizeObserver.observe(container);
    }
    window.addEventListener("resize", handleResize);

    // 11. Main Contemplative Animation Loop
    let animId;
    let clock = new THREE.Clock();

    const animateLoop = () => {
      animId = requestAnimationFrame(animateLoop);
      const delta = clock.getDelta();
      const time = clock.getElapsedTime();
      stateRef.current.time = time;

      const {
        pose: currentPose,
        isZenSpin: zenSpinning,
        isDragging,
        mouseNormalized,
        rotationTarget,
        rotationCurrent,
      } = stateRef.current;

      // Zen auto-rotation
      if (zenSpinning && !isDragging) {
        rotationTarget.y += delta * 0.45;
      }

      // Smooth Orbit Lerp
      rotationCurrent.x += (rotationTarget.x - rotationCurrent.x) * 0.1;
      rotationCurrent.y += (rotationTarget.y - rotationCurrent.y) * 0.1;

      // Pointer Head-Tracking (tilting towards cursor if not dragging)
      const lookTiltX = !isDragging ? -mouseNormalized.y * 0.22 : 0;
      const lookTiltY = !isDragging ? mouseNormalized.x * 0.32 : 0;

      mascotRoot.rotation.x = rotationCurrent.x + lookTiltX;
      mascotRoot.rotation.y = rotationCurrent.y + lookTiltY;

      // Eye pupil tracking
      const pupilShiftX = mouseNormalized.x * 0.024;
      const pupilShiftY = mouseNormalized.y * 0.018;
      leftEyeGroup.position.x = -0.31 + pupilShiftX;
      leftEyeGroup.position.y = 0.18 + pupilShiftY;
      rightEyeGroup.position.x = 0.35 + pupilShiftX;
      rightEyeGroup.position.y = 0.13 + pupilShiftY;

      // Squash & Stretch Spring Physics
      const springStiffness = 140;
      const springDamping = 10;
      const displacement = stateRef.current.bounceScale - 1.0;
      const springForce = -springStiffness * displacement;
      const dampingForce = -springDamping * stateRef.current.bounceVelocity;
      stateRef.current.bounceVelocity += (springForce + dampingForce) * delta;
      stateRef.current.bounceScale += stateRef.current.bounceVelocity * delta;

      // Breathing Cycle
      const isBreathingMode = currentPose === "breathing";
      const breathSpeed = isBreathingMode ? 1.0 : 1.35; // Slower rhythmic breath in breathing pose
      const breathPhase = Math.sin(time * breathSpeed);
      const breathExpansion = breathPhase * (isBreathingMode ? 0.045 : 0.025);
      const verticalFloat = Math.sin(time * 1.1) * 0.035;

      // Apply body transform
      const currentScaleY = stateRef.current.bounceScale * (1.0 + breathExpansion);
      const currentScaleXZ = (1.0 / Math.sqrt(Math.max(0.2, currentScaleY))) * (1.0 + breathExpansion * 0.5);

      bodyGroup.scale.set(currentScaleXZ, currentScaleY, currentScaleXZ);
      bodyGroup.position.y = verticalFloat;

      // Random eye blink cycle
      if (!isBreathingMode) {
        if (!stateRef.current.isBlinking && Math.random() < 0.006) {
          stateRef.current.isBlinking = true;
          stateRef.current.blinkProgress = 0;
        }

        if (stateRef.current.isBlinking) {
          stateRef.current.blinkProgress += delta * 7;
          const blinkFactor = Math.sin(Math.min(Math.PI, stateRef.current.blinkProgress));
          const eyeScaleY = Math.max(0.1, 1.0 - blinkFactor * 0.9);
          leftEyeGroup.scale.y = eyeScaleY;
          rightEyeGroup.scale.y = eyeScaleY;

          if (stateRef.current.blinkProgress >= Math.PI) {
            stateRef.current.isBlinking = false;
            leftEyeGroup.scale.y = 1.0;
            rightEyeGroup.scale.y = 1.0;
          }
        }
      }

      // Pose: Breathing / Meditation Mode
      if (isBreathingMode) {
        // Eyes closed serenely
        leftEyeGroup.visible = false;
        rightEyeGroup.visible = false;
        leftClosedEye.visible = true;
        rightClosedEye.visible = true;

        // Arms folded serenely on belly
        leftArmPivot.rotation.z = 0.85 + Math.sin(time * breathSpeed) * 0.04;
        leftArmPivot.rotation.y = 0.5;
        rightArmPivot.rotation.z = -0.85 - Math.sin(time * breathSpeed) * 0.04;
        rightArmPivot.rotation.y = -0.5;
      } else {
        leftEyeGroup.visible = true;
        rightEyeGroup.visible = true;
        leftClosedEye.visible = false;
        rightClosedEye.visible = false;

        // Pose: Waving
        if (currentPose === "wave") {
          // Right arm raised and waving warmly
          const waveAngle = Math.sin(time * 6.5) * 0.32;
          rightArmPivot.rotation.z = -1.45 + waveAngle;
          rightArmPivot.rotation.y = 0.2;
          leftArmPivot.rotation.z = 0.45;
          leftArmPivot.rotation.y = 0;
          // Body slight joyful rock
          mascotRoot.rotation.z = Math.sin(time * 3.2) * 0.035;
        } else if (currentPose === "epiphany") {
          // Both arms slightly raised in wonder
          leftArmPivot.rotation.z = 0.7;
          rightArmPivot.rotation.z = -0.7;
          mascotRoot.rotation.z = 0;
        } else {
          // Default Welcome / Listening pose: relaxed resting arms with subtle breath sway
          leftArmPivot.rotation.z = 0.42 + breathPhase * 0.03;
          leftArmPivot.rotation.y = 0.1;
          rightArmPivot.rotation.z = -0.42 - breathPhase * 0.03;
          rightArmPivot.rotation.y = -0.1;
          mascotRoot.rotation.z = 0;
        }
      }

      // Top Leaf Sprout Inertia: sway in reaction to body motion & wind
      const sproutSway = Math.sin(time * 2.4) * 0.06 - lookTiltY * 0.4;
      sproutPivot.rotation.z = sproutSway;

      // Epiphany Celestial Spark
      if (currentPose === "epiphany") {
        stateRef.current.sparkScale = Math.min(1.0, stateRef.current.sparkScale + delta * 3.5);
        sparkMesh.rotation.y = time * 2.0;
        sparkMesh.rotation.x = time * 1.4;
        sparkGroup.position.y = 1.85 + Math.sin(time * 2.8) * 0.06;
      } else {
        stateRef.current.sparkScale = Math.max(0.0, stateRef.current.sparkScale - delta * 4.0);
      }
      sparkGroup.scale.setScalar(stateRef.current.sparkScale);

      // Render Scene
      renderer.render(scene, camera);
    };

    animateLoop();

    // Cleanup on unmount
    return () => {
      cancelAnimationFrame(animId);
      if (resizeObserver) resizeObserver.disconnect();
      window.removeEventListener("resize", handleResize);
      if (interactive) {
        container.removeEventListener("pointermove", handlePointerMove);
        container.removeEventListener("pointerdown", handlePointerDown);
        window.removeEventListener("pointerup", handlePointerUp);
        container.removeEventListener("click", handleClick);
      }
      pebbleGeometry.dispose();
      pebbleMaterial.dispose();
      eyeGeometry.dispose();
      eyeMaterial.dispose();
      diffuseTexture.dispose();
      bumpTexture.dispose();
      renderer.dispose();
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement);
      }
    };
  }, [interactive, showRipples]);

  // Reset Camera & Rotation Helper
  const handleResetView = useCallback(() => {
    stateRef.current.rotationTarget = { x: 0, y: 0 };
  }, []);

  const handlePokeClick = () => {
    stateRef.current.bounceVelocity = 0.35;
    stateRef.current.isBlinking = true;
    stateRef.current.blinkProgress = 0;
    setPokeCount((c) => c + 1);
    if (onPoke) onPoke();
  };

  return (
    <div className={`relative flex flex-col items-center select-none w-full h-full ${className}`} style={style}>
      {/* 3D WebGL Canvas Container */}
      <div
        ref={mountRef}
        className="w-full h-full cursor-grab active:cursor-grabbing relative flex items-center justify-center overflow-hidden"
        title="Sanctuary 3D Pebble Mascot · Drag to rotate, click to poke"
      />

      {/* Interactive Controls Bar */}
      {showControls && (
        <div className="w-full mt-3 flex flex-wrap items-center justify-between gap-2 px-3 py-2 bg-surface-container-lowest/80 border border-outline-variant/30 rounded-xl backdrop-blur-sm">
          {/* Pose Selector */}
          <div className="flex items-center gap-1">
            {[
              { id: "welcome", label: "Welcome", icon: "🌿" },
              { id: "breathing", label: "Breathe", icon: "🧘" },
              { id: "wave", label: "Wave", icon: "👋" },
              { id: "epiphany", label: "Insight", icon: "✨" },
            ].map((p) => (
              <button
                key={p.id}
                onClick={() => setActivePose(p.id)}
                className={`text-[11px] font-label px-2.5 py-1 rounded-full transition-colors flex items-center gap-1.5 ${
                  activePose === p.id
                    ? "bg-primary text-on-primary font-medium shadow-none"
                    : "text-secondary hover:text-on-surface hover:bg-surface-container-low"
                }`}
              >
                <span>{p.icon}</span>
                <span>{p.label}</span>
              </button>
            ))}
          </div>

          {/* Action buttons: Poke & Zen Spin */}
          <div className="flex items-center gap-1.5 text-[11px] font-label text-secondary">
            <button
              onClick={handlePokeClick}
              title="Give Pebble a gentle poke"
              className="px-2.5 py-1 bg-surface-container-low hover:bg-surface-container hover:text-primary rounded-full transition-colors flex items-center gap-1"
            >
              <span>🫧</span>
              <span>Poke {pokeCount > 0 ? `(${pokeCount})` : ""}</span>
            </button>

            <button
              onClick={() => setIsZenSpin(!isZenSpin)}
              title="Toggle continuous calm rotation"
              className={`px-2.5 py-1 rounded-full transition-colors flex items-center gap-1 ${
                isZenSpin
                  ? "bg-primary-container text-on-primary-container font-medium"
                  : "bg-surface-container-low hover:bg-surface-container"
              }`}
            >
              <span>🔄</span>
              <span>Spin</span>
            </button>

            <button
              onClick={handleResetView}
              title="Reset front-facing angle"
              className="px-2 py-1 bg-surface-container-low hover:bg-surface-container rounded-full transition-colors"
            >
              Reset
            </button>
          </div>
        </div>
      )}

      {/* Gentle interaction tooltip */}
      {showControls && (
        <div className="text-[10px] text-outline font-label mt-1 text-center">
          <span>Drag to rotate 360° · Click stone to interact · Eyes follow your cursor</span>
        </div>
      )}
    </div>
  );
}
