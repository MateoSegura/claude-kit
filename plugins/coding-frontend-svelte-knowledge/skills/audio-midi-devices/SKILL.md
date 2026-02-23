---
name: coding-frontend-svelte-knowledge:audio-midi-devices
description: "Audio I/O and MIDI device access from Tauri Rust backends: cpal for cross-platform audio capture and playback, midir for MIDI input/output, real-time audio streaming to frontend via Tauri events, audio device enumeration, ring buffer patterns for low-latency streaming, and Svelte audio/MIDI UI components (level meters, waveform canvas, virtual keyboard)."
user-invocable: true
---

# Audio / MIDI Devices Quick Reference

Audio and MIDI from a Tauri app are handled entirely in Rust. The frontend calls `invoke()` for commands and `listen()` for real-time event streams — the crate choice is invisible to Svelte.

## Section 1 — Crate Overview

| Crate | Purpose | Async Support |
|-------|---------|---------------|
| `cpal` | Cross-platform audio I/O — input capture, output playback, device enumeration, sample format handling | Callback-based; pair with Tokio for event emission |
| `midir` | MIDI input/output — port enumeration, message send/receive, SysEx | Callback-based for input; blocking output |
| `ringbuf` | Lock-free SPSC ring buffer for audio callback → Tauri event bridge | Async consumer available |
| `realfft` | Real-to-complex FFT for spectrum display (powers of 2 only) | No |

**cpal** handles audio; it does NOT do MIDI. **midir** handles MIDI; it does NOT handle audio.

### Cargo.toml

```toml
[dependencies]
cpal = "0.15"
midir = "0.10"
ringbuf = "0.4"
tauri = { version = "2", features = ["default"] }
tokio = { version = "1", features = ["full"] }
serde_json = "1"
```

---

## Section 2 — Audio Device Patterns

### Enumerate Devices

```rust
use cpal::traits::{DeviceTrait, HostTrait};

#[tauri::command]
fn list_audio_input_devices() -> Result<Vec<String>, String> {
    let host = cpal::default_host();
    let devices = host.input_devices().map_err(|e| e.to_string())?;
    Ok(devices.filter_map(|d| d.name().ok()).collect())
}

// Query supported configs for a device
fn query_configs(device: &cpal::Device) {
    for cfg in device.supported_input_configs().unwrap() {
        println!(
            "ch={} rate={}–{} fmt={:?}",
            cfg.channels(),
            cfg.min_sample_rate().0,
            cfg.max_sample_rate().0,
            cfg.sample_format()
        );
    }
}
```

### Open Input Stream (Microphone Capture)

Use a lock-free ring buffer between the audio callback and the Tauri event emitter task:

```rust
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, Stream};
use ringbuf::{HeapRb, traits::Split};

fn build_capture_stream(producer: ringbuf::HeapProd<f32>) -> Result<Stream, String> {
    let host = cpal::default_host();
    let device = host.default_input_device().ok_or("No input device")?;
    let config = device.default_input_config().map_err(|e| e.to_string())?;
    let mut prod = producer;

    match config.sample_format() {
        SampleFormat::F32 => device.build_input_stream(
            &config.into(),
            move |data: &[f32], _| {
                for &s in data { let _ = prod.try_push(s); }
            },
            |err| eprintln!("Error: {err}"),
            None,
        ),
        SampleFormat::I16 => device.build_input_stream(
            &config.into(),
            move |data: &[i16], _| {
                for &s in data {
                    let _ = prod.try_push(s as f32 / i16::MAX as f32);
                }
            },
            |err| eprintln!("Error: {err}"),
            None,
        ),
        f => return Err(format!("Unsupported format: {:?}", f)),
    }.map_err(|e| e.to_string())
}
```

### Open Output Stream (Playback)

