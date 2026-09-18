package com.jarvis.hud.view;

import javafx.animation.AnimationTimer;
import javafx.scene.canvas.Canvas;
import javafx.scene.canvas.GraphicsContext;
import javafx.scene.effect.DropShadow;
import javafx.scene.paint.Color;
import javafx.scene.paint.RadialGradient;
import javafx.scene.paint.CycleMethod;
import javafx.scene.paint.Stop;
import javafx.scene.shape.StrokeLineCap;
import javafx.scene.text.Font;
import javafx.scene.text.FontWeight;
import javafx.scene.text.TextAlignment;

public class ArcReactorCanvas extends Canvas {
    private double outerAngle = 0;
    private double middleAngle = 0;
    private double pulsePhase = 0;
    private String statusText = "SYSTEM ONLINE";
    private Color primaryCyan = Color.web("#00f0ff");
    private Color deepCyan = Color.web("#0088cc");

    private final AnimationTimer timer = new AnimationTimer() {
        private long lastNano = 0;

        @Override
        public void handle(long now) {
            if (lastNano == 0) {
                lastNano = now;
                return;
            }
            double delta = (now - lastNano) / 1_000_000_000.0;
            lastNano = now;

            outerAngle = (outerAngle + 45 * delta) % 360;
            middleAngle = (middleAngle - 30 * delta) % 360;
            pulsePhase = (pulsePhase + 2.5 * delta) % (2 * Math.PI);

            render();
        }
    };

    public ArcReactorCanvas() {
        this(400, 400);
    }

    public ArcReactorCanvas(double width, double height) {
        super(width, height);
        timer.start();
    }

    public void setStatusText(String text) {
        this.statusText = text;
    }

    private void render() {
        double w = getWidth();
        double h = getHeight();
        if (w <= 0 || h <= 0) return;

        GraphicsContext gc = getGraphicsContext2D();
        gc.clearRect(0, 0, w, h);

        double cx = w / 2.0;
        double cy = h / 2.0;
        double maxRadius = Math.min(cx, cy) - 10;

        // Pulse scale
        double pulse = 0.95 + 0.05 * Math.sin(pulsePhase);

        // Background subtle radial glow
        RadialGradient bgGlow = new RadialGradient(
                0, 0, cx, cy, maxRadius, false, CycleMethod.NO_CYCLE,
                new Stop(0.0, Color.web("#003355", 0.45)),
                new Stop(0.7, Color.web("#001a33", 0.15)),
                new Stop(1.0, Color.TRANSPARENT)
        );
        gc.setFill(bgGlow);
        gc.fillOval(cx - maxRadius, cy - maxRadius, maxRadius * 2, maxRadius * 2);

        gc.save();
        gc.setLineCap(StrokeLineCap.ROUND);

        // 1. Outermost thin circle with tick marks
        gc.setStroke(Color.web("#0077aa", 0.5));
        gc.setLineWidth(1.5);
        gc.strokeOval(cx - maxRadius, cy - maxRadius, maxRadius * 2, maxRadius * 2);

        // 2. Segmented Rotating Outer Arc Ring
        double rOuter = maxRadius * 0.88;
        gc.save();
        gc.setStroke(primaryCyan);
        gc.setLineWidth(4.0);
        gc.setEffect(new DropShadow(8, primaryCyan));
        int segments = 12;
        for (int i = 0; i < segments; i++) {
            double startAngle = outerAngle + (i * (360.0 / segments));
            if (i % 2 == 0) {
                gc.strokeArc(cx - rOuter, cy - rOuter, rOuter * 2, rOuter * 2, startAngle, 18, javafx.scene.shape.ArcType.OPEN);
            } else {
                gc.setStroke(deepCyan);
                gc.strokeArc(cx - rOuter, cy - rOuter, rOuter * 2, rOuter * 2, startAngle, 8, javafx.scene.shape.ArcType.OPEN);
                gc.setStroke(primaryCyan);
            }
        }
        gc.restore();

        // 3. Middle Rotating Ring (Counter-Clockwise)
        double rMid = maxRadius * 0.72 * pulse;
        gc.save();
        gc.setStroke(Color.web("#00d2ff", 0.7));
        gc.setLineWidth(3.0);
        int midSegments = 8;
        for (int i = 0; i < midSegments; i++) {
            double startAngle = middleAngle + (i * (360.0 / midSegments));
            gc.strokeArc(cx - rMid, cy - rMid, rMid * 2, rMid * 2, startAngle, 28, javafx.scene.shape.ArcType.OPEN);
        }
        gc.restore();

        // 4. Glowing inner ring with segmented blocks
        double rInner = maxRadius * 0.52;
        gc.save();
        gc.setStroke(Color.web("#00f0ff", 0.85));
        gc.setLineWidth(7.0);
        gc.setEffect(new DropShadow(12, primaryCyan));
        int innerSegments = 6;
        for (int i = 0; i < innerSegments; i++) {
            double angle = outerAngle * 0.5 + (i * (360.0 / innerSegments));
            gc.strokeArc(cx - rInner, cy - rInner, rInner * 2, rInner * 2, angle, 40, javafx.scene.shape.ArcType.OPEN);
        }
        gc.restore();

        // 5. Central Core Circle
        double rCore = maxRadius * 0.38;
        RadialGradient coreGrad = new RadialGradient(
                0, 0, cx, cy, rCore, false, CycleMethod.NO_CYCLE,
                new Stop(0.0, Color.web("#003366", 0.85)),
                new Stop(0.8, Color.web("#021020", 0.95)),
                new Stop(1.0, Color.web("#00f0ff", 0.7))
        );
        gc.setFill(coreGrad);
        gc.fillOval(cx - rCore, cy - rCore, rCore * 2, rCore * 2);

        gc.setStroke(primaryCyan);
        gc.setLineWidth(2.0);
        gc.strokeOval(cx - rCore, cy - rCore, rCore * 2, rCore * 2);

        // 6. Central Core Text
        gc.setTextAlign(TextAlignment.CENTER);
        gc.setFill(Color.web("#ffffff"));
        gc.setFont(Font.font("Monospaced", FontWeight.BOLD, 18));
        gc.setEffect(new DropShadow(6, primaryCyan));
        gc.fillText("J . A . R . V . I . S .", cx, cy - 4);

        gc.setFill(Color.web("#00f0ff"));
        gc.setFont(Font.font("Monospaced", FontWeight.NORMAL, 10));
        gc.fillText(statusText, cx, cy + 16);

        gc.restore();
    }
}
