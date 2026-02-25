# Audio / MIDI Devices — Complete Reference

Detailed code examples for the `frontend-svelte-knowledge:audio-midi-devices` skill. Each section is self-contained.

---

## Section 1 — Complete cpal Audio Capture Pipeline

Full example: enumerate devices, select by name or default, stream samples through a ring buffer, emit chunks to the frontend at 30 fps.

### Cargo.toml

```toml
[dependencies]
cpal = "0.15"
ringbuf = "0.4"
tauri = { version = "2", features = ["default"] }
tokio = { version = "1", features = ["full"] }
serde_json = "1"
```

### lib.rs — Audio State + Commands

```rust
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, Stream};
use ringbuf::{HeapRb, traits::Split};
use std::sync::Mutex;
use tauri::{AppHandle, Emitter, State};

pub struct AudioCaptureState {
    pub stream: Mutex<Option<Stream>>,
}

// Build capture stream for a named device (or default if name is empty)
fn build_capture_stream(
    device_name: &str,
    producer: ringbuf::HeapProd<f32>,
) -> Result<Stream, String> {
    let host = cpal::default_host();
    let device = if device_name.is_empty() {
        host.default_input_device().ok_or("No default input device")?
    } else {
        host.input_devices()
            .map_err(|e| e.to_string())?
            .find(|d| d.name().as_deref() == Ok(device_name))
            .ok_or_else(|| format!("Device '{}' not found", device_name))?
    };

    let config = device.default_input_config().map_err(|e| e.to_string())?;
    let mut prod = producer;

    let stream = match config.sample_format() {
        SampleFormat::F32 => device.build_input_stream(
            &config.into(),
            move |data: &[f32], _| {
                for &s in data {
                    let _ = prod.try_push(s);
                }
            },
            |err| eprintln!("Input stream error: {err}"),
            None,
        ),
        SampleFormat::I16 => device.build_input_stream(
            &config.into(),
            move |data: &[i16], _| {
                for &s in data {
                    let _ = prod.try_push(s as f32 / i16::MAX as f32);
                }
            },
            |err| eprintln!("Input stream error: {err}"),
            None,
        ),
        SampleFormat::U16 => device.build_input_stream(
            &config.into(),
            move |data: &[u16], _| {
                for &s in data {
                    let _ = prod.try_push((s as f32 / u16::MAX as f32) * 2.0 - 1.0);
                }
            },
            |err| eprintln!("Input stream error: {err}"),
            None,
        ),
        f => return Err(format!("Unsupported sample format: {:?}", f)),
    };

    stream.map_err(|e| e.to_string())
}

// Background task: reads ring buffer, emits chunks at ~30 fps
fn spawn_audio_emitter(app: AppHandle, mut consumer: ringbuf::HeapCons<f32>) {
    tokio::spawn(async move {
        let mut interval = tokio::time::interval(
            std::time::Duration::from_millis(33), // ~30 fps
        );
        loop {
            interval.tick().await;

            let mut chunk: Vec<f32> = Vec::with_capacity(2048);
            while let Some(s) = consumer.try_pop() {
                chunk.push(s);
                if chunk.len() >= 2048 { break; }
            }

            if chunk.is_empty() { continue; }

            // Downsample by 4× for waveform (reduces bandwidth)
            let waveform: Vec<f32> = chunk.iter().step_by(4).copied().collect();

            // RMS level
            let rms = (chunk.iter().map(|s| s * s).sum::<f32>() / chunk.len() as f32).sqrt();

            // Peak
            let peak = chunk.iter().cloned().fold(0.0_f32, f32::max);

            let _ = app.emit("audio-chunk", serde_json::json!({
                "waveform": waveform,
                "rms": rms,
                "peak": peak,
                "samples": chunk.len(),
            }));
        }
    });
}

#[tauri::command]
pub async fn start_audio_capture(
    app: AppHandle,
    state: State<'_, AudioCaptureState>,
    device_name: String,
) -> Result<(), String> {
    // Stop existing stream first
    *state.stream.lock().unwrap() = None;

    let (producer, consumer) = HeapRb::<f32>::new(8192).split();
    let stream = build_capture_stream(&device_name, producer)?;
    stream.play().map_err(|e| e.to_string())?;

    spawn_audio_emitter(app, consumer);
    *state.stream.lock().unwrap() = Some(stream);
    Ok(())
}

#[tauri::command]
pub fn stop_audio_capture(state: State<'_, AudioCaptureState>) {
    *state.stream.lock().unwrap() = None;
}

#[tauri::command]
pub fn list_audio_input_devices() -> Result<Vec<String>, String> {
    let host = cpal::default_host();
    let devices = host.input_devices().map_err(|e| e.to_string())?;
    Ok(devices
        .filter_map(|d| d.name().ok())
        .collect())
}
```

