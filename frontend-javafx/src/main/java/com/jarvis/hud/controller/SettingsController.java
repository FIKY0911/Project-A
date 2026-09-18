package com.jarvis.hud.controller;

import com.jarvis.hud.websocket.JarvisWebSocketClient;
import javafx.fxml.FXML;
import javafx.scene.control.ComboBox;
import javafx.scene.control.Label;
import javafx.scene.control.PasswordField;
import javafx.scene.control.TextField;
import javafx.stage.Stage;

public class SettingsController {
    @FXML private ComboBox<String> providerComboBox;
    @FXML private TextField modelField;
    @FXML private PasswordField apiKeyField;
    @FXML private TextField baseUrlField;
    @FXML private Label statusLabel;

    private JarvisWebSocketClient wsClient;

    @FXML
    public void initialize() {
        providerComboBox.getItems().addAll(
                "OpenCode / OpenRouter",
                "OpenAI",
                "DeepSeek",
                "Groq",
                "Anthropic Claude",
                "Google Gemini",
                "Ollama (Local)",
                "Custom Endpoint"
        );
        providerComboBox.setValue("OpenCode / OpenRouter");
        modelField.setText("openai/gpt-4o");
        baseUrlField.setText("https://openrouter.ai/api/v1");

        providerComboBox.valueProperty().addListener((obs, oldVal, newVal) -> {
            if ("OpenCode / OpenRouter".equals(newVal)) {
                modelField.setText("openai/gpt-4o");
                baseUrlField.setText("https://openrouter.ai/api/v1");
            } else if ("OpenAI".equals(newVal)) {
                modelField.setText("gpt-4o");
                baseUrlField.setText("https://api.openai.com/v1");
            } else if ("DeepSeek".equals(newVal)) {
                modelField.setText("deepseek-chat");
                baseUrlField.setText("https://api.deepseek.com/v1");
            } else if ("Groq".equals(newVal)) {
                modelField.setText("llama-3.3-70b-versatile");
                baseUrlField.setText("https://api.groq.com/openai/v1");
            } else if ("Anthropic Claude".equals(newVal)) {
                modelField.setText("claude-3-5-sonnet-20241022");
                baseUrlField.setText("https://api.anthropic.com");
            } else if ("Google Gemini".equals(newVal)) {
                modelField.setText("gemini-1.5-flash");
                baseUrlField.setText("");
            } else if ("Ollama (Local)".equals(newVal)) {
                modelField.setText("llama3");
                baseUrlField.setText("http://localhost:11434");
            } else if ("Custom Endpoint".equals(newVal)) {
                modelField.setText("FreeTrial");
                baseUrlField.setText("http://localhost:20128/v1");
            }
        });
    }

    public void setWebSocketClient(JarvisWebSocketClient wsClient) {
        this.wsClient = wsClient;
    }

    @FXML
    private void handleSave() {
        String provider = providerComboBox.getValue().toLowerCase();
        String model = modelField.getText().trim();
        String apiKey = apiKeyField.getText().trim();
        String baseUrl = baseUrlField.getText().trim();

        if (wsClient != null) {
            wsClient.sendConfigUpdate(provider, model, apiKey, baseUrl);
            statusLabel.setText("Configuration transmitted to core.");
        }

        Stage stage = (Stage) providerComboBox.getScene().getWindow();
        stage.close();
    }

    @FXML
    private void handleCancel() {
        Stage stage = (Stage) providerComboBox.getScene().getWindow();
        stage.close();
    }
}
