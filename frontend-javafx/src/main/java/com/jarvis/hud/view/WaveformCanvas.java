package com.jarvis.hud.view;

import javafx.animation.AnimationTimer;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.effect.DropShadow;
import javafx.scene.paint.Color;

public class WaveformCanvas extends Canvas {
    private double phase = 0;
    private boolean isListening = true;

    private final AnimationTimer timer = new AnimationTimer() {
        private long last = 0;
        @Override
        public void handle(long now) {
            if (last == 0) { last = now; return; }
            double delta = (now - last) / 1_000_000_000.0;
            last = now;
            phase += 4.0 * delta;
            render();
        }
    };

    public WaveformCanvas() {
        this(260, 60);
    }

    public WaveformCanvas(double width, double height) {
        super(width, height);
        timer.start();
    }

    public void setListening(boolean listening) {
        this.isListening = listening;
    }

    private void render() {
        double w = getWidth();
        double h = getHeight();
        if (w <= 0 || h <= 0) return;

        GraphicsContext gc = getGraphicsContext2D();
        gc.clearRect(0, 0, w, h);

        double cy = h / 2.0;
        int bars = 36;
        double barWidth = 3.0;
        double spacing = (w - (bars * barWidth)) / (bars - 1);

        gc.setFill(Color.web("#00f0ff"));
        gc.setEffect(new DropShadow(5, Color.web("#00f0ff")));

        for (int i = 0; i < bars; i++) {
            double x = i * (barWidth + spacing);
            double distFromCenter = Math.abs((bars / 2.0) - i) / (bars / 2.0);
            double envelope = Math.max(0.1, 1.0 - (distFromCenter * distFromCenter));
            
            double amp = isListening 
                    ? (10 + 22 * envelope * Math.abs(Math.sin(phase + i * 0.35)))
                    : (4 + 6 * envelope * Math.abs(Math.sin(phase * 0.5 + i * 0.2)));

            double y = cy - (amp / 2.0);
            gc.fillRect(x, y, barWidth, amp);
        }
    }
}