```rust
fn build_output_stream(mut consumer: ringbuf::HeapCons<f32>) -> cpal::Stream {
    let host = cpal::default_host();
    let device = host.default_output_device().expect("no output device");
    let config = device.default_output_config().unwrap();
    let channels = config.channels() as usize;

    device.build_output_stream(
        &config.into(),
        move |data: &mut [f32], _| {
            for frame in data.chunks_mut(channels) {
                let s = consumer.try_pop().unwrap_or(0.0);
                for ch in frame.iter_mut() { *ch = s; }
            }
        },
        |err| eprintln!("Output error: {err}"),
        None,
    ).unwrap()
}
```

---

## Section 3 — MIDI Patterns

### Enumerate and Connect Input

```rust
use midir::{MidiInput, MidiInputConnection};
use tauri::{AppHandle, Emitter};

#[tauri::command]
fn list_midi_input_ports() -> Result<Vec<String>, String> {
    let input = MidiInput::new("tauri-app").map_err(|e| e.to_string())?;
    input.ports().iter()
        .map(|p| input.port_name(p).map_err(|e| e.to_string()))
        .collect()
}

fn connect_midi_input(app: AppHandle, port_name: &str) -> Result<MidiInputConnection<()>, String> {
    let input = MidiInput::new("tauri-app").map_err(|e| e.to_string())?;
    let port = input.ports().into_iter()
        .find(|p| input.port_name(p).as_deref() == Ok(port_name))
        .ok_or("Port not found")?;

    input.connect(&port, "midi-in", move |_ts, msg, _| {
        if msg.len() >= 2 {
            let _ = app.emit("midi-in", serde_json::json!({
                "type": parse_midi_type(msg),
                "channel": (msg[0] & 0x0F) + 1,
                "note": msg.get(1).copied().unwrap_or(0),
                "value": msg.get(2).copied().unwrap_or(0),
                "raw": msg.to_vec(),
            }));
        }
    }, ()).map_err(|e| e.to_string())
}

fn parse_midi_type(msg: &[u8]) -> &'static str {
    match msg[0] & 0xF0 {
        0x80 => "note-off",
        0x90 => if msg.get(2).copied().unwrap_or(0) > 0 { "note-on" } else { "note-off" },
        0xB0 => "control-change",
        0xC0 => "program-change",
        0xE0 => "pitch-bend",
        0xF0 => "sysex",
        _    => "unknown",
    }
}
```

### Connect and Send MIDI Output

```rust
use midir::{MidiOutput, MidiOutputConnection};

fn connect_midi_output(port_name: &str) -> Result<MidiOutputConnection, String> {
    let output = MidiOutput::new("tauri-app").map_err(|e| e.to_string())?;
    let port = output.ports().into_iter()
        .find(|p| output.port_name(p).as_deref() == Ok(port_name))
        .ok_or("Port not found")?;
    output.connect(&port, "midi-out").map_err(|e| e.to_string())
}

// Message constructors
// Note on:        [0x90 | ch, note, velocity]
// Note off:       [0x80 | ch, note, 0]
// Control change: [0xB0 | ch, cc, value]
// Program change: [0xC0 | ch, program]   (2 bytes only)
// SysEx:          [0xF0, ...data..., 0xF7]

fn send_note_on(conn: &mut MidiOutputConnection, ch: u8, note: u8, vel: u8) {
    conn.send(&[0x90 | (ch & 0x0F), note, vel]).unwrap();
}
fn send_note_off(conn: &mut MidiOutputConnection, ch: u8, note: u8) {
    conn.send(&[0x80 | (ch & 0x0F), note, 0]).unwrap();
}
fn send_cc(conn: &mut MidiOutputConnection, ch: u8, cc: u8, value: u8) {
    conn.send(&[0xB0 | (ch & 0x0F), cc, value]).unwrap();
}
```

---

## Section 4 — Real-Time Audio Streaming

The audio callback runs on a real-time OS thread. **Never allocate, lock, or do I/O inside the callback.** Use a lock-free ring buffer to bridge to the Tauri event system.

### Ring Buffer → Event Emitter Pattern

