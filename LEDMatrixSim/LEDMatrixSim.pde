// LED Matrix Simulator — Adafruit 2278 (64x32 RGB matrix, 4mm pitch)
//
// Draw your visuals at full resolution into `canvas` (640x320) using any
// standard Processing drawing calls, exactly as if it were the main window.
// Every frame this gets block-averaged down to 64x32 and rendered back out
// as a grid of round LEDs with dark gaps, approximating how it'll look on
// the real panel.
//
// All the visual work happens in drawVisual() near the bottom — that's the
// only function you should need to touch when designing a new animation.
//
// To drive a real HUB75 matrix (e.g. on a Raspberry Pi via the Adafruit
// RGB Matrix Bonnet/HAT), set SEND_TO_HARDWARE = true. Each frame's 64x32
// pixels get streamed over a local TCP socket to a receiver process using
// the rpi-rgb-led-matrix library — see pi/matrix_server.py and the
// "Deploying to a Raspberry Pi" section in README.md. Processing itself
// can't drive the panel's GPIO timing directly, so this hand-off is
// required either way.

import processing.net.*;

// ---- Matrix / canvas configuration ----
final int MATRIX_W = 64;
final int MATRIX_H = 32;
final int SCALE     = 10;                 // pixels per LED, both axes
final int CANVAS_W  = MATRIX_W * SCALE;   // 640
final int CANVAS_H  = MATRIX_H * SCALE;   // 320
final float LED_DIAMETER = SCALE * 0.75;  // leaves a gap so LEDs read as dots

// ---- Hardware output (Raspberry Pi + physical matrix) ----
final boolean SEND_TO_HARDWARE = false;    // set true when running on the Pi
final String  MATRIX_HOST      = "127.0.0.1";
final int     MATRIX_PORT      = 7890;
Client matrixClient;

PGraphics canvas;
color[] ledColors = new color[MATRIX_W * MATRIX_H];
boolean showRawCanvas = false; // press 'd' to toggle

void setup() {
  size(640, 320);
  pixelDensity(1); // force 1:1 pixel buffer; Retina displays otherwise
                    // double the pixels[] row stride and break downsample()
  canvas = createGraphics(CANVAS_W, CANVAS_H);
  noStroke();
  if (SEND_TO_HARDWARE) connectToMatrixServer();
}

void draw() {
  // 1. Render this frame's visual at full resolution.
  canvas.beginDraw();
  drawVisual(canvas, frameCount / 60.0);
  canvas.endDraw();

  if (showRawCanvas) {
    image(canvas, 0, 0);
    return;
  }

  // 2. Downsample 640x320 -> 64x32 by averaging each 10x10 block.
  downsample(canvas, ledColors);

  // 3. Render the simulated matrix (round LEDs + gaps) to the window.
  background(0);
  renderMatrix(ledColors);

  // 4. Optionally mirror the same frame to a physical matrix.
  if (SEND_TO_HARDWARE) sendFrameToHardware();
}

void keyPressed() {
  if (key == 'd' || key == 'D') {
    showRawCanvas = !showRawCanvas;
  }
}

void connectToMatrixServer() {
  matrixClient = new Client(this, MATRIX_HOST, MATRIX_PORT);
}

// Streams the current 64x32 frame as raw RGB bytes (no framing needed —
// matrix_server.py just reads MATRIX_W*MATRIX_H*3 bytes per frame).
void sendFrameToHardware() {
  if (matrixClient == null || !matrixClient.active()) {
    connectToMatrixServer();
    if (matrixClient == null || !matrixClient.active()) return;
  }
  byte[] frame = new byte[MATRIX_W * MATRIX_H * 3];
  int i = 0;
  for (int p = 0; p < ledColors.length; p++) {
    color c = ledColors[p];
    frame[i++] = (byte) ((c >> 16) & 0xFF);
    frame[i++] = (byte) ((c >> 8) & 0xFF);
    frame[i++] = (byte) (c & 0xFF);
  }
  matrixClient.write(frame);
}

// Averages each SCALE x SCALE block of `src` into one color per LED.
void downsample(PGraphics src, color[] outColors) {
  src.loadPixels();
  for (int my = 0; my < MATRIX_H; my++) {
    for (int mx = 0; mx < MATRIX_W; mx++) {
      long rSum = 0, gSum = 0, bSum = 0;
      int startX = mx * SCALE;
      int startY = my * SCALE;
      for (int y = 0; y < SCALE; y++) {
        int rowOffset = (startY + y) * CANVAS_W + startX;
        for (int x = 0; x < SCALE; x++) {
          color c = src.pixels[rowOffset + x];
          rSum += (c >> 16) & 0xFF;
          gSum += (c >> 8) & 0xFF;
          bSum += c & 0xFF;
        }
      }
      int n = SCALE * SCALE;
      outColors[my * MATRIX_W + mx] = color(rSum / n, gSum / n, bSum / n);
    }
  }
}

// Draws the downsampled colors as a grid of round LEDs with dark gaps
// between them, standing in for the physical panel's pixel pitch.
void renderMatrix(color[] colors) {
  for (int my = 0; my < MATRIX_H; my++) {
    for (int mx = 0; mx < MATRIX_W; mx++) {
      float cx = mx * SCALE + SCALE / 2.0;
      float cy = my * SCALE + SCALE / 2.0;
      fill(colors[my * MATRIX_W + mx]);
      ellipse(cx, cy, LED_DIAMETER, LED_DIAMETER);
    }
  }
}

// ---- Your visual goes here ----
// `pg` is the 640x320 canvas — draw into it with pg.background(), pg.fill(),
// pg.ellipse(), pg.rect(), etc. (same API as the main sketch, just prefixed).
// `t` is seconds elapsed, handy for animation.
void drawVisual(PGraphics pg, float t) {
  pg.background(0);

  float x = pg.width / 2.0 + cos(t) * 200;
  float y = pg.height / 2.0 + sin(t * 1.3) * 100;

  pg.fill(255, 80, 80);
  pg.ellipse(x, y, 120, 120);

  pg.fill(80, 160, 255);
  pg.ellipse(pg.width - x, pg.height - y, 80, 80);
}
