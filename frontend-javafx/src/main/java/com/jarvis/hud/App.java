package com.jarvis.hud;

import com.jarvis.hud.controller.HUDController;
import com.jarvis.hud.websocket.JarvisWebSocketClient;
import javafx.application.Application;
import javafx.application.Platform;
import javafx.fxml.FXMLLoader;
import javafx.scene.Parent;
import javafx.scene.Scene;
import javafx.scene.image.Image;
import javafx.scene.paint.Color;
import javafx.stage.Stage;
import javafx.stage.StageStyle;

public class App extends Application {
    private static final String WS_ENDPOINT = "ws://127.0.0.1:8765/ws/agent";
    private JarvisWebSocketClient wsClient;

    // Allow window dragging for custom undecorated stage
    private double xOffset = 0;
    private double yOffset = 0;

    @Override
    public void start(Stage primaryStage) throws Exception {
        FXMLLoader loader = new FXMLLoader(getClass().getResource("/fxml/hud_main.fxml"));
        Parent root = loader.load();

        HUDController controller = loader.getController();

        // Connect WebSocket client
        wsClient = new JarvisWebSocketClient(WS_ENDPOINT, controller);
        controller.setWebSocketClient(wsClient);
        wsClient.connect();

        // Window drag handlers
        root.setOnMousePressed(event -> {
            xOffset = event.getSceneX();
            yOffset = event.getSceneY();
        });
        root.setOnMouseDragged(event -> {
            primaryStage.setX(event.getScreenX() - xOffset);
            primaryStage.setY(event.getScreenY() - yOffset);
        });

        Scene scene = new Scene(root, 1280, 820);
        scene.setFill(Color.web("#030b17"));

        primaryStage.initStyle(StageStyle.UNDECORATED);
        primaryStage.setTitle("J.A.R.V.I.S. - Iron Man HUD");

        // Set Tab bar / Taskbar / Window Icon (multiple resolutions for crisp display)
        try {
            primaryStage.getIcons().addAll(
                new Image(getClass().getResourceAsStream("/icons/app_icon_16x16.png")),
                new Image(getClass().getResourceAsStream("/icons/app_icon_32x32.png")),
                new Image(getClass().getResourceAsStream("/icons/app_icon_48x48.png")),
                new Image(getClass().getResourceAsStream("/icons/app_icon_64x64.png")),
                new Image(getClass().getResourceAsStream("/icons/app_icon_128x128.png")),
                new Image(getClass().getResourceAsStream("/icons/app_icon_256x256.png")),
                new Image(getClass().getResourceAsStream("/icons/app_icon.png"))
            );
        } catch (Exception ex) {
            System.err.println("[App] Could not load icon: " + ex.getMessage());
        }

        primaryStage.setScene(scene);
        primaryStage.show();

        primaryStage.setOnCloseRequest(e -> {
            if (wsClient != null) {
                wsClient.close();
            }
            Platform.exit();
            System.exit(0);
        });
    }

    @Override
    public void stop() throws Exception {
        if (wsClient != null) {
            wsClient.close();
        }
        super.stop();
    }

    public static void main(String[] args) {
        launch(args);
    }
}
