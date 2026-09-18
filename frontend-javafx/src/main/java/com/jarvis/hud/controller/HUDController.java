package com.jarvis.hud.controller;

import com.jarvis.hud.audio.AudioCaptureService;
import com.jarvis.hud.audio.AudioPlaybackService;
import com.jarvis.hud.view.ArcReactorCanvas;
import com.jarvis.hud.view.RadarCanvas;
import com.jarvis.hud.view.WaveformCanvas;
import com.jarvis.hud.websocket.JarvisWebSocketClient;
import com.jarvis.hud.websocket.PacketListener;
import javafx.animation.KeyFrame;
import javafx.animation.Timeline;
import javafx.application.Platform;
import javafx.fxml.FXML;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.*;
import javafx.scene.paint.Color;
import javafx.scene.shape.Circle;
import javafx.stage.Modality;
import javafx.stage.Stage;
import javafx.stage.StageStyle;
import javafx.util.Duration;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

public class HUDController implements PacketListener {
    // Top Bar
    @FXML private Label connectionStatusLabel;
    @FXML private Circle connectionLed;

    // Left Column - Voice Command
    @FXML private Pane waveformContainer;
    @FXML private Label voiceCommandTranscriptLabel;

    // Left Column - System Status
    @FXML private Label cpuLabel;
    @FXML private ProgressBar cpuProgressBar;
    @FXML private Label ramLabel;
    @FXML private ProgressBar ramProgressBar;
    @FXML private Label diskLabel;
    @FXML private ProgressBar diskProgressBar;
    @FXML private Label networkStatusLabel;
    @FXML private Circle networkLed;

    // Center Section
    @FXML private Label statusAnalyzingLabel;
    @FXML private Label statusProcessingLabel;
    @FXML private Label statusReadyLabel;
    @FXML private StackPane arcReactorContainer;
    @FXML private Pane radarContainer;
    @FXML private Label securityAlertBanner;

    // Right Column - Clock & Weather
    @FXML private Label clockLabel;
    @FXML private Label dateLabel;
    @FXML private VBox recentActivityList;

    // Bottom Input Bar
    @FXML private TextField promptInputField;
    @FXML private Button sendBtn;
    @FXML private Button abortBtn;

    // Audio Services
    private final AudioPlaybackService audioPlaybackService = new AudioPlaybackService();
    private final AudioCaptureService audioCaptureService = new AudioCaptureService();

    // 5-Second Inactivity Timeline for auto-trigger
    private Timeline silenceAutoExecuteTimeline;
    private int countdownSeconds = 5;

    // Canvases
    private ArcReactorCanvas arcReactorCanvas;
    private WaveformCanvas waveformCanvas;
    private RadarCanvas radarCanvas;

    // WebSocket Client
    private JarvisWebSocketClient wsClient;

    @FXML
    public void initialize() {
        // Embed Canvases
        arcReactorCanvas = new ArcReactorCanvas(360, 360);
        arcReactorContainer.getChildren().add(arcReactorCanvas);

        waveformCanvas = new WaveformCanvas(240, 50);
        waveformContainer.getChildren().add(waveformCanvas);

        radarCanvas = new RadarCanvas(110, 110);
        radarContainer.getChildren().add(radarCanvas);

        // Clock Timeline
        Timeline clockTimeline = new Timeline(new KeyFrame(Duration.seconds(1), e -> updateClock()));
        clockTimeline.setCycleCount(Timeline.INDEFINITE);
        clockTimeline.play();
        updateClock();

        // Default HUD states
        statusAnalyzingLabel.setOpacity(0.3);
        statusProcessingLabel.setOpacity(0.3);
        statusReadyLabel.setOpacity(1.0);
        securityAlertBanner.setVisible(false);

        // Enter key in prompt field
        promptInputField.setOnAction(e -> handleSendMessage());

        // Setup 5-second silence auto-execute timer
        setupSilenceDetection();
    }