---

## Section 2 — Complete cpal Audio Playback

Select output device, stream output from a buffer, sine wave generation, atomic volume control.

```rust
use cpal::traits::{DeviceTrait, HostTrait, StreamTrait};
use cpal::{SampleFormat, Stream, StreamConfig};
use std::sync::atomic::{AtomicU32, Ordering};
use std::sync::Arc;

pub struct PlaybackState {
    pub stream: Mutex<Option<Stream>>,
    pub volume: Arc<AtomicU32>, // stored as f32 bits
}

fn atomic_f32_load(a: &AtomicU32) -> f32 {
    f32::from_bits(a.load(Ordering::Relaxed))
}

fn atomic_f32_store(a: &AtomicU32, v: f32) {
    a.store(v.to_bits(), Ordering::Relaxed);
}

// Build a sine wave playback stream
fn build_sine_stream(
    freq_hz: f32,
    volume: Arc<AtomicU32>,
) -> Result<Stream, String> {
    let host = cpal::default_host();
    let device = host.default_output_device().ok_or("No output device")?;
    let config = device.default_output_config().map_err(|e| e.to_string())?;
    let sample_rate = config.sample_rate().0 as f32;
    let channels = config.channels() as usize;

    let mut phase: f32 = 0.0;
    let phase_step = freq_hz / sample_rate;

    let stream = match config.sample_format() {
        SampleFormat::F32 => device.build_output_stream(
            &config.into(),
            move |data: &mut [f32], _| {
                let vol = atomic_f32_load(&volume);
                for frame in data.chunks_mut(channels) {
                    let sample = (phase * std::f32::consts::TAU).sin() * vol;
                    phase = (phase + phase_step) % 1.0;
                    for ch in frame.iter_mut() { *ch = sample; }
                }
            },
            |err| eprintln!("Output error: {err}"),
            None,
        ),
        _ => return Err("Unsupported output format".into()),
    };

    stream.map_err(|e| e.to_string())
}

#[tauri::command]
pub fn start_playback(
    state: State<'_, PlaybackState>,
    freq_hz: f32,
) -> Result<(), String> {
    let vol = Arc::clone(&state.volume);
    let stream = build_sine_stream(freq_hz, vol)?;
    stream.play().map_err(|e| e.to_string())?;
    *state.stream.lock().unwrap() = Some(stream);
    Ok(())
}

#[tauri::command]
pub fn set_volume(state: State<'_, PlaybackState>, volume: f32) {
    atomic_f32_store(&state.volume, volume.clamp(0.0, 1.0));
}

#[tauri::command]
pub fn stop_playback(state: State<'_, PlaybackState>) {
    *state.stream.lock().unwrap() = None;
}
```

---

## Section 3 — Complete midir MIDI Input

Full pipeline: create MidiInput, list ports, connect with callback, forward messages to frontend.

