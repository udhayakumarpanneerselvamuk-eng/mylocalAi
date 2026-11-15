
import tkinter as tk
from tkinter import ttk
import threading
import queue
import ollama

# ---------------- CONFIGURATION ----------------

MODEL = "llama3.2"  # Change to your installed Ollama model

BG = "#212121"
SIDEBAR = "#171717"
PANEL = "#2f2f2f"
TEXT = "#ececec"
MUTED = "#a0a0a0"
ACCENT = "#10a37f"

# ---------------- APPLICATION ----------------

class LocalChat:

    def __init__(self, root):
        self.root = root
        self.root.title("My Local AI")
        self.root.geometry("1050x720")
        self.root.minsize(700, 500)
        self.root.configure(bg=BG)

        self.messages = []
        self.events = queue.Queue()
        self.busy = False

        self.build_ui()
        self.root.after(100, self.process_events)

    # ---------------- UI ----------------

    def build_ui(self):

        # Sidebar
        self.sidebar = tk.Frame(
            self.root,
            bg=SIDEBAR,
            width=220
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        tk.Label(
            self.sidebar,
            text="✦ My Local AI",
            bg=SIDEBAR,
            fg="white",
            font=("Segoe UI", 17, "bold")
        ).pack(pady=25)

        tk.Button(
            self.sidebar,
            text="+ New Chat",
            bg=PANEL,
            fg=TEXT,
            activebackground="#444444",
            activeforeground="white",
            relief="flat",
            font=("Segoe UI", 11),
            command=self.new_chat
        ).pack(fill="x", padx=15, pady=10)

        tk.Label(
            self.sidebar,
            text=f"Model: {MODEL}",
            bg=SIDEBAR,
            fg=MUTED,
            font=("Segoe UI", 10)
        ).pack(side="bottom", pady=20)

        # Main area
        self.main = tk.Frame(self.root, bg=BG)
        self.main.pack(side="left", fill="both", expand=True)

        # Header
        header = tk.Frame(self.main, bg=BG, height=60)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Chat",
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 15, "bold")
        ).pack(side="left", padx=25, pady=15)

        # Scrollable chat area
        self.canvas = tk.Canvas(
            self.main,
            bg=BG,
            highlightthickness=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(
            self.main,
            orient="vertical",
            command=self.canvas.yview
        )
        scrollbar.pack(side="right", fill="y")

        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.chat_frame = tk.Frame(self.canvas, bg=BG)

        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.chat_frame,
            anchor="nw"
        )

        self.chat_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.itemconfigure(
                self.canvas_window,
                width=e.width
            )
        )

        # Input section
        bottom = tk.Frame(self.main, bg=BG)
        bottom.pack(fill="x", padx=40, pady=20)

        self.input_box = tk.Text(
            bottom,
            height=3,
            bg=PANEL,
            fg=TEXT,
            insertbackground="white",
            font=("Segoe UI", 12),
            relief="flat",
            wrap="word",
            padx=15,
            pady=12
        )
        self.input_box.pack(
            side="left",
            fill="x",
            expand=True
        )

        self.input_box.bind("<Return>", self.enter_pressed)

        self.send_button = tk.Button(
            bottom,
            text="↑",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 18, "bold"),
            relief="flat",
            width=3,
            command=self.send_message
        )
        self.send_button.pack(
            side="right",
            padx=(10, 0),
            fill="y"
        )

        self.input_box.focus_set()

        self.add_message(
            "assistant",
            f"Hello! I'm your local AI assistant.\n\n"
            f"I'm running locally using Ollama ({MODEL}). "
            "How can I help you today?"
        )

    # ---------------- CHAT UI ----------------

    def add_message(self, role, content):

        outer = tk.Frame(self.chat_frame, bg=BG)
        outer.pack(fill="x", padx=30, pady=12)

        is_user = role == "user"

        bubble = tk.Frame(
            outer,
            bg="#303030" if is_user else BG
        )

        bubble.pack(
            anchor="e" if is_user else "w",
            padx=(100, 0) if is_user else (0, 100)
        )

        tk.Label(
            bubble,
            text="You" if is_user else "AI Assistant",
            bg=bubble["bg"],
            fg=ACCENT if is_user else "#8ab4f8",
            font=("Segoe UI", 10, "bold")
        ).pack(anchor="w", padx=12, pady=(8, 3))

        label = tk.Label(
            bubble,
            text=content,
            bg=bubble["bg"],
            fg=TEXT,
            font=("Segoe UI", 11),
            justify="left",
            wraplength=650,
            anchor="w",
            padx=12,
            pady=8
        )
        label.pack(anchor="w")

        self.root.update_idletasks()
        self.canvas.yview_moveto(1.0)

        return label

    # ---------------- SEND MESSAGE ----------------

    def enter_pressed(self, event):

        if event.state & 0x0001:
            return

        self.send_message()
        return "break"

    def send_message(self):

        if self.busy:
            return

        prompt = self.input_box.get("1.0", "end-1c").strip()

        if not prompt:
            return

        self.input_box.delete("1.0", "end")

        self.messages.append({
            "role": "user",
            "content": prompt
        })

        self.add_message("user", prompt)

        self.busy = True
        self.send_button.config(state="disabled")

        # Create an empty assistant message
        self.response_label = self.add_message(
            "assistant",
            "Thinking..."
        )

        threading.Thread(
            target=self.generate_response,
            daemon=True
        ).start()

    # ---------------- OLLAMA STREAMING ----------------

    def generate_response(self):

        try:
            stream = ollama.chat(
                model=MODEL,
                messages=self.messages,
                stream=True
            )

            full_response = ""

            for chunk in stream:

                content = chunk.message.content

                if content:
                    full_response += content

                    self.events.put((
                        "token",
                        content
                    ))

            self.messages.append({
                "role": "assistant",
                "content": full_response
            })

            self.events.put(("done", None))

        except Exception as error:

            self.events.put((
                "error",
                str(error)
            ))

    # ---------------- UI THREAD EVENTS ----------------

    def process_events(self):

        try:
            while True:

                event, data = self.events.get_nowait()

                if event == "token":

                    current = self.response_label.cget("text")

                    if current == "Thinking...":
                        current = ""

                    self.response_label.config(
                        text=current + data
                    )

                    self.canvas.update_idletasks()
                    self.canvas.yview_moveto(1.0)

                elif event == "done":

                    self.busy = False
                    self.send_button.config(state="normal")

                elif event == "error":

                    self.response_label.config(
                        text="Error: " + data
                    )

                    self.busy = False
                    self.send_button.config(state="normal")

        except queue.Empty:
            pass

        self.root.after(50, self.process_events)

    # ---------------- NEW CHAT ----------------

    def new_chat(self):

        if self.busy:
            return

        self.messages.clear()

        for widget in self.chat_frame.winfo_children():
            widget.destroy()

        self.add_message(
            "assistant",
            "New conversation started. What would you like to discuss?"
        )


# ---------------- RUN APPLICATION ----------------

if __name__ == "__main__":

    root = tk.Tk()

    app = LocalChat(root)

    root.mainloop()