    private void setupSilenceDetection() {
        // Continuous Audio Capture with VAD
        audioCaptureService.setOnSilenceDetected(() -> {
            Platform.runLater(() -> {
                String currentText = promptInputField.getText().trim();
                if (!currentText.isEmpty()) {
                    voiceCommandTranscriptLabel.setText("5s silence detected: Executing task...");
                    handleSendMessage();
                }
            });
        });

        audioCaptureService.setOnAudioLevel(rms -> {
            Platform.runLater(() -> {
                waveformCanvas.setListening(rms > 250.0);
            });
        });

        // Start capture
        audioCaptureService.startCapture(null);

        // Auto-execute 5 seconds after user stops typing as well
        promptInputField.textProperty().addListener((obs, oldVal, newVal) -> {
            if (silenceAutoExecuteTimeline != null) {
                silenceAutoExecuteTimeline.stop();
            }
            if (!newVal.trim().isEmpty()) {
                countdownSeconds = 5;
                silenceAutoExecuteTimeline = new Timeline(new KeyFrame(Duration.seconds(1), evt -> {
                    countdownSeconds--;
                    if (countdownSeconds <= 0) {
                        silenceAutoExecuteTimeline.stop();
                        handleSendMessage();
                    } else {
                        voiceCommandTranscriptLabel.setText("\"" + newVal + "\" (Auto-executing in " + countdownSeconds + "s...)");
                    }
                }));
                silenceAutoExecuteTimeline.setCycleCount(5);
                silenceAutoExecuteTimeline.play();
            }
        });
    }

    public void setWebSocketClient(JarvisWebSocketClient wsClient) {
        this.wsClient = wsClient;
    }

    private void updateClock() {
        LocalDateTime now = LocalDateTime.now();
        clockLabel.setText(now.format(DateTimeFormatter.ofPattern("HH:mm")));
        dateLabel.setText(now.format(DateTimeFormatter.ofPattern("EEEE, d MMMM yyyy")));
    }

    @FXML
    private void handleSendMessage() {
        String text = promptInputField.getText().trim();
        if (text.isEmpty()) return;

        voiceCommandTranscriptLabel.setText("\"" + text + "\"");
        promptInputField.clear();

        statusAnalyzingLabel.setOpacity(0.4);
        statusProcessingLabel.setOpacity(1.0);
        statusReadyLabel.setOpacity(0.3);
        arcReactorCanvas.setStatusText("PROCESSING");

        if (wsClient != null) {
            wsClient.sendPrompt(text, "TEXT");
        }
    }

    @FXML
    private void handleMicClick() {
        // Continuous background listening is always active.
        promptInputField.requestFocus();
        voiceCommandTranscriptLabel.setText("Microphone is LIVE & Always-On. Say 'Jarvis' to command.");
    }

    @FXML
    private void handleEmergencyAbort() {
        if (wsClient != null) {
            wsClient.sendAbortSignal("USER_EMERGENCY_KILL_SWITCH");
        }
        arcReactorCanvas.setStatusText("ABORTED");
        statusAnalyzingLabel.setOpacity(0.3);
        statusProcessingLabel.setOpacity(0.3);
        statusReadyLabel.setOpacity(1.0);
        addActivityItem("EMERGENCY ABORT", "Action halt triggered by user", "#ff3344");
    }

    @FXML
    private void handleOpenSettings() {
        try {
            FXMLLoader loader = new FXMLLoader(getClass().getResource("/fxml/settings_dialog.fxml"));
            Parent root = loader.load();
            SettingsController controller = loader.getController();
            controller.setWebSocketClient(wsClient);

            Stage dialogStage = new Stage();
            dialogStage.initStyle(StageStyle.UNDECORATED);
            dialogStage.initModality(Modality.APPLICATION_MODAL);
            dialogStage.setTitle("J.A.R.V.I.S. Settings");
            Scene scene = new Scene(root);
            scene.setFill(Color.TRANSPARENT);
            dialogStage.setScene(scene);
            dialogStage.showAndWait();
        } catch (Exception e) {
            e.printStackTrace();
        }
    }

    @FXML
    private void handleQuickBrowser() {
        if (wsClient != null) wsClient.sendPrompt("Buka Chrome", "TEXT");
    }

    @FXML
    private void handleQuickFiles() {
        if (wsClient != null) wsClient.sendPrompt("Buka folder files", "TEXT");
    }

