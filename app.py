import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from tkcalendar import DateEntry
import json
import os
import subprocess
from datetime import datetime

DATA_FILE = "data.json"

class ProductivityApp:
    def __init__(self, root):
        self.root = root
        self.root.title("System Control Deck")
        self.root.geometry("650x700")
        self.root.configure(bg="#111827")
        
        # Configure Premium Dark Style
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure(".", background="#111827", foreground="#F9FAFB")
        self.style.configure("TNotebook", background="#111827", borderwidth=0)
        self.style.configure("TNotebook.Tab", background="#374151", foreground="#9CA3AF", font=("Segoe UI", 10), padding=[15, 5])
        self.style.map("TNotebook.Tab", background=[("selected", "#1F2937")], foreground=[("selected", "#3B82F6")])
        self.style.configure("TLabel", background="#111827", foreground="#E5E7EB", font=("Segoe UI", 10))
        self.style.configure("TCheckbutton", background="#111827", foreground="#E5E7EB")
        self.style.configure("TRadiobutton", background="#1F2937", foreground="#E5E7EB", font=("Segoe UI", 9))
        self.style.configure("TEntry", fieldbackground="#1F2937", foreground="#F9FAFB", borderwidth=1)
        self.style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), background="#2563EB", foreground="#FFFFFF")
        self.style.map("Action.TButton", background=[("active", "#1D4ED8")])

        # --- GLOBAL DATE SELECTOR BAR ---
        top_bar = tk.Frame(self.root, bg="#1F2937", height=50)
        top_bar.pack(fill="x", side="top")
        
        ttk.Label(top_bar, text="Target Target Date:", background="#1F2937", font=("Segoe UI", 10, "bold")).pack(side="left", padx=15, pady=10)
        self.date_picker = DateEntry(top_bar, width=12, background="#3B82F6", foreground="white", borderwidth=2, date_pattern="yyyy-mm-dd")
        self.date_picker.pack(side="left", padx=5, pady=10)
        self.date_picker.bind("<<DateEntrySelected>>", self.load_date_data)

        # --- MAIN TABBED INTERFACE ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.setup_academic_tab()
        self.setup_shorthand_tab()
        self.setup_misc_tab()

        # --- CONTROL BUTTONS BOTTOM BAR ---
        bottom_bar = tk.Frame(self.root, bg="#111827")
        bottom_bar.pack(fill="x", side="bottom", pady=10)
        
        self.status_lbl = tk.Label(bottom_bar, text="Ready to commit.", bg="#111827", fg="#9CA3AF", font=("Segoe UI", 9, "italic"))
        self.status_lbl.pack(pady=2)
        
        sync_btn = ttk.Button(bottom_bar, text="Update & Push Live Dashboard", style="Action.TButton", command=self.save_and_push, width=35)
        sync_btn.pack(pady=5)

        # Initialize Data
        self.load_date_data()

    def setup_academic_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📚 Academic Mocks")
        
        scroll_canvas = tk.Canvas(tab, bg="#111827", highlightthickness=0)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=scroll_canvas.yview)
        scroll_frame = tk.Frame(scroll_canvas, bg="#111827")
        
        scroll_frame.bind("<Configure>", lambda e: scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all")))
        scroll_canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        scroll_canvas.configure(yscrollcommand=scrollbar.set)
        
        scroll_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.academics = {}
        subjects = [
            ("english", "English Language"),
            ("arithmetic", "Quantitative Arithmetic"),
            ("ga", "General Awareness"),
            ("reasoning", "Logical Reasoning")
        ]

        for idx, (code, name) in enumerate(subjects):
            section = tk.LabelFrame(scroll_frame, text=f" {name} ", bg="#1F2937", fg="#3B82F6", font=("Segoe UI", 11, "bold"), padx=10, pady=10)
            section.pack(fill="x", expand=True, padx=10, pady=8)
            
            skip_var = tk.BooleanVar(value=True)
            chk = ttk.Checkbutton(section, text="Skip/Absent Today", variable=skip_var, command=lambda c=code: self.toggle_academic_fields(c))
            chk.grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
            
            fields = ["Desc", "Total Marks", "Obtained Marks", "Attempts", "Wrongs", "Baseline Target"]
            entries = {}
            
            for f_idx, field in enumerate(fields):
                r = (f_idx // 2) + 1
                c = (f_idx % 2) * 2
                ttk.Label(section, text=f"{field}:", background="#1F2937").grid(row=r, column=c, sticky="w", padx=5, pady=4)
                ent = ttk.Entry(section, width=14)
                ent.grid(row=r, column=c+1, padx=5, pady=4, sticky="w")
                entries[field.lower().replace(" ", "_")] = ent

            self.academics[code] = {"skip_var": skip_var, "entries": entries, "frame": section}

    def toggle_academic_fields(self, code):
        is_skipped = self.academics[code]["skip_var"].get()
        state = "disabled" if is_skipped else "normal"
        for ent in self.academics[code]["entries"].values():
            ent.configure(state=state)

    def setup_shorthand_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="✍️ Shorthand Entry")
        
        wrapper = tk.Frame(tab, bg="#1F2937", padx=20, pady=20)
        wrapper.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.sh_skip_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(wrapper, text="No Shorthand Session Logged Today", variable=self.sh_skip_var, 
                        command=self.toggle_shorthand_fields, style="TCheckbutton").pack(anchor="w", pady=5)
        
        self.sh_form = tk.Frame(wrapper, bg="#1F2937")
        self.sh_form.pack(fill="both", expand=True, pady=10)
        
        # Core form inputs
        grid_f = tk.Frame(self.sh_form, bg="#1F2937")
        grid_f.pack(fill="x", anchor="w")
        
        ttk.Label(grid_f, text="Speed (WPM):", background="#1F2937").grid(row=0, column=0, sticky="w", pady=6)
        self.sh_speed = ttk.Entry(grid_f, width=15)
        self.sh_speed.grid(row=0, column=1, padx=10, pady=6)
        
        ttk.Label(grid_f, text="Total Words:", background="#1F2937").grid(row=1, column=0, sticky="w", pady=6)
        self.sh_words = ttk.Entry(grid_f, width=15)
        self.sh_words.grid(row=1, column=1, padx=10, pady=6)
        
        ttk.Label(grid_f, text="Accuracy (%):", background="#1F2937").grid(row=2, column=0, sticky="w", pady=6)
        self.sh_accuracy = ttk.Entry(grid_f, width=15)
        self.sh_accuracy.grid(row=2, column=1, padx=10, pady=6)
        
        ttk.Label(grid_f, text="Topic Profile / Vol:", background="#1F2937").grid(row=3, column=0, sticky="w", pady=6)
        self.sh_topic = ttk.Entry(grid_f, width=35)
        self.sh_topic.grid(row=3, column=1, padx=10, pady=6, columnspan=2, sticky="w")
        
        ttk.Label(self.sh_form, text="Qualitative Execution Notes:", background="#1F2937").pack(anchor="w", pady=(15,2))
        self.sh_notes = scrolledtext.ScrolledText(self.sh_form, width=50, height=8, bg="#111827", fg="#F9FAFB", insertbackground="white", font=("Segoe UI", 10), borderwidth=0)
        self.sh_notes.pack(fill="both", expand=True, pady=5)

    def toggle_shorthand_fields(self):
        state = "disabled" if self.sh_skip_var.get() else "normal"
        self.sh_speed.configure(state=state)
        self.sh_words.configure(state=state)
        self.sh_accuracy.configure(state=state)
        self.sh_topic.configure(state=state)
        self.sh_notes.configure(state="disabled" if self.sh_skip_var.get() else "normal")

    def setup_misc_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📅 Miscellaneous Habits")
        
        self.misc_tasks = {
            "english_vocabulary": "English Vocabulary",
            "typing_practice": "Typing Speed Drills",
            "computer": "Computer Science Modules",
            "shorthand_stroke": "Shorthand Stroke Geometry"
        }
        
        self.misc_vars = {}
        
        for idx, (code, title) in enumerate(self.misc_tasks.items()):
            card = tk.Frame(tab, bg="#1F2937", padx=15, pady=15)
            card.pack(fill="x", padx=15, pady=8)
            
            ttk.Label(card, text=title, background="#1F2937", font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
            
            var = tk.StringVar(value="absent")
            self.misc_vars[code] = var
            
            r_frame = tk.Frame(card, bg="#1F2937")
            r_frame.pack(side="right")
            
            ttk.Radiobutton(r_frame, text="Present 🟢", variable=var, value="present", style="TRadiobutton").pack(side="left", padx=8)
            ttk.Radiobutton(r_frame, text="Absent 🔴", variable=var, value="absent", style="TRadiobutton").pack(side="left", padx=8)
            ttk.Radiobutton(r_frame, text="Break 🟡", variable=var, value="planned_break", style="TRadiobutton").pack(side="left", padx=8)

    def load_date_data(self, event=None):
        target_date = self.date_picker.get_date().strftime("%Y-%m-%d")
        
        # Reset UI default clear states
        for code in self.academics:
            self.academics[code]["skip_var"].set(True)
            for ent in self.academics[code]["entries"].values():
                ent.delete(0, tk.END)
            self.toggle_academic_fields(code)
            
        self.sh_skip_var.set(False)
        self.sh_speed.delete(0, tk.END)
        self.sh_words.delete(0, tk.END)
        self.sh_accuracy.delete(0, tk.END)
        self.sh_topic.delete(0, tk.END)
        self.sh_notes.delete("1.0", tk.END)
        self.toggle_shorthand_fields()
        
        for var in self.misc_vars.values():
            var.set("absent")

        if not os.path.exists(DATA_FILE):
            return

        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
                for entry in data:
                    if entry.get("date") == target_date:
                        # Load Academic
                        ac_data = entry.get("academic_data", {})
                        for code, s_data in ac_data.items():
                            if s_data and code in self.academics:
                                self.academics[code]["skip_var"].set(False)
                                self.toggle_academic_fields(code)
                                mapping = {
                                    "desc": s_data.get("mock_desc", ""),
                                    "total_marks": s_data.get("total_marks", ""),
                                    "obtained_marks": s_data.get("marks_obtained", ""),
                                    "attempts": s_data.get("total_attempt", ""),
                                    "wrongs": s_data.get("wrong_answers", ""),
                                    "baseline_target": s_data.get("baseline", "")
                                }
                                for key, val in mapping.items():
                                    self.academics[code]["entries"][key].insert(0, str(val))
                        
                        # Load Shorthand
                        sh = entry.get("shorthand_data")
                        if sh is None:
                            self.sh_skip_var.set(True)
                            self.toggle_shorthand_fields()
                        elif code in self.academics:
                            self.sh_speed.insert(0, str(sh.get("speed_wpm", "")))
                            self.sh_words.insert(0, str(sh.get("word_count", "")))
                            self.sh_accuracy.insert(0, str(sh.get("accuracy", "")))
                            self.sh_topic.insert(0, sh.get("topic", ""))
                            self.sh_notes.insert("1.0", sh.get("notes", ""))
                        
                        # Load Miscellaneous
                        m_data = entry.get("miscellaneous_data", {})
                        for m_code, var in self.misc_vars.items():
                            var.set(m_data.get(m_code, "absent"))
                        break
        except Exception as e:
            print(f"Error parsing database read: {e}")

    def save_and_push(self):
        target_date = self.date_picker.get_date().strftime("%Y-%m-%d")
        
        # Pack Academic Records
        academic_payload = {}
        for code, struct in self.academics.items():
            if struct["skip_var"].get():
                academic_payload[code] = None
            else:
                try:
                    ents = struct["entries"]
                    academic_payload[code] = {
                        "mock_desc": ents["desc"].get().strip(),
                        "total_marks": float(ents["total_marks"].get() or 0),
                        "marks_obtained": float(ents["obtained_marks"].get() or 0),
                        "total_attempt": float(ents["attempts"].get() or 0),
                        "wrong_answers": float(ents["wrongs"].get() or 0),
                        "accuracy": round((float(ents["obtained_marks"].get() or 0) / float(ents["total_marks"].get() or 1)) * 100, 1) if ents["total_marks"].get() else 0.0,
                        "baseline": float(ents["baseline_target"].get() or 0)
                    }
                except ValueError:
                    messagebox.showerror("Validation Error", f"Ensure all input figures in {code.upper()} are integers or decimals.")
                    return

        # Pack Shorthand Payload
        if self.sh_skip_var.get():
            shorthand_payload = None
        else:
            try:
                shorthand_payload = {
                    "speed_wpm": float(self.sh_speed.get() or 0),
                    "word_count": float(self.sh_words.get() or 0),
                    "accuracy": float(self.sh_accuracy.get() or 0),
                    "topic": self.sh_topic.get().strip(),
                    "notes": self.sh_notes.get("1.0", tk.END).strip()
                }
            except ValueError:
                messagebox.showerror("Validation Error", "Verify Shorthand metrics (Speed, Words, Accuracy) are clean numeric codes.")
                return

        # Pack Misc Elements
        misc_payload = {}
        for m_code, var in self.misc_vars.items():
            misc_payload[m_code] = var.get()

        new_entry = {
            "date": target_date,
            "academic_data": academic_payload,
            "shorthand_data": shorthand_payload,
            "miscellaneous_data": misc_payload
        }

        # Parse local storage append
        data = []
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r") as f:
                    data = json.load(f)
            except Exception:
                data = []

        data = [e for e in data if e.get("date") != target_date]
        data.append(new_entry)
        data.sort(key=lambda x: x["date"])

        try:
            with open(DATA_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            messagebox.showerror("Database Crash", f"Could not preserve locally: {e}")
            return

        # Trigger Automation Pipelines
        try:
            self.status_lbl.config(text="Connecting to cloud channels...", fg="#F59E0B")
            self.root.update()
            
            subprocess.run(["git", "add", "data.json"], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["git", "commit", "-m", f"data: dashboard pipeline sync {target_date}"], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            subprocess.run(["git", "push", "origin", "main"], check=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            self.status_lbl.config(text="Cloud network synchronization complete.", fg="#10B981")
            messagebox.showinfo("Success", "Metrics successfully processed. Server build takes roughly 30 seconds.")
        except subprocess.CalledProcessError:
            self.status_lbl.config(text="Preserved locally. Git handshakes failed.", fg="#EF4444")
            messagebox.showwarning("Network Sync Fail", "Metrics successfully preserved locally, but network transmission dropped out. Check connection speeds.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProductivityApp(root)
    root.mainloop()