```rust
use tauri::{AppHandle, Emitter};
use ringbuf::{HeapRb, traits::Split};

pub fn start_audio_bridge(app: AppHandle) {
    let (producer, mut consumer) = HeapRb::<f32>::new(8192).split();

    let stream = build_capture_stream(producer).unwrap();
    stream.play().unwrap();

    // Emit audio chunks at ~30 fps
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(
            std::time::Duration::from_millis(33)
        );
        loop {
            interval.tick().await;
            let mut chunk = Vec::with_capacity(1024);
            while let Some(s) = consumer.try_pop() {
                chunk.push(s);
                if chunk.len() >= 1024 { break; }
            }
            if chunk.is_empty() { continue; }

            // Downsample 4× for waveform display
            let waveform: Vec<f32> = chunk.iter().step_by(4).copied().collect();
            // RMS for level meter
            let rms = (chunk.iter().map(|s| s * s).sum::<f32>() / chunk.len() as f32).sqrt();

            let _ = app.emit("audio-chunk", serde_json::json!({
                "waveform": waveform,
                "rms": rms,
            }));
        }
    });

    // Keep stream alive — store in Tauri state, not a local variable
}
```

### FFT Spectrum (realfft)

```toml
# Cargo.toml
realfft = "3"
```

```rust
use realfft::RealFftPlanner;

fn compute_spectrum(samples: &[f32], fft_size: usize) -> Vec<f32> {
    let mut planner = RealFftPlanner::<f32>::new();
    let fft = planner.plan_fft_forward(fft_size);
    let mut input = samples[..fft_size].to_vec();
    // Apply Hann window
    for (i, s) in input.iter_mut().enumerate() {
        let w = 0.5 * (1.0 - (2.0 * std::f32::consts::PI * i as f32 / fft_size as f32).cos());
        *s *= w;
    }
    let mut spectrum = fft.make_output_vec();
    fft.process(&mut input, &mut spectrum).unwrap();
    spectrum.iter()
        .map(|c| 20.0 * ((c.re * c.re + c.im * c.im).sqrt() + 1e-10).log10())
        .collect()
}
```

---

## Section 5 — Tauri Integration

### State Management

```rust
use std::sync::Mutex;
use cpal::Stream;
use midir::{MidiInputConnection, MidiOutputConnection};

pub struct AudioState {
    pub input_stream: Mutex<Option<Stream>>,
    pub midi_in:      Mutex<Option<MidiInputConnection<()>>>,
    pub midi_out:     Mutex<Option<MidiOutputConnection>>,
}

pub fn run() {
    tauri::Builder::default()
        .manage(AudioState {
            input_stream: Mutex::new(None),
            midi_in:      Mutex::new(None),
            midi_out:     Mutex::new(None),
        })
        .invoke_handler(tauri::generate_handler![
            list_audio_input_devices,
            start_audio_capture,
            stop_audio_capture,
            list_midi_input_ports,
            list_midi_output_ports,
            connect_midi_input_cmd,
            connect_midi_output_cmd,
            midi_note_on,
            midi_note_off,
            midi_control_change,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[tauri::command]
async fn start_audio_capture(
    app: tauri::AppHandle,
    state: tauri::State<'_, AudioState>,
) -> Result<(), String> {
    let (producer, consumer) = HeapRb::<f32>::new(8192).split();
    let stream = build_capture_stream(producer)?;
    stream.play().map_err(|e| e.to_string())?;
    spawn_audio_emitter(app, consumer);
    *state.input_stream.lock().unwrap() = Some(stream);
    Ok(())
}

#[tauri::command]
fn stop_audio_capture(state: tauri::State<'_, AudioState>) {
    *state.input_stream.lock().unwrap() = None; // drop stops the stream
}
```

---

## Section 6 — Svelte Audio UI Patterns

### Level Meter (RMS → dB → visual bar)

```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { onDestroy } from 'svelte';

  let rms = $state(0);
  let dbLevel = $derived(20 * Math.log10(rms + 1e-10));
  let barPercent = $derived(Math.max(0, Math.min(100, (dbLevel + 60) / 60 * 100)));

  const unlisten = listen<{ rms: number }>('audio-chunk', (e) => {
    rms = e.payload.rms;
  });
  onDestroy(async () => (await unlisten)());
</script>

<div class="meter">
  <div class="fill" style="width: {barPercent}%"></div>
  <span>{dbLevel.toFixed(1)} dB</span>
</div>
```