    @FXML
    private void handleQuickNotepad() {
        if (wsClient != null) wsClient.sendPrompt("Buka notepad catatan", "TEXT");
    }

    @FXML
    private void handleQuickMusic() {
        if (wsClient != null) wsClient.sendPrompt("Putar musik", "TEXT");
    }

    @FXML
    private void handleWindowMinimize() {
        Stage stage = (Stage) promptInputField.getScene().getWindow();
        stage.setIconified(true);
    }

    @FXML
    private void handleWindowClose() {
        if (wsClient != null) {
            wsClient.close();
        }
        Platform.exit();
        System.exit(0);
    }

    // PacketListener Callbacks
    @Override
    public void onConnected() {
        connectionStatusLabel.setText("ONLINE");
        connectionLed.setFill(Color.web("#00f0ff"));
        arcReactorCanvas.setStatusText("SYSTEM ONLINE");
        addActivityItem("CORE CONNECTED", "WebSocket link established", "#00d2ff");
    }

    @Override
    public void onDisconnected() {
        connectionStatusLabel.setText("OFFLINE");
        connectionLed.setFill(Color.web("#ff3344"));
        arcReactorCanvas.setStatusText("OFFLINE");
    }

    @Override
    public void onGreeting(String greetingText, String audioUrl) {
        voiceCommandTranscriptLabel.setText("\"" + greetingText + "\"");
        arcReactorCanvas.setStatusText("READY");
        addActivityItem("SYSTEM GREETING", greetingText, "#00f0ff");
    }

    @Override
    public void onStatusUpdate(String status, String detail) {
        if ("PROCESSING".equalsIgnoreCase(status)) {
            statusAnalyzingLabel.setOpacity(0.5);
            statusProcessingLabel.setOpacity(1.0);
            statusReadyLabel.setOpacity(0.3);
            arcReactorCanvas.setStatusText("PROCESSING");
        } else if ("AWAITING_COMMAND".equalsIgnoreCase(status) || "LISTENING".equalsIgnoreCase(status)) {
            statusAnalyzingLabel.setOpacity(0.3);
            statusProcessingLabel.setOpacity(0.7);
            statusReadyLabel.setOpacity(1.0);
            arcReactorCanvas.setStatusText("LISTENING");
            waveformCanvas.setListening(true);
            if (detail != null && !detail.isEmpty()) {
                voiceCommandTranscriptLabel.setText(detail);
            }
        } else if ("ABORTED".equalsIgnoreCase(status)) {
            arcReactorCanvas.setStatusText("ABORTED");
            statusAnalyzingLabel.setOpacity(0.3);
            statusProcessingLabel.setOpacity(0.3);
            statusReadyLabel.setOpacity(1.0);
        } else {
            statusAnalyzingLabel.setOpacity(0.3);
            statusProcessingLabel.setOpacity(0.3);
            statusReadyLabel.setOpacity(1.0);
            arcReactorCanvas.setStatusText("READY");
        }
    }

    @Override
    public void onActionDispatch(String taskId, String actionType, String target, String status) {
        addActivityItem("ACTION: " + actionType, target, "#00d2ff");
        if ("IN_PROGRESS".equalsIgnoreCase(status)) {
            arcReactorCanvas.setStatusText("EXECUTING");
        } else if ("COMPLETED".equalsIgnoreCase(status)) {
            arcReactorCanvas.setStatusText("COMPLETE");
        }
    }

    @Override
    public void onSecurityAlert(String violationCode, String message) {
        securityAlertBanner.setText("⚠️ " + violationCode + ": " + message);
        securityAlertBanner.setVisible(true);
        arcReactorCanvas.setStatusText("ALERT!");
        addActivityItem("SECURITY ALERT", violationCode + " - " + message, "#ff3344");

        Timeline hideAlert = new Timeline(new KeyFrame(Duration.seconds(6), e -> securityAlertBanner.setVisible(false)));
        hideAlert.play();
    }

    @Override
    public void onTelemetryUpdate(int cpu, int ram, int disk, String network) {
        cpuLabel.setText(cpu + "%");
        cpuProgressBar.setProgress(cpu / 100.0);

        ramLabel.setText(ram + "%");
        ramProgressBar.setProgress(ram / 100.0);

        diskLabel.setText(disk + "%");
        diskProgressBar.setProgress(disk / 100.0);

        networkStatusLabel.setText(network);
        networkLed.setFill("Connected".equalsIgnoreCase(network) ? Color.web("#00ffaa") : Color.web("#ff3344"));
    }