```rust
use midir::{MidiInput, MidiInputConnection};
use tauri::{AppHandle, Emitter};
use std::sync::Mutex;

pub struct MidiInState {
    pub connection: Mutex<Option<MidiInputConnection<()>>>,
}

#[tauri::command]
pub fn list_midi_input_ports() -> Result<Vec<String>, String> {
    let input = MidiInput::new("tauri-app").map_err(|e| e.to_string())?;
    input.ports().iter()
        .map(|p| input.port_name(p).map_err(|e| e.to_string()))
        .collect()
}

#[tauri::command]
pub fn connect_midi_input(
    app: AppHandle,
    state: State<'_, MidiInState>,
    port_name: String,
) -> Result<(), String> {
    // Close existing connection
    *state.connection.lock().unwrap() = None;

    let input = MidiInput::new("tauri-app").map_err(|e| e.to_string())?;
    let port = input.ports().into_iter()
        .find(|p| input.port_name(p).as_deref() == Ok(&port_name))
        .ok_or_else(|| format!("MIDI input port '{}' not found", port_name))?;

    let conn = input.connect(
        &port,
        "tauri-midi-in",
        move |timestamp_us, message, _| {
            if message.is_empty() { return; }

            let status = message[0];
            let channel = (status & 0x0F) + 1;
            let msg_type = match status & 0xF0 {
                0x80 => "note-off",
                0x90 => if message.get(2).copied().unwrap_or(0) > 0 { "note-on" } else { "note-off" },
                0xA0 => "aftertouch",
                0xB0 => "control-change",
                0xC0 => "program-change",
                0xD0 => "channel-pressure",
                0xE0 => "pitch-bend",
                0xF0 => "sysex",
                _    => "unknown",
            };

            let note = message.get(1).copied().unwrap_or(0);
            let value = message.get(2).copied().unwrap_or(0);

            let _ = app.emit("midi-in", serde_json::json!({
                "timestamp_us": timestamp_us,
                "type": msg_type,
                "channel": channel,
                "note": note,
                "value": value,
                "raw": message.to_vec(),
            }));
        },
        (),
    ).map_err(|e| e.to_string())?;

    *state.connection.lock().unwrap() = Some(conn);
    Ok(())
}

#[tauri::command]
pub fn disconnect_midi_input(state: State<'_, MidiInState>) {
    *state.connection.lock().unwrap() = None;
}
```

---

## Section 4 — Complete midir MIDI Output

Full pipeline: create MidiOutput, list ports, connect, send note sequences and CC.

```rust
use midir::{MidiOutput, MidiOutputConnection};
use std::sync::Mutex;
use tauri::State;

pub struct MidiOutState {
    pub connection: Mutex<Option<MidiOutputConnection>>,
}

#[tauri::command]
pub fn list_midi_output_ports() -> Result<Vec<String>, String> {
    let output = MidiOutput::new("tauri-app").map_err(|e| e.to_string())?;
    output.ports().iter()
        .map(|p| output.port_name(p).map_err(|e| e.to_string()))
        .collect()
}

#[tauri::command]
pub fn connect_midi_output(
    state: State<'_, MidiOutState>,
    port_name: String,
) -> Result<(), String> {
    *state.connection.lock().unwrap() = None;

    let output = MidiOutput::new("tauri-app").map_err(|e| e.to_string())?;
    let port = output.ports().into_iter()
        .find(|p| output.port_name(p).as_deref() == Ok(&port_name))
        .ok_or_else(|| format!("MIDI output port '{}' not found", port_name))?;

    let conn = output.connect(&port, "tauri-midi-out")
        .map_err(|e| e.to_string())?;

    *state.connection.lock().unwrap() = Some(conn);
    Ok(())
}

#[tauri::command]
pub fn midi_note_on(
    state: State<'_, MidiOutState>,
    channel: u8,
    note: u8,
    velocity: u8,
) -> Result<(), String> {
    let mut guard = state.connection.lock().unwrap();
    let conn = guard.as_mut().ok_or("MIDI output not connected")?;
    conn.send(&[0x90 | (channel.saturating_sub(1) & 0x0F), note, velocity])
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn midi_note_off(
    state: State<'_, MidiOutState>,
    channel: u8,
    note: u8,
) -> Result<(), String> {
    let mut guard = state.connection.lock().unwrap();
    let conn = guard.as_mut().ok_or("MIDI output not connected")?;
    conn.send(&[0x80 | (channel.saturating_sub(1) & 0x0F), note, 0])
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub fn midi_control_change(
    state: State<'_, MidiOutState>,
    channel: u8,
    cc: u8,
    value: u8,
) -> Result<(), String> {
    let mut guard = state.connection.lock().unwrap();
    let conn = guard.as_mut().ok_or("MIDI output not connected")?;
    conn.send(&[0xB0 | (channel.saturating_sub(1) & 0x0F), cc, value])
        .map_err(|e| e.to_string())
}

// Play a note for a fixed duration (blocks the thread — use sparingly)
pub fn play_note_blocking(
    conn: &mut MidiOutputConnection,
    channel: u8,
    note: u8,
    velocity: u8,
    duration_ms: u64,
) {
    let ch = channel.saturating_sub(1) & 0x0F;
    conn.send(&[0x90 | ch, note, velocity]).unwrap();
    std::thread::sleep(std::time::Duration::from_millis(duration_ms));
    conn.send(&[0x80 | ch, note, 0]).unwrap();
}

// Timing note: midir MIDI output has no built-in scheduling.
// For precise timing, use a dedicated thread with std::thread::sleep or
// a high-resolution timer. tokio::time::sleep is NOT suitable for sub-ms timing.
```