### Waveform (Canvas + requestAnimationFrame)

```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { onMount, onDestroy } from 'svelte';

  let canvas: HTMLCanvasElement;
  let latestWaveform = new Float32Array(0);

  const unlisten = listen<{ waveform: number[] }>('audio-chunk', (e) => {
    latestWaveform = new Float32Array(e.payload.waveform);
  });

  onMount(() => {
    let animId: number;
    function draw() {
      const ctx = canvas.getContext('2d')!;
      const { width, height } = canvas;
      ctx.fillStyle = '#111827';
      ctx.fillRect(0, 0, width, height);
      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      const step = width / (latestWaveform.length || 1);
      latestWaveform.forEach((s, i) => {
        const x = i * step, y = (0.5 - s * 0.45) * height;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      });
      ctx.stroke();
      animId = requestAnimationFrame(draw);
    }
    animId = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animId);
  });

  onDestroy(async () => (await unlisten)());
</script>

<canvas bind:this={canvas} width={512} height={128}></canvas>
```

### MIDI Activity Indicator

```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { onDestroy } from 'svelte';

  let active = $state(false);
  let timer: ReturnType<typeof setTimeout>;

  const unlisten = listen('midi-in', () => {
    active = true;
    clearTimeout(timer);
    timer = setTimeout(() => { active = false; }, 120);
  });
  onDestroy(async () => (await unlisten)());
</script>

<div class="dot" class:active>MIDI</div>
```

### Virtual Keyboard (MIDI Note Output)

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  // C4–B4 = MIDI 60–71; white keys only for brevity
  const WHITE = [60, 62, 64, 65, 67, 69, 71];
  const LABELS = ['C','D','E','F','G','A','B'];
  let held = $state(new Set<number>());

  async function noteOn(n: number) {
    held = new Set([...held, n]);
    await invoke('midi_note_on', { channel: 1, note: n, velocity: 100 });
  }
  async function noteOff(n: number) {
    held = new Set([...held].filter(x => x !== n));
    await invoke('midi_note_off', { channel: 1, note: n });
  }
</script>

<div class="keys">
  {#each WHITE as note, i}
    <button class="key" class:held={held.has(note)}
      onpointerdown={() => noteOn(note)}
      onpointerup={() => noteOff(note)}
      onpointerleave={() => noteOff(note)}>
      {LABELS[i]}
    </button>
  {/each}
</div>
```

---

## Section 7 — Cross-Platform Notes

### Audio Backends

| Platform | Default Backend | Notes |
|----------|----------------|-------|
| Linux | ALSA | PulseAudio/PipeWire exposed via ALSA compat layer; cpal uses automatically |
| macOS | CoreAudio | Works out of the box; no extra deps |
| Windows | WASAPI | Default since Vista; shared mode (default) or exclusive mode (lowest latency) |

### MIDI Backends

| Platform | Backend |
|----------|---------|
| Linux | ALSA Sequencer — virtual ports supported, connect with `aconnect` |
| macOS | CoreMIDI — IAC driver for virtual ports |
| Windows | WinMM — legacy but universal |

### Permissions

- **Audio output**: No special permissions on any platform.
- **Audio input**: macOS requires `NSMicrophoneUsageDescription` in Info.plist + `com.apple.security.device.audio-input` entitlement. Linux and Windows: none.
- **MIDI**: No special permissions on any platform.

---

## Additional Resources

- [audio-reference.md](audio-reference.md) — Complete code examples: full cpal audio capture pipeline with multi-format support, cpal playback with atomic volume control, full midir MIDI input/output with message parsing, Svelte waveform/spectrum/level-meter components, MIDI device manager with port selector and message log, virtual piano keyboard, latency tradeoffs and audio callback rules
