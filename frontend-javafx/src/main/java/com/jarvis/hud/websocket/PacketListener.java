package com.jarvis.hud.websocket;

public interface PacketListener {
    void onConnected();
    void onDisconnected();
    void onGreeting(String greetingText, String audioUrl);
    void onStatusUpdate(String status, String detail);
    void onActionDispatch(String taskId, String actionType, String target, String status);
    void onSecurityAlert(String violationCode, String message);
    void onTelemetryUpdate(int cpu, int ram, int disk, String network);
    void onAudioFeedback(String promptText, String replyText, String audioUrl);
    void onVoiceStatus(String status);
    void onContextRehydrated(int count);
    void onErrorAlert(String title, String errorMessage);
}