---

## Section 5 — Svelte Audio Visualization

### Canvas Waveform Renderer

Subscribes to `audio-chunk` events, renders waveform using requestAnimationFrame. Decouples event receipt from draw calls to avoid dropped frames.

```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { onMount, onDestroy } from 'svelte';

  let canvas: HTMLCanvasElement;
  // Double-buffer: event listener writes, rAF reads
  let latestWaveform: Float32Array = new Float32Array(0);

  const unlisten = listen<{ waveform: number[] }>('audio-chunk', (e) => {
    latestWaveform = new Float32Array(e.payload.waveform);
  });

  onMount(() => {
    let animId: number;

    function draw() {
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      const { width, height } = canvas;
      const data = latestWaveform;

      ctx.fillStyle = '#111827';
      ctx.fillRect(0, 0, width, height);

      if (data.length === 0) {
        animId = requestAnimationFrame(draw);
        return;
      }

      // Centre line
      ctx.strokeStyle = '#374151';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(0, height / 2);
      ctx.lineTo(width, height / 2);
      ctx.stroke();

      // Waveform
      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      const step = width / data.length;
      for (let i = 0; i < data.length; i++) {
        const x = i * step;
        const y = (0.5 - data[i] * 0.48) * height;
        i === 0 ? ctx.moveTo(x, y) : ctx.lineTo(x, y);
      }
      ctx.stroke();

      animId = requestAnimationFrame(draw);
    }

    animId = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animId);
  });

  onDestroy(async () => (await unlisten)());
</script>

<canvas bind:this={canvas} width={640} height={160} class="waveform"></canvas>

<style>
  .waveform { display: block; border-radius: 4px; }
</style>
```

### Level Meter Component

```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { onDestroy } from 'svelte';

  let { label = 'IN' }: { label?: string } = $props();

  let rms = $state(0);
  let peak = $state(0);

  // Convert linear amplitude to dBFS
  const toDb = (v: number) => 20 * Math.log10(Math.max(v, 1e-10));
  // Map -60..0 dB → 0..100%
  const toPercent = (db: number) => Math.max(0, Math.min(100, (db + 60) / 60 * 100));

  let rmsDb = $derived(toDb(rms));
  let peakDb = $derived(toDb(peak));
  let rmsBar = $derived(toPercent(rmsDb));
  let peakBar = $derived(toPercent(peakDb));

  const unlisten = listen<{ rms: number; peak: number }>('audio-chunk', (e) => {
    rms = e.payload.rms;
    // Slow peak decay
    if (e.payload.peak > peak) peak = e.payload.peak;
    else peak *= 0.97;
  });

  onDestroy(async () => (await unlisten)());
</script>

<div class="meter-wrap">
  <span class="label">{label}</span>
  <div class="track">
    <div class="fill rms" style="width: {rmsBar}%"></div>
    <div class="peak-marker" style="left: {peakBar}%"></div>
  </div>
  <span class="db">{rmsDb.toFixed(1)} dB</span>
</div>

<style>
  .meter-wrap { display: flex; align-items: center; gap: 8px; }
  .label { font-size: 11px; color: #9ca3af; width: 24px; }
  .track { flex: 1; height: 12px; background: #1f2937; border-radius: 2px; position: relative; }
  .fill { height: 100%; border-radius: 2px; background: linear-gradient(to right, #4ade80, #facc15, #f87171); }
  .peak-marker { position: absolute; top: 0; width: 2px; height: 100%; background: #f87171; transform: translateX(-1px); }
  .db { font-size: 11px; color: #6b7280; width: 56px; text-align: right; }
</style>
```

### Frequency Spectrum (FFT data)