    @Override
    public void onAudioFeedback(String promptText, String replyText, String audioUrl) {
        if (promptText != null && !promptText.isEmpty()) {
            voiceCommandTranscriptLabel.setText("\"" + promptText + "\"");
        }
        boolean isError = replyText != null && (
            replyText.toLowerCase().contains("error:") || 
            replyText.toLowerCase().contains("exception:") ||
            replyText.toLowerCase().contains("ai error")
        );
        if (isError) {
            addActivityItem("ERROR", replyText, "#ff3344");
        } else {
            addActivityItem("JARVIS RESPONSE", replyText, "#00f0ff");
        }
    }

    @Override
    public void onErrorAlert(String title, String errorMessage) {
        // Display error message as text in Recent Activity, DO NOT read aloud
        voiceCommandTranscriptLabel.setText("⚠️ " + errorMessage);
        arcReactorCanvas.setStatusText("ERROR");
        statusAnalyzingLabel.setOpacity(0.3);
        statusProcessingLabel.setOpacity(0.3);
        statusReadyLabel.setOpacity(1.0);
        addActivityItem(title != null && !title.isEmpty() ? title : "ERROR", errorMessage, "#ff3344");
    }


    @Override
    public void onVoiceStatus(String status) {
        if ("LISTENING".equalsIgnoreCase(status) || "STANDBY".equalsIgnoreCase(status)) {
            waveformCanvas.setListening(false);
            voiceCommandTranscriptLabel.setText("Microphone LIVE: Waiting for 'Jarvis'...");
        } else if ("PROCESSING_SPEECH".equalsIgnoreCase(status)) {
            statusAnalyzingLabel.setOpacity(0.5);
            statusProcessingLabel.setOpacity(1.0);
            statusReadyLabel.setOpacity(0.3);
            arcReactorCanvas.setStatusText("PROCESSING");
            voiceCommandTranscriptLabel.setText("5s silence reached. Executing task...");
        } else if (status != null && status.startsWith("WAKE_WORD_ACTIVE:")) {
            String utterance = status.substring("WAKE_WORD_ACTIVE:".length()).trim();
            waveformCanvas.setListening(true);
            arcReactorCanvas.setStatusText("ACTIVE");
            voiceCommandTranscriptLabel.setText("Jarvis Activated: \"" + utterance + "\"");
        } else if (status != null && status.startsWith("IGNORED_NO_WAKE_WORD:")) {
            waveformCanvas.setListening(false);
            voiceCommandTranscriptLabel.setText("Ignored: Standby (Say 'Jarvis' to command)");
        }
    }

    @Override
    public void onContextRehydrated(int count) {
        addActivityItem("CONTEXT RESTORED", count + " prior logs recovered from crash", "#00ffaa");
    }

    private void addActivityItem(String title, String subtitle, String colorHex) {
        HBox row = new HBox(8);
        row.setStyle("-fx-padding: 4px 6px; -fx-background-color: rgba(5, 20, 35, 0.4); -fx-background-radius: 4px;");

        Label dot = new Label("●");
        dot.setStyle("-fx-text-fill: " + colorHex + "; -fx-font-size: 10px;");

        VBox texts = new VBox(2);
        Label titleLbl = new Label(title);
        titleLbl.setStyle("-fx-text-fill: #e6f7ff; -fx-font-size: 11px; -fx-font-weight: bold;");
        Label subLbl = new Label(subtitle);
        subLbl.setStyle("-fx-text-fill: #5c8ca6; -fx-font-size: 10px;");
        subLbl.setWrapText(true);
        texts.getChildren().addAll(titleLbl, subLbl);

        row.getChildren().addAll(dot, texts);

        // Keep maximum 5 items
        if (recentActivityList.getChildren().size() >= 5) {
            recentActivityList.getChildren().remove(recentActivityList.getChildren().size() - 1);
        }
        recentActivityList.getChildren().add(0, row);
    }
}
