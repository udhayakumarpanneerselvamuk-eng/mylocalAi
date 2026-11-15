
import tkinter as tk
import threading
import queue
import ollama

from guardrails import (
    SYSTEM_PROMPT,
    validate_input,
    validate_output,
    detect_prompt_injection
)


# ==================================================
# CONFIGURATION
# ==================================================

MODEL = "qwen2.5:0.5b"

BG = "#212121"
PANEL = "#303030"
TEXT = "#eeeeee"
ACCENT = "#10a37f"
WARNING = "#ffcc66"
ERROR = "#ff7777"

MAX_HISTORY = 20

# Guardrails enabled by default
GUARDRAILS_ENABLED = True


# ==================================================
# MAIN APPLICATION
# ==================================================

class LocalChat:

    def __init__(self, root):

        self.root = root
        self.root.title("My Local gpt")
        self.root.geometry("900x700")
        self.root.minsize(650, 450)
        self.root.configure(bg=BG)

        self.guardrails_enabled = GUARDRAILS_ENABLED

        # System prompt is retained as conversation context
        self.messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]

        self.events = queue.Queue()
        self.busy = False
        self.pending_start = None

        self.create_ui()

        self.root.after(100, self.process_events)

    # ==================================================
    # CREATE UI
    # ==================================================

    def create_ui(self):

        header = tk.Frame(
            self.root,
            bg=BG
        )

        header.pack(
            fill="x",
            padx=20,
            pady=15
        )

        tk.Label(
            header,
            text="✦ My Local AI",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 20, "bold")
        ).pack(side="left")

        self.guard_button = tk.Button(
            header,
            text="Guardrails: ON",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.toggle_guardrails
        )

        self.guard_button.pack(
            side="right",
            padx=10
        )

        tk.Label(
            header,
            text=f"Model: {MODEL}",
            bg=BG,
            fg=ACCENT,
            font=("Segoe UI", 10)
        ).pack(side="right", padx=10)

        # Chat container
        chat_container = tk.Frame(
            self.root,
            bg=BG
        )

        chat_container.pack(
            fill="both",
            expand=True,
            padx=15
        )

        self.chat = tk.Text(
            chat_container,
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 12),
            wrap="word",
            relief="flat",
            padx=20,
            pady=10,
            state="disabled"
        )

        scrollbar = tk.Scrollbar(
            chat_container,
            command=self.chat.yview
        )

        self.chat.configure(
            yscrollcommand=scrollbar.set
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        self.chat.pack(
            side="left",
            fill="both",
            expand=True
        )

        # Text formatting
        self.chat.tag_config(
            "heading",
            foreground=ACCENT,
            font=("Segoe UI", 11, "bold")
        )

        self.chat.tag_config(
            "warning",
            foreground=WARNING
        )

        self.chat.tag_config(
            "error",
            foreground=ERROR
        )

        # Input area
        bottom = tk.Frame(
            self.root,
            bg=BG
        )

        bottom.pack(
            fill="x",
            padx=20,
            pady=20
        )

        self.entry = tk.Text(
            bottom,
            height=3,
            bg=PANEL,
            fg=TEXT,
            insertbackground="white",
            font=("Segoe UI", 12),
            relief="flat",
            padx=10,
            pady=10,
            wrap="word"
        )

        self.entry.pack(
            side="left",
            fill="x",
            expand=True
        )

        self.entry.bind(
            "<Return>",
            self.enter_pressed
        )

        self.send_button = tk.Button(
            bottom,
            text="Send ↑",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            command=self.send_message
        )

        self.send_button.pack(
            side="right",
            padx=10
        )

        # Welcome messages
        self.write(
            "AI",
            "Hello! I'm your local AI assistant. "
            "How can I help you today?"
        )

        self.update_guardrail_status()

    # ==================================================
    # GUARDRAIL TOGGLE
    # ==================================================

    def toggle_guardrails(self):

        self.guardrails_enabled = (
            not self.guardrails_enabled
        )

        self.update_guardrail_status()

    def update_guardrail_status(self):

        if self.guardrails_enabled:

            self.guard_button.config(
                text="Guardrails: ON",
                bg=ACCENT
            )

            self.write(
                "Security",
                "Application-level guardrails enabled.",
                warning=True
            )

        else:

            self.guard_button.config(
                text="Guardrails: OFF",
                bg="#cc5555"
            )

            self.write(
                "Security",
                "Application-level input and output checks disabled. "
                "Model system instructions remain active.",
                warning=True
            )

    # ==================================================
    # DISPLAY MESSAGES
    # ==================================================

    def write(self, sender, message, warning=False):

        self.chat.config(state="normal")

        self.chat.insert(
            "end",
            f"\n{sender}\n",
            "heading"
        )

        if warning:

            self.chat.insert(
                "end",
                message + "\n",
                "warning"
            )

        else:

            self.chat.insert(
                "end",
                message + "\n"
            )

        self.chat.config(state="disabled")
        self.chat.see("end")

    # ==================================================
    # KEYBOARD INPUT
    # ==================================================

    def enter_pressed(self, event):

        # Shift + Enter creates a new line
        if event.state & 0x0001:
            return

        self.send_message()

        return "break"

    # ==================================================
    # SEND MESSAGE
    # ==================================================

    def send_message(self):

        if self.busy:
            return

        prompt = self.entry.get(
            "1.0",
            "end-1c"
        ).strip()

        # ------------------------------------------
        # INPUT GUARDRAILS
        # ------------------------------------------

        if self.guardrails_enabled:

            allowed, result = validate_input(prompt)

            if not allowed:

                self.write(
                    "Input Guardrail",
                    result,
                    warning=True
                )

                return

            injection_detected, reason = (
                detect_prompt_injection(result)
            )

            if injection_detected:

                self.write(
                    "Security Guardrail",
                    "Request blocked: " + reason,
                    warning=True
                )

                self.entry.delete(
                    "1.0",
                    "end"
                )

                return

        else:

            # Basic empty-input check remains active
            if not prompt:
                return

            result = prompt

        # ------------------------------------------
        # ACCEPT MESSAGE
        # ------------------------------------------

        self.entry.delete(
            "1.0",
            "end"
        )

        self.messages.append({
            "role": "user",
            "content": result
        })

        self.write(
            "You",
            result
        )

        self.pending_start = self.chat.index("end-1c")

        self.write(
            "AI",
            "Thinking..."
        )

        self.busy = True

        self.send_button.config(
            state="disabled",
            text="Thinking..."
        )

        # Preserve system prompt and recent history
        conversation = (
            [self.messages[0]]
            + self.messages[-MAX_HISTORY:]
        )

        # Background processing
        threading.Thread(
            target=self.get_response,
            args=(conversation, self.guardrails_enabled),
            daemon=True
        ).start()

    # ==================================================
    # OLLAMA RESPONSE
    # ==================================================

    def get_response(self, conversation, use_guardrails):

        try:

            response = ollama.chat(
                model=MODEL,
                messages=conversation
            )

            answer = response.message.content

            # --------------------------------------
            # OUTPUT GUARDRAILS
            # --------------------------------------

            if use_guardrails:

                allowed, result = validate_output(answer)

                if not allowed:

                    self.events.put(
                        ("error", result)
                    )

                    return

                answer = result

            self.events.put(
                ("success", answer)
            )

        except Exception as e:

            self.events.put(
                ("error", str(e))
            )

    # ==================================================
    # PROCESS BACKGROUND EVENTS
    # ==================================================

    def process_events(self):

        try:

            while True:

                event, data = self.events.get_nowait()

                self.chat.config(state="normal")

                # Remove Thinking placeholder
                if self.pending_start:

                    self.chat.delete(
                        self.pending_start,
                        "end-1c"
                    )

                if event == "success":

                    self.chat.insert(
                        "end",
                        data + "\n"
                    )

                    self.messages.append({
                        "role": "assistant",
                        "content": data
                    })

                elif event == "error":

                    self.chat.insert(
                        "end",
                        "Error: " + data + "\n",
                        "error"
                    )

                self.chat.config(state="disabled")
                self.chat.see("end")

                self.pending_start = None
                self.busy = False

                self.send_button.config(
                    state="normal",
                    text="Send ↑"
                )

        except queue.Empty:
            pass

        self.root.after(
            100,
            self.process_events
        )


# ==================================================
# START APPLICATION
# ==================================================

if __name__ == "__main__":

    root = tk.Tk()

    app = LocalChat(root)

    root.mainloop()