```svelte
<script lang="ts">
  import { listen } from '@tauri-apps/api/event';
  import { onMount, onDestroy } from 'svelte';

  let canvas: HTMLCanvasElement;
  let spectrum: number[] = [];

  // Rust must emit 'audio-spectrum' event with { bins: number[] } (dB values)
  const unlisten = listen<{ bins: number[] }>('audio-spectrum', (e) => {
    spectrum = e.payload.bins;
  });

  onMount(() => {
    let animId: number;
    function draw() {
      if (!canvas) { animId = requestAnimationFrame(draw); return; }
      const ctx = canvas.getContext('2d')!;
      const { width, height } = canvas;
      ctx.fillStyle = '#111827';
      ctx.fillRect(0, 0, width, height);

      if (spectrum.length > 0) {
        const barW = width / spectrum.length;
        spectrum.forEach((db, i) => {
          // db is typically -80..0; map to 0..1
          const norm = Math.max(0, (db + 80) / 80);
          const barH = norm * height;
          const hue = 200 + norm * 160; // blue → green → yellow
          ctx.fillStyle = `hsl(${hue}, 90%, 55%)`;
          ctx.fillRect(i * barW, height - barH, barW - 1, barH);
        });
      }

      animId = requestAnimationFrame(draw);
    }
    animId = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animId);
  });

  onDestroy(async () => (await unlisten)());
</script>

<canvas bind:this={canvas} width={512} height={128}></canvas>
```

---

## Section 6 — Svelte MIDI Device Manager

### Port Selector + MIDI Log

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';
  import { listen } from '@tauri-apps/api/event';
  import { onDestroy } from 'svelte';

  interface MidiMessage {
    timestamp_us: number;
    type: string;
    channel: number;
    note: number;
    value: number;
    raw: number[];
  }

  let inputPorts = $state<string[]>([]);
  let outputPorts = $state<string[]>([]);
  let selectedInput = $state('');
  let selectedOutput = $state('');
  let messages = $state<MidiMessage[]>([]);
  let connected = $state(false);

  async function loadPorts() {
    inputPorts = await invoke<string[]>('list_midi_input_ports');
    outputPorts = await invoke<string[]>('list_midi_output_ports');
  }

  async function connectInput() {
    await invoke('connect_midi_input', { portName: selectedInput });
    connected = true;
  }

  async function connectOutput() {
    await invoke('connect_midi_output', { portName: selectedOutput });
  }

  function noteLabel(note: number) {
    const names = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];
    return `${names[note % 12]}${Math.floor(note / 12) - 1}`;
  }

  function formatMessage(m: MidiMessage) {
    const hex = m.raw.map(b => b.toString(16).padStart(2, '0').toUpperCase()).join(' ');
    let detail = '';
    if (m.type === 'note-on' || m.type === 'note-off') {
      detail = ` ${noteLabel(m.note)} vel=${m.value}`;
    } else if (m.type === 'control-change') {
      detail = ` CC${m.note}=${m.value}`;
    }
    return `[${m.type}] ch${m.channel}${detail} | ${hex}`;
  }

  const unlisten = listen<MidiMessage>('midi-in', (e) => {
    messages = [e.payload, ...messages].slice(0, 200); // keep last 200
  });

  onDestroy(async () => (await unlisten)());
  loadPorts();
</script>

