# LED Matrix Simulator (Processing)

A Processing template for designing visuals for a **64x32 RGB LED matrix**
(e.g. the [Adafruit 2278](https://www.adafruit.com/product/2278), 4mm pitch)
without needing the physical hardware, **mounted in portrait orientation**
(rotated 90° from the panel's native landscape wiring, so it reads as
32-wide x 64-tall). Draw at a comfortable 320x640 resolution using normal
Processing calls, and the sketch downsamples and renders it back as a grid
of round LEDs so you can see roughly how it'll look on the real panel.

![Example: two orbiting circles rendered as simulated LEDs](example.gif)

## Why this exists

Designing pixel art / animations directly at 32x64 is fiddly — shapes,
text, and curves all need to be figured out at a resolution too small to
work in comfortably. This template lets you draw at 320x640 (10x scale)
using the full Processing API (shapes, PImage, PFont, video, whatever you
like), and handles the downsampling and LED-style rendering for you.

## Requirements

- [Processing](https://processing.org/download) 4.x, Java mode (the default).
  No extra libraries required — everything here uses core Processing.

## Getting started

1. Clone or download this repo.
2. Open `LEDMatrixSim/LEDMatrixSim.pde` in the Processing IDE.
3. Press **Run**. You should see two overlapping circles orbiting the
   center, rendered as a grid of dots.
4. Press **`d`** to toggle between the simulated LED view and the raw
   320x640 canvas — handy for checking what you're actually drawing before
   it gets downsampled.

## How it works

```
drawVisual(canvas, t)     draw your visual at 320x640 into an offscreen PGraphics
        │
        ▼
   downsample()           average every 10x10 block down to one color (32x64 total)
        │
        ▼
   renderMatrix()          draw each of the 32x64 colors as a round "LED" with
                            a dark gap around it, mimicking the real panel
```

The only function you need to edit is `drawVisual()`. Everything else
(downsampling, LED rendering, the debug toggle) is infrastructure you
shouldn't need to touch.

```java
void drawVisual(PGraphics pg, float t) {
  pg.background(0);
  pg.noStroke();
  pg.fill(255);
  pg.ellipse(pg.width / 2, pg.height / 2, 80, 80);
}
```

- `pg` — the 320x640 offscreen canvas. Use the same drawing calls you'd use
  in a normal sketch, just prefixed with `pg.` (`pg.fill()`, `pg.rect()`,
  `pg.text()`, `pg.image()`, etc.)
- `t` — seconds elapsed since the sketch started (`frameCount / 60.0`),
  useful for animation.

**Always set fill/stroke explicitly** (`pg.fill(...)`, `pg.noStroke()`)
rather than relying on defaults — style state on an offscreen `PGraphics`
persists frame to frame, so an explicit call is the only reliable way to
know what you'll get.

## Matrix specs

| Setting        | Value |
|----------------|-------|
| Matrix size    | 32 x 64 LEDs (portrait, as mounted) |
| Canvas size    | 320 x 640 px |
| Scale factor   | 10 px per LED |
| Panel native wiring | 64 x 32 (unrotated HUB75 layout) |

These live as constants (`MATRIX_W`, `MATRIX_H`, `SCALE`) at the top of
`LEDMatrixSim.pde` if you're adapting this for a differently-sized panel —
just change them and everything downstream (canvas size, downsampling,
rendering) adjusts automatically.

`MATRIX_W`/`MATRIX_H` describe the panel **as mounted**, not its native
wiring — the panel itself is still 64 cols x 32 rows internally.
`pi/matrix_server.py` rotates each frame back to that native layout before
writing it out, so it's the one place that needs to know about both the
portrait and native orientations (see "Deploying to a Raspberry Pi"
below). If you're using a panel that's natively wired 32x64 instead of a
rotated 64x32, skip the rotation logic in `matrix_server.py` and set
`options.rows`/`options.cols` to match your panel directly.

## Tutorials

### 1. Static shapes

Draw anything you'd draw in a normal Processing sketch — it just needs the
`pg.` prefix:

```java
void drawVisual(PGraphics pg, float t) {
  pg.background(0);
  pg.noStroke();

  pg.fill(255, 0, 0);
  pg.rect(40, 40, 200, 200);

  pg.fill(0, 255, 0);
  pg.triangle(400, 60, 320, 260, 480, 260);
}
```

### 2. Simple animation

Use `t` to drive motion. Since `t` is in seconds, `sin(t)`/`cos(t)`
complete one cycle roughly every 6.3 seconds — multiply `t` to speed it up.

```java
void drawVisual(PGraphics pg, float t) {
  pg.background(0);
  pg.noStroke();
  pg.fill(255, 200, 0);

  float x = pg.width / 2 + cos(t * 2) * 250;
  float y = pg.height / 2 + sin(t * 2) * 120;
  pg.ellipse(x, y, 60, 60);
}
```

### 3. Text / scrolling marquee

Text is legible on a 32x64 matrix only in short bursts or scrolled — this
scrolls a message right to left.

```java
PFont font;

void settings() {
  size(CANVAS_W, CANVAS_H);
}

void setup() {
  pixelDensity(1);
  canvas = createGraphics(CANVAS_W, CANVAS_H);
  noStroke();
  font = createFont("Arial Bold", 200);
}

void drawVisual(PGraphics pg, float t) {
  pg.background(0);
  pg.fill(255);
  pg.textFont(font);
  pg.textAlign(LEFT, CENTER);

  float speed = 150; // px/sec
  float x = pg.width - (t * speed) % (pg.width + 800);
  pg.text("HELLO WORLD", x, pg.height / 2);
}
```

### 4. Using pixel/image data

Load a small image and draw it directly — since the canvas is 10x the
matrix resolution, a 32x64 source image can be drawn at 320x640 with
`pg.noSmooth()` for a crisp blocky look, or a larger image can be scaled
down for a smoother, anti-aliased result once downsampled.

```java
PImage img;

void settings() {
  size(CANVAS_W, CANVAS_H);
}

void setup() {
  pixelDensity(1);
  canvas = createGraphics(CANVAS_W, CANVAS_H);
  noStroke();
  img = loadImage("sprite.png"); // put sprite.png in the sketch's data/ folder
}

void drawVisual(PGraphics pg, float t) {
  pg.background(0);
  pg.image(img, 0, 0, pg.width, pg.height);
}
```


## Adapting for a different panel size

Editing the constants at the top of `LEDMatrixSim.pde` retargets the whole
template to a different matrix (e.g. a 32x32 panel):

```java
final int MATRIX_W = 32;
final int MATRIX_H = 32;
final int SCALE     = 10;
```

Canvas size, downsampling, and rendering all derive from these — no other
changes needed.

## Troubleshooting

**Sketch runs but the window is solid black.**
Make sure you're setting fill/stroke explicitly in `drawVisual()`
(`pg.fill(...)`, `pg.noStroke()`) rather than relying on defaults.

**Shapes appear torn or wrapped from one edge to the other.**
This is a Retina/HiDPI pixel-density mismatch — Processing's `pixels[]`
buffer can be `width*2` px wide on high-DPI displays even though `width`
still reports the logical size, which breaks the downsampling math. Make
sure `pixelDensity(1);` is called in `setup()` right after `size()` (it's
included by default in this template).

## Deploying to a Raspberry Pi + physical matrix

Processing can't drive the matrix's GPIO timing directly — that requires
[rpi-rgb-led-matrix](https://github.com/hzeller/rpi-rgb-led-matrix), a C++
library built for exactly this. The setup: the Processing sketch keeps
running unchanged (same `drawVisual()`, still shows the simulator), and
streams each downsampled 32x64 portrait frame over a local TCP socket to a
small Python daemon (`pi/matrix_server.py`) that rotates it back to the
panel's native 64x32 layout and pushes it out.

Requires the [Adafruit RGB Matrix Bonnet/HAT](https://www.adafruit.com/product/3211)
wired to the panel.

**1. On the Pi, install rpi-rgb-led-matrix and its Python bindings:**

```bash
sudo apt-get update && sudo apt-get install -y python3-dev cython3 build-essential
git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
cd rpi-rgb-led-matrix
make build-python PYTHON=$(which python3)
sudo make install-python PYTHON=$(which python3)
```

**2. Disable onboard audio** — it uses the same PWM hardware the matrix
library needs. Add to `/boot/firmware/config.txt` (or `/boot/config.txt`
on older OS versions):

```
dtparam=audio=off
```

Reboot after this change.

**3. Copy this repo to the Pi** (or `git clone` it there), then start the
receiver — it must be running *before* the Processing sketch, and needs
root for GPIO access:

```bash
cd led-matrix-simulator/pi
sudo python3 matrix_server.py
```

**4. In `LEDMatrixSim.pde`, set `SEND_TO_HARDWARE = true`**, then run the
sketch as usual (Processing IDE, or `processing-java --sketch=$(pwd)/LEDMatrixSim --run`
if running headless over SSH with a display available, e.g. via VNC).

You should now see the same visual on-screen in the simulator window and
on the physical matrix simultaneously — useful for spotting any mismatch
between the simulation and the real panel.

**Troubleshooting:**
- *Flickering/glitching on the panel:* raise `gpio_slowdown` in
  `matrix_server.py` (try 3 or 4).
- *Dim or slightly banded colors:* try `hardware_mapping = "adafruit-hat-pwm"`
  instead of `"adafruit-hat"` — only if you've done the hardware PWM
  mod described in the rpi-rgb-led-matrix docs.
- *Sketch can't connect / nothing shows on the panel:* confirm
  `matrix_server.py` is running and printed "Waiting for Processing
  sketch..." before you start the sketch, and that `SEND_TO_HARDWARE` is
  `true`.
- *Image on the panel is upside-down or mirrored:* the panel is mounted
  rotated the opposite way from what `matrix_server.py` assumes — flip
  `ROTATE_CW` at the top of that file and restart it.

## License

GPLv3 — see [LICENSE](LICENSE). You're free to use, modify, and share this,
but derivative works must also be open-sourced under GPLv3.
