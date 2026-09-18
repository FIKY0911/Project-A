package com.jarvis.hud.audio;

import javafx.scene.media.Media;
import javafx.scene.media.MediaPlayer;

import javax.sound.sampled.AudioInputStream;
import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.Clip;
import java.io.File;

public class AudioPlaybackService {
    private MediaPlayer currentMediaPlayer;

    public void playUrlOrFile(String pathOrUrl) {
        try {
            stopCurrent();
            if (pathOrUrl.startsWith("http://") || pathOrUrl.startsWith("https://")) {
                Media media = new Media(pathOrUrl);
                currentMediaPlayer = new MediaPlayer(media);
                currentMediaPlayer.play();
            } else {
                File file = new File(pathOrUrl);
                if (file.exists()) {
                    if (pathOrUrl.endsWith(".wav")) {
                        AudioInputStream audioStream = AudioSystem.getAudioInputStream(file);
                        Clip clip = AudioSystem.getClip();
                        clip.open(audioStream);
                        clip.start();
                    } else {
                        Media media = new Media(file.toURI().toString());
                        currentMediaPlayer = new MediaPlayer(media);
                        currentMediaPlayer.play();
                    }
                }
            }
        } catch (Exception e) {
            System.err.println("[AudioPlaybackService] Playback error: " + e.getMessage());
        }
    }

    public void stopCurrent() {
        if (currentMediaPlayer != null) {
            try {
                currentMediaPlayer.stop();
                currentMediaPlayer.dispose();
            } catch (Exception ignored) {}
            currentMediaPlayer = null;
        }
    }
}
