# Mega Test Prompt: 3D/4D Music Visualizer

> **Purpose:** Stress-test the core-spec plan protocol. This prompt should
> trigger Tier 2 phased specification automatically via complexity assessment
> rules — no `/spec:new` needed.
>
> **Prerequisites:** Run `claude-kit setup` first so `~/.claude/rules/claude-kit.md`
> is installed. The plan protocol section will fire when Claude receives this prompt.
>
> **Expected behavior:**
> 1. Claude detects 5/5 complexity heuristics (>5 files, >4 steps, multiple layers, scope words, underspecified requirements)
> 2. Claude creates a Tier 2 phased specification at `~/.claude-kit/plans/`
> 3. Claude creates a PLAN-ACTIVE TaskList anchor
> 4. After context compaction, Claude reads status.md and resumes from the correct phase
> 5. Plan gets updated as work progresses

---

## The Prompt

Copy everything below the line and paste it as the first message in a fresh
Claude Code session (with claude-kit rules installed).

---

Build a complete desktop application called **Synesthesia** — a real-time 3D and 4D music visualization tool built with Tauri 2 and SvelteKit 5, targeting Windows as the primary platform.

### Core Architecture

- **Tauri 2** backend (Rust) handles audio capture, FFT processing, and GPU compute
- **SvelteKit 5** frontend with Three.js / WebGPU for 3D rendering
- **Real-time audio analysis pipeline**: capture system audio output (WASAPI loopback on Windows), perform FFT, extract frequency bands, detect tempo/BPM, identify musical scales and keys, measure volume/RMS/peak levels
- The audio capture must work by default on Windows without requiring the user to install virtual audio cables — tap directly into the system's audio output

### Visualization Engine

Build an entire shader-based visualization system that responds in real time to:

- **Frequency spectrum** — bass, mids, highs mapped to different visual elements
- **Tempo/BPM** — pulse effects, rhythmic scaling, beat-synchronized transitions
- **Musical scale/key detection** — color palette shifts based on detected key (e.g., C major = warm, A minor = cool)
- **Volume/RMS** — global intensity, bloom, particle density
- **Transients/onsets** — flash effects, geometry spawning on drum hits

The system must support multiple visualization modes:

1. **Particle Field** — thousands of particles flowing through 3D space, reacting to frequency bands. Bass pushes outward, treble creates fine detail. 4D mode adds time-based trails that create history ribbons
2. **Geometric Landscape** — procedurally generated terrain mesh that deforms in real time based on audio. Mountains rise with bass, texture detail increases with high frequencies
3. **Neural Web** — interconnected node graph where connections pulse with the beat, node sizes respond to frequency bands, and the entire structure breathes with the music
4. **Waveform Tunnel** — camera flies through a tube constructed from the waveform, with the tube walls textured by spectral data and lit by beat-reactive lighting
5. **Fractal Bloom** — Mandelbrot/Julia set variations where iteration depth, zoom level, and color mapping are driven by audio parameters. 4D mode morphs between fractal types

### 4D Visualization

"4D" means the visualizations have a time dimension that creates persistent visual history:

- Trails, ribbons, and afterimages that show how the visualization evolved over the last N seconds
- Time-scrubbing: user can pause and scrub backward through the visual history
- Time-stretching: slow down or speed up the visual timeline independently of audio

### Texture Generation

- Procedural textures generated from audio data in real time (noise functions modulated by frequency bands)
- Texture caching system so textures don't regenerate every frame
- Support for user-provided texture packs that get audio-reactively blended

### Configuration UI

Build a modern, sleek configuration panel (think: Resolume Avenue, TouchDesigner):

- **Preset system** — save/load/share visualization presets as JSON files
- **Parameter mapping** — drag-and-drop any audio parameter (bass, BPM, key, volume) to any visual parameter (color, size, speed, intensity)
- **Real-time parameter tweaking** — sliders, color pickers, curve editors that update the visualization instantly
- **MIDI mapping** — map MIDI CC controls to visualization parameters for live performance
- **Audio device selector** — dropdown to choose which audio output to capture
- **Resolution/quality presets** — balanced, quality, performance modes

### Performance Requirements

- 60fps minimum at 1080p on a mid-range GPU (GTX 1660 / RX 5600)
- Audio latency under 20ms from sound to visual response
- Memory usage under 500MB for the base application
- GPU compute for FFT when WebGPU is available, CPU fallback otherwise

### Project Structure

Set up the entire project from scratch with:

- Tauri 2 + SvelteKit 5 scaffolding
- Rust audio capture crate (cpal + WASAPI)
- FFT processing pipeline (rustfft)
- TypeScript/Svelte component library for the config UI
- Three.js scene management with shader material system
- WebGPU compute shader pipeline for particle systems
- Build system that produces a Windows installer (.msi)
- Unit tests for the audio analysis pipeline
- Integration tests for the Tauri commands
