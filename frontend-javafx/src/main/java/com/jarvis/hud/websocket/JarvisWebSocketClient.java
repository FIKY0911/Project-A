package com.jarvis.hud.websocket;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import javafx.application.Platform;
import org.java_websocket.client.WebSocketClient;
import org.java_websocket.handshake.ServerHandshake;

import java.net.URI;
import java.time.Instant;
import java.util.UUID;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class JarvisWebSocketClient {
    private final URI serverUri;
    private final PacketListener listener;
    private WebSocketClient client;
    private final ScheduledExecutorService reconnectExecutor = Executors.newSingleThreadScheduledExecutor();
    private int backoffSeconds = 1;
    private boolean isExplicitlyClosed = false;

    public JarvisWebSocketClient(String uriString, PacketListener listener) {
        this.serverUri = URI.create(uriString);
        this.listener = listener;
    }

    public void connect() {
        isExplicitlyClosed = false;
        initClient();
        client.connect();
    }

    private void initClient() {
        client = new WebSocketClient(serverUri) {
            @Override
            public void onOpen(ServerHandshake handshakedata) {
                backoffSeconds = 1;
                Platform.runLater(listener::onConnected);
            }

            @Override
            public void onMessage(String message) {
                handleIncomingMessage(message);
            }

            @Override
            public void onClose(int code, String reason, boolean remote) {
                Platform.runLater(listener::onDisconnected);
                if (!isExplicitlyClosed) {
                    scheduleReconnect();
                }
            }

            @Override
            public void onError(Exception ex) {
                // Handled in onClose or logged
            }
        };
    }

    private void scheduleReconnect() {
        reconnectExecutor.schedule(() -> {
            if (!isExplicitlyClosed) {
                initClient();
                try {
                    client.connect();
                } catch (Exception ignored) {}
                backoffSeconds = Math.min(backoffSeconds * 2, 10);
            }
        }, backoffSeconds, TimeUnit.SECONDS);
    }

    private void handleIncomingMessage(String jsonStr) {
        try {
            JsonObject json = JsonParser.parseString(jsonStr).getAsJsonObject();
            String eventType = json.has("event_type") ? json.get("event_type").getAsString() : "";
            JsonObject payload = json.has("payload") && json.get("payload").isJsonObject() 
                    ? json.getAsJsonObject("payload") : new JsonObject();

            Platform.runLater(() -> {
                switch (eventType) {
                    case "SYSTEM_GREETING" -> {
                        String greetingText = payload.has("greeting_text") ? payload.get("greeting_text").getAsString() : "";
                        String audioUrl = payload.has("audio_stream_url") ? payload.get("audio_stream_url").getAsString() : "";
                        listener.onGreeting(greetingText, audioUrl);
                    }
                    case "STATUS_UPDATE" -> {
                        String status = payload.has("status") ? payload.get("status").getAsString() : "";
                        String detail = payload.has("detail") ? payload.get("detail").getAsString() : "";
                        listener.onStatusUpdate(status, detail);
                    }
                    case "ACTION_DISPATCH" -> {
                        String taskId = json.has("task_id") ? json.get("task_id").getAsString() : "";
                        String actionType = payload.has("action_type") ? payload.get("action_type").getAsString() : "";
                        String target = payload.has("target") ? payload.get("target").getAsString() : "";
                        String status = payload.has("status") ? payload.get("status").getAsString() : "";
                        listener.onActionDispatch(taskId, actionType, target, status);
                    }
                    case "SECURITY_ALERT" -> {
                        String code = payload.has("violation_code") ? payload.get("violation_code").getAsString() : "";
                        String msg = payload.has("message") ? payload.get("message").getAsString() : "";
                        listener.onSecurityAlert(code, msg);
                    }
                    case "SYSTEM_TELEMETRY" -> {
                        int cpu = payload.has("cpu_usage") ? payload.get("cpu_usage").getAsInt() : 0;
                        int ram = payload.has("ram_usage") ? payload.get("ram_usage").getAsInt() : 0;
                        int disk = payload.has("disk_usage") ? payload.get("disk_usage").getAsInt() : 0;
                        String net = payload.has("network_status") ? payload.get("network_status").getAsString() : "Unknown";
                        listener.onTelemetryUpdate(cpu, ram, disk, net);
                    }
                    case "TTS_AUDIO_STREAM" -> {
                        String prompt = payload.has("prompt_text") ? payload.get("prompt_text").getAsString() : "";
                        String reply = payload.has("reply_text") ? payload.get("reply_text").getAsString() : "";
                        String audioUrl = payload.has("audio_url") ? payload.get("audio_url").getAsString() : "";
                        listener.onAudioFeedback(prompt, reply, audioUrl);
                    }
                    case "VOICE_STATUS" -> {
                        String status = payload.has("status") ? payload.get("status").getAsString() : "";
                        listener.onVoiceStatus(status);
                    }
                    case "CONTEXT_REHYDRATED" -> {
                        int count = payload.has("recovered_count") ? payload.get("recovered_count").getAsInt() : 0;
                        listener.onContextRehydrated(count);
                    }
                    case "ERROR_ALERT" -> {
                        String title = payload.has("title") ? payload.get("title").getAsString() : "ERROR";
                        String errMsg = payload.has("error_message") ? payload.get("error_message").getAsString() : "";
                        listener.onErrorAlert(title, errMsg);
                    }
                }
            });
        } catch (Exception e) {
            System.err.println("JSON parse error: " + e.getMessage());
        }
    }

    public void sendPrompt(String text, String mode) {
        if (client != null && client.isOpen()) {
            JsonObject root = new JsonObject();
            root.addProperty("event_type", "USER_PROMPT");
            root.addProperty("session_id", UUID.randomUUID().toString());
            root.addProperty("timestamp", Instant.now().toString());

            JsonObject payload = new JsonObject();
            payload.addProperty("input_mode", mode);
            payload.addProperty("text_content", text);
            payload.addProperty("audio_sample_rate", 16000);
            root.add("payload", payload);

            client.send(root.toString());
        }
    }

    public void sendAbortSignal(String reason) {
        if (client != null && client.isOpen()) {
            JsonObject root = new JsonObject();
            root.addProperty("event_type", "USER_ABORT_SIGNAL");
            JsonObject payload = new JsonObject();
            payload.addProperty("reason", reason);
            root.add("payload", payload);

            client.send(root.toString());
        }
    }

    public void sendConfigUpdate(String provider, String model, String apiKey, String baseUrl) {
        if (client != null && client.isOpen()) {
            JsonObject root = new JsonObject();
            root.addProperty("event_type", "SYSTEM_CONFIG_UPDATE");
            JsonObject payload = new JsonObject();
            payload.addProperty("provider_name", provider);
            payload.addProperty("model_name", model);
            payload.addProperty("api_key", apiKey);
            payload.addProperty("base_url", baseUrl);
            root.add("payload", payload);

            client.send(root.toString());
        }
    }

    public void close() {
        isExplicitlyClosed = true;
        reconnectExecutor.shutdownNow();
        if (client != null) {
            client.close();
        }
    }
}
