package com.jarvis.hud.audio;

import javax.sound.sampled.*;
import java.util.function.Consumer;

public class AudioCaptureService {
    private TargetDataLine line;
    private Thread captureThread;
    private boolean isRecording = false;
    private static final double SPEECH_RMS_THRESHOLD = 300.0;
    private static final long SILENCE_TRIGGER_MS = 5000; // 5 seconds of silence

    private long lastSpeechTime = 0;
    private boolean wasSpeaking = false;
    private Runnable onSilenceDetectedCallback;
    private Consumer<Double> onAudioLevelCallback;

    public static AudioFormat getStandardFormat() {
        // 16kHz, 16-bit, Mono, Signed, Little-Endian
        return new AudioFormat(16000, 16, 1, true, false);
    }

    public void setOnSilenceDetected(Runnable callback) {
        this.onSilenceDetectedCallback = callback;
    }

    public void setOnAudioLevel(Consumer<Double> callback) {
        this.onAudioLevelCallback = callback;
    }

    public synchronized void startCapture(Consumer<byte[]> chunkConsumer) {
        if (isRecording) return;
        try {
            AudioFormat format = getStandardFormat();
            DataLine.Info info = new DataLine.Info(TargetDataLine.class, format);
            if (!AudioSystem.isLineSupported(info)) {
                System.err.println("[AudioCaptureService] Microphone line not supported.");
                return;
            }
            line = (TargetDataLine) AudioSystem.getLine(info);
            line.open(format);
            line.start();
            isRecording = true;

            captureThread = new Thread(() -> {
                byte[] buffer = new byte[2048];
                while (isRecording) {
                    int count = line.read(buffer, 0, buffer.length);
                    if (count > 0) {
                        double rms = calculateRMS(buffer, count);
                        if (onAudioLevelCallback != null) {
                            onAudioLevelCallback.accept(rms);
                        }

                        long now = System.currentTimeMillis();
                        if (rms > SPEECH_RMS_THRESHOLD) {
                            wasSpeaking = true;
                            lastSpeechTime = now;
                        } else if (wasSpeaking && lastSpeechTime > 0) {
                            // Silence elapsed check
                            if (now - lastSpeechTime >= SILENCE_TRIGGER_MS) {
                                wasSpeaking = false;
                                lastSpeechTime = 0;
                                if (onSilenceDetectedCallback != null) {
                                    onSilenceDetectedCallback.run();
                                }
                            }
                        }

                        if (chunkConsumer != null) {
                            byte[] chunk = new byte[count];
                            System.arraycopy(buffer, 0, chunk, 0, count);
                            chunkConsumer.accept(chunk);
                        }
                    }
                }
            }, "AudioCaptureWorker");
            captureThread.setDaemon(true);
            captureThread.start();
        } catch (Exception e) {
            System.err.println("[AudioCaptureService] Error starting capture: " + e.getMessage());
        }
    }

    private double calculateRMS(byte[] audioData, int length) {
        long sum = 0;
        int samples = length / 2;
        for (int i = 0; i < length - 1; i += 2) {
            short sample = (short) ((audioData[i + 1] << 8) | (audioData[i] & 0xff));
            sum += (long) sample * sample;
        }
        return samples > 0 ? Math.sqrt((double) sum / samples) : 0.0;
    }

    public synchronized void stopCapture() {
        isRecording = false;
        if (line != null) {
            line.stop();
            line.close();
        }
    }

    public boolean isRecording() {
        return isRecording;
    }
}