<div class="midi-manager">
  <div class="ports">
    <div class="port-row">
      <select bind:value={selectedInput}>
        <option value="">-- Select MIDI Input --</option>
        {#each inputPorts as port}
          <option value={port}>{port}</option>
        {/each}
      </select>
      <button onclick={connectInput} disabled={!selectedInput}>Connect</button>
      {#if connected}<span class="dot active"></span>{/if}
    </div>
    <div class="port-row">
      <select bind:value={selectedOutput}>
        <option value="">-- Select MIDI Output --</option>
        {#each outputPorts as port}
          <option value={port}>{port}</option>
        {/each}
      </select>
      <button onclick={connectOutput} disabled={!selectedOutput}>Connect</button>
    </div>
    <button onclick={loadPorts} class="refresh">Refresh Ports</button>
  </div>

  <div class="log">
    {#each messages as msg}
      <div class="msg-row" class:note-on={msg.type === 'note-on'}>
        {formatMessage(msg)}
      </div>
    {/each}
  </div>
</div>
```

### Virtual Piano Keyboard (MIDI Output)

```svelte
<script lang="ts">
  import { invoke } from '@tauri-apps/api/core';

  let { channel = 1, velocity = 100 }: { channel?: number; velocity?: number } = $props();

  // One octave (C4–B4 = MIDI 60–71)
  const WHITE_KEYS = [60, 62, 64, 65, 67, 69, 71];  // C D E F G A B
  const BLACK_KEYS = [61, 63, null, 66, 68, 70, null]; // C# D# _ F# G# A# _
  const NOTE_NAMES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'];

  let heldNotes = $state<Set<number>>(new Set());

  async function noteOn(note: number) {
    if (heldNotes.has(note)) return;
    heldNotes = new Set([...heldNotes, note]);
    await invoke('midi_note_on', { channel, note, velocity });
  }

  async function noteOff(note: number) {
    heldNotes = new Set([...heldNotes].filter(n => n !== note));
    await invoke('midi_note_off', { channel, note });
  }
</script>

<div class="keyboard">
  {#each WHITE_KEYS as note, i}
    <button
      class="white-key"
      class:held={heldNotes.has(note)}
      onpointerdown={() => noteOn(note)}
      onpointerup={() => noteOff(note)}
      onpointerleave={() => noteOff(note)}
    >
      <span class="key-label">{NOTE_NAMES[note % 12]}</span>
      {#if BLACK_KEYS[i] !== null}
        <button
          class="black-key"
          class:held={heldNotes.has(BLACK_KEYS[i]!)}
          onpointerdown|stopPropagation={() => noteOn(BLACK_KEYS[i]!)}
          onpointerup|stopPropagation={() => noteOff(BLACK_KEYS[i]!)}
          onpointerleave|stopPropagation={() => noteOff(BLACK_KEYS[i]!)}
        ></button>
      {/if}
    </button>
  {/each}
</div>

<style>
  .keyboard { display: flex; height: 120px; user-select: none; }
  .white-key {
    position: relative; flex: 1; background: white; border: 1px solid #9ca3af;
    border-top: none; display: flex; align-items: flex-end; justify-content: center;
    padding-bottom: 6px; cursor: pointer;
  }
  .white-key.held { background: #bfdbfe; }
  .black-key {
    position: absolute; top: -1px; right: -18px; width: 28px; height: 70px;
    background: #1f2937; z-index: 2; cursor: pointer; border: none;
    border-radius: 0 0 3px 3px;
  }
  .black-key.held { background: #3b82f6; }
  .key-label { font-size: 10px; color: #6b7280; pointer-events: none; }
</style>
```

---

## Section 7 — Latency Considerations

### Buffer Size Tradeoffs

| Buffer Size | Latency | CPU Load | Risk |
|-------------|---------|----------|------|
| 64 samples | ~1.5 ms at 44.1 kHz | High | Dropouts on load spikes |
| 256 samples | ~6 ms at 44.1 kHz | Moderate | Good for most use cases |
| 512 samples | ~12 ms at 44.1 kHz | Low | Safe for all platforms |
| 1024+ samples | 23+ ms | Very low | Noticeable for real-time monitoring |

cpal's `StreamConfig` accepts a `buffer_size` hint via `cpal::BufferSize::Fixed(n)` or `Default`. Not all backends respect it.

```rust
use cpal::{BufferSize, StreamConfig, SampleRate};

let config = StreamConfig {
    channels: 2,
    sample_rate: SampleRate(44_100),
    buffer_size: BufferSize::Fixed(256), // hint — may not be honoured
};
```

### Audio Callback Rules (Critical)

The audio callback runs on a real-time OS thread. Violating these rules causes clicks, pops, or dropouts:

```rust
// NEVER do this in the audio callback:
// vec.push(x)        — heap allocation
// Mutex::lock()      — may block
// String::new()      — heap allocation
// println!()         — syscall
// app.emit()         — async, not real-time safe
// std::fs::read()    — I/O

// DO this instead:
// ringbuf producer.try_push(x)  — lock-free, non-blocking
// atomic loads/stores            — always real-time safe
// stack-allocated arrays         — fine
```

### Ring Buffer Sizing

Size the ring buffer to hold at least 3 callback durations to absorb scheduling jitter:

```
ring_buffer_samples = callback_frames * 3 * channels
// For 256-frame stereo buffer: 256 * 3 * 2 = 1536 samples minimum
// In practice, use 4096–8192 for safety
```

### Real-Time Thread Priority

cpal does not expose thread priority controls. On Linux, the audio thread may be elevated automatically by PulseAudio/PipeWire if the process is in the `audio` group. On macOS, CoreAudio sets thread priority automatically. On Windows, WASAPI exclusive mode uses a real-time thread. If ultra-low latency is critical, consider a dedicated audio process communicating via shared memory.
