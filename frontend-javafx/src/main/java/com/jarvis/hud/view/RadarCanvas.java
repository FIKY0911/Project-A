package com.jarvis.hud.view;

import javafx.animation.AnimationTimer;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.effect.DropShadow;
import javafx.scene.paint.Color;
import javafx.scene.paint.RadialGradient;
import javafx.scene.paint.CycleMethod;
import javafx.scene.paint.Stop;

public class RadarCanvas extends Canvas {
    private double sweepAngle = 0;

    private final AnimationTimer timer = new AnimationTimer() {
        private long last = 0;
        @Override
        public void handle(long now) {
            if (last == 0) { last = now; return; }
            double delta = (now - last) / 1_000_000_000.0;
            last = now;
            sweepAngle = (sweepAngle + 70 * delta) % 360;
            render();
        }
    };

    public RadarCanvas() {
        this(120, 120);
    }

    public RadarCanvas(double width, double height) {
        super(width, height);
        timer.start();
    }

    private void render() {
        double w = getWidth();
        double h = getHeight();
        if (w <= 0 || h <= 0) return;

        GraphicsContext gc = getGraphicsContext2D();
        gc.clearRect(0, 0, w, h);

        double cx = w / 2.0;
        double cy = h / 2.0;
        double r = Math.min(cx, cy) - 5;

        // Outer ring
        gc.setStroke(Color.web("#00d2ff", 0.7));
        gc.setLineWidth(1.5);
        gc.strokeOval(cx - r, cy - r, r * 2, r * 2);

        // Inner rings
        gc.setStroke(Color.web("#005577", 0.5));
        gc.strokeOval(cx - r * 0.66, cy - r * 0.66, r * 1.32, r * 1.32);
        gc.strokeOval(cx - r * 0.33, cy - r * 0.33, r * 0.66, r * 0.66);

        // Crosshairs
        gc.strokeLine(cx - r, cy, cx + r, cy);
        gc.strokeLine(cx, cy - r, cx, cy + r);

        // Sweep beam
        gc.save();
        gc.setStroke(Color.web("#00f0ff", 0.9));
        gc.setLineWidth(2.0);
        gc.setEffect(new DropShadow(6, Color.web("#00f0ff")));

        double rad = Math.toRadians(sweepAngle);
        double sx = cx + r * Math.cos(rad);
        double sy = cy + r * Math.sin(rad);
        gc.strokeLine(cx, cy, sx, sy);

        // Target blip
        gc.setFill(Color.web("#00ffaa"));
        gc.fillOval(cx + r * 0.45, cy - r * 0.35, 4, 4);
        gc.restore();
    }
}
