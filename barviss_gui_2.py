"""
BARVISS AI Assistant - Full Voice GUI
======================================
Wake words : "hey barviss"  OR  "initiate"
After wake : speak your command within 6 seconds

Install once:
    pip install SpeechRecognition pyttsx3 pyaudio

Windows pyaudio fix if pip fails:
    pip install pipwin && pipwin install pyaudio

Linux extras:
    sudo apt-get install python3-pyaudio portaudio19-dev espeak python3-tk
"""

import sys, os, subprocess, platform
PLATFORM = platform.system()

# ── dependency check ─────────────────────────────────────────────────────────
def _check():
    try:
        import tkinter
    except ImportError:
        print("ERROR: tkinter not found.")
        print("  Windows : reinstall Python, tick 'tcl/tk' option")
        print("  Linux   : sudo apt-get install python3-tk")
        print("  Mac     : brew install python-tk")
        sys.exit(1)
    missing = []
    for pkg in ["speech_recognition","pyttsx3","pyaudio"]:
        try: __import__(pkg)
        except ImportError: missing.append(pkg.replace("speech_recognition","SpeechRecognition"))
    if missing:
        print("="*55)
        print("Missing packages:", ", ".join(missing))
        print("Run:  pip install", " ".join(missing))
        if "pyaudio" in missing:
            print("  Windows alt:  pip install pipwin && pipwin install pyaudio")
        print("="*55)
        input("Press Enter to open GUI without voice, or Ctrl+C to install first: ")

_check()

# ── standard imports ──────────────────────────────────────────────────────────
import tkinter as tk
import math, threading, time, datetime, random, webbrowser, queue

SR_OK = TTS_OK = False
try:
    import speech_recognition as sr
    SR_OK = True
except ImportError:
    pass
try:
    import pyttsx3
    TTS_OK = True
except ImportError:
    pass

# ─────────────────────────────────────────────
#  COLORS
# ─────────────────────────────────────────────
BG        = "#020d1a"
CYAN      = "#00d4ff"
CYAN_DIM  = "#007a99"
CYAN_GLOW = "#00aacc"
GREEN     = "#00ff88"
RED       = "#ff3333"
YELLOW    = "#ffcc00"
TEXT_W    = "#e0f7ff"
TEXT_DIM  = "#4a7a8a"
BORDER    = "#0a4060"
BORDER2   = "#0d5070"
PANEL_BG  = "#020f1e"
ACCENT_BG = "#031828"

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def round_rect(canvas, x1, y1, x2, y2, r=10, **kw):
    pts = [
        x1+r,y1,  x2-r,y1,  x2,y1,    x2,y1+r,
        x2,y2-r,  x2,y2,    x2-r,y2,  x1+r,y2,
        x1,y2,    x1,y2-r,  x1,y1+r,  x1,y1,
    ]
    return canvas.create_polygon(pts, smooth=True, **kw)

def open_url(url):
    webbrowser.open(url)

def open_app(win, mac, linux_list):
    try:
        if PLATFORM=="Windows":   subprocess.Popen(win, shell=True)
        elif PLATFORM=="Darwin":  subprocess.Popen(mac, shell=True)
        else:
            for cmd in linux_list:
                try: subprocess.Popen(cmd.split()); return
                except FileNotFoundError: continue
    except Exception as e:
        print(f"[open_app] {e}")

# ─────────────────────────────────────────────
#  TTS  (single engine, queue-based)
# ─────────────────────────────────────────────
_tts_q   = queue.Queue()
_tts_eng = None

def _tts_worker():
    global _tts_eng
    if not TTS_OK:
        return
    try:
        _tts_eng = pyttsx3.init()
        _tts_eng.setProperty("rate", 160)
        _tts_eng.setProperty("volume", 0.95)
        voices = _tts_eng.getProperty("voices")
        for v in voices:
            if any(k in v.name.lower() for k in ["zira","female","woman","hazel"]):
                _tts_eng.setProperty("voice", v.id)
                break
    except Exception as e:
        print(f"[TTS init] {e}")
        return
    while True:
        text = _tts_q.get()
        if text is None:
            break
        try:
            _tts_eng.say(text)
            _tts_eng.runAndWait()
        except Exception as e:
            print(f"[TTS speak] {e}")

threading.Thread(target=_tts_worker, daemon=True).start()

def speak(text):
    print(f"[BARVISS says]: {text}")
    if TTS_OK:
        _tts_q.put(text)

# ─────────────────────────────────────────────
#  COMMAND HANDLER
# ─────────────────────────────────────────────
def handle_command(text, app):
    """Returns (reply, label) tuple."""
    t = text.lower().strip()
    if not t:
        return ("I didn't catch that. Please try again.", "No input")

    # YouTube
    if "youtube" in t:
        if "play" in t:
            q = t.split("play",1)[-1].replace("on youtube","").replace("youtube","").strip()
            if q:
                open_url(f"https://www.youtube.com/results?search_query={q.replace(' ','+')}")
                return (f"Playing {q} on YouTube.", "YouTube Play")
        open_url("https://www.youtube.com")
        return ("Opening YouTube.", "Open YouTube")

    # Google search
    if "google" in t or "search" in t:
        q = ""
        for kw in ["search for","search on google","google search","search","google"]:
            if kw in t:
                q = t.split(kw,1)[-1].strip()
                break
        if q:
            open_url(f"https://www.google.com/search?q={q.replace(' ','+')}")
            return (f"Searching Google for: {q}", "Google Search")
        open_url("https://www.google.com")
        return ("Opening Google.", "Open Google")

    # Spotify
    if "spotify" in t:
        open_url("https://open.spotify.com")
        return ("Opening Spotify.", "Open Spotify")

    # Notepad
    if "notepad" in t or "text editor" in t:
        open_app("notepad.exe","open -a TextEdit",
                 ["gedit","kate","mousepad","xed","leafpad","nano"])
        return ("Opening Notepad.", "Open Notepad")

    # Calculator
    if "calculator" in t or "calculate" in t:
        open_app("calc.exe","open -a Calculator",
                 ["gnome-calculator","kcalc","galculator","xcalc"])
        return ("Opening Calculator.", "Calculator")

    # File manager
    if ("file manager" in t or "file explorer" in t or
            ("file" in t and "open" in t)):
        open_app("explorer","open "+os.path.expanduser("~"),
                 ["nautilus","dolphin","thunar","nemo","pcmanfm"])
        return ("Opening File Manager.", "File Manager")

    # Time
    if "time" in t and "system" not in t:
        now = datetime.datetime.now().strftime("%I:%M %p")
        return (f"The time is {now}.", "Tell Time")

    # Date
    if "date" in t or "today" in t:
        d = datetime.datetime.now().strftime("%A, %d %B %Y")
        return (f"Today is {d}.", "Tell Date")

    # System status / CPU / RAM
    if "system" in t or "status" in t or "cpu" in t or "ram" in t:
        return (f"CPU is at {app._cpu} percent, RAM at {app._ram} percent, "
                f"Network at {app._net} percent.", "System Status")

    # Volume
    if "volume up" in t or "louder" in t or "increase volume" in t:
        _vol("+"); return ("Volume increased.", "Volume Up")
    if "volume down" in t or "quieter" in t or "decrease volume" in t:
        _vol("-"); return ("Volume decreased.", "Volume Down")
    if "mute" in t:
        _mute(); return ("Muted.", "Mute")

    # Weather
    if "weather" in t:
        open_url("https://www.google.com/search?q=weather+today")
        return ("Checking weather.", "Weather")

    # Screenshot
    if "screenshot" in t:
        if PLATFORM=="Windows":   subprocess.Popen(["snippingtool"])
        elif PLATFORM=="Darwin":  subprocess.Popen(["screencapture","-i","~/Desktop/ss.png"])
        else:                     subprocess.Popen(["gnome-screenshot"])
        return ("Taking screenshot.", "Screenshot")

    # Lock
    if "lock" in t:
        if PLATFORM=="Windows":
            subprocess.run(["rundll32","user32.dll,LockWorkStation"])
        elif PLATFORM=="Darwin":
            subprocess.run(["pmset","displaysleepnow"])
        else:
            subprocess.Popen(["xdg-screensaver","lock"])
        return ("Screen locked.", "Lock Screen")

    # Restart
    if "restart" in t or "reboot" in t:
        def _do():
            time.sleep(5)
            if PLATFORM=="Windows": subprocess.run(["shutdown","/r","/t","0"])
            else: subprocess.run(["sudo","reboot"])
        threading.Thread(target=_do,daemon=True).start()
        return ("Restarting in 5 seconds!", "Restart")

    # Shutdown
    if any(w in t for w in ["shutdown","shut down","power off","turn off the laptop",
                              "switch off","turn off computer"]):
        def _do():
            time.sleep(5)
            if PLATFORM=="Windows": subprocess.run(["shutdown","/s","/t","0"])
            elif PLATFORM=="Darwin": subprocess.run(["sudo","shutdown","-h","now"])
            else: subprocess.run(["sudo","shutdown","-h","now"])
        threading.Thread(target=_do,daemon=True).start()
        return ("Shutting down in 5 seconds!", "Shutdown")

    # Hide / close
    if "close barviss" in t or "hide barviss" in t or "go to sleep" in t:
        app.after(800, app.withdraw)
        return ("Minimizing. Say 'Hey Barviss' or 'Initiate' to wake me.", "Hide")

    # Greetings
    if any(t.startswith(w) for w in ["hello","hi","how are you","what's up","good"]):
        h = datetime.datetime.now().hour
        g = "Good morning" if h<12 else "Good afternoon" if h<17 else "Good evening"
        return (f"{g}, Prajwal! How can I help?", "Greeting")

    # Joke
    if "joke" in t:
        return (random.choice([
            "Why do programmers prefer dark mode? Light attracts bugs!",
            "I told my PC I needed a break. Now it sends me Kit-Kat ads.",
            "Why did the coder go broke? He used up all his cache.",
            "There are 10 types of people: those who get binary and those who don't.",
        ]), "Joke")

    # Identity
    if "who are you" in t or "what are you" in t or "your name" in t:
        return ("I am Barviss, your personal AI desktop assistant!", "Identity")

    return (f"Sorry, I don't know how to: {text}", "Unknown")


def _vol(d):
    if PLATFORM=="Linux":
        subprocess.run(["amixer","-q","sset","Master","10%+" if d=="+" else "10%-"])
    elif PLATFORM=="Darwin":
        delta="+10" if d=="+" else "-10"
        subprocess.run(["osascript","-e",
            f"set volume output volume (output volume of (get volume settings) {delta})"])

def _mute():
    if PLATFORM=="Linux": subprocess.run(["amixer","-q","sset","Master","toggle"])
    elif PLATFORM=="Darwin": subprocess.run(["osascript","-e","set volume with output muted"])


# ─────────────────────────────────────────────
#  VOICE LISTENER  (background thread)
# ─────────────────────────────────────────────
# All wake words — say ANY of these to activate
WAKE_WORDS = [
    "hey barviss", "hay barviss", "hey barvis",
    "hey bars",    "a barviss",   "initiate",
    "hey initiate","barviss",     "hi barviss",
    "ok barviss",  "wake up",     "activate",
]

class VoiceListener(threading.Thread):
    """
    Two-phase listener:
      Phase 1 (idle)  → listen for a wake word
      Phase 2 (awake) → listen for a command (8-second window)

    Runs in its own daemon thread; communicates with the GUI
    via app.after() so everything stays thread-safe.
    """

    def __init__(self, app):
        super().__init__(daemon=True, name="VoiceListener")
        self.app   = app
        self.alive = True
        self._phase = "idle"   # "idle" | "command"

    # ── internal helpers ──────────────────────────────────────────────────────
    def _update_status(self, msg, col=CYAN_DIM):
        self.app.after(0, lambda m=msg,c=col: self.app.set_status(m, c))

    def _set_mic_color(self, col):
        self.app.after(0, lambda c=col: self.app.set_mic_color(c))

    def _try_recognize(self, recognizer, audio):
        """Try Google first, fall back to Sphinx (offline) if available."""
        try:
            return recognizer.recognize_google(audio).lower()
        except sr.RequestError:
            # no internet — try offline engine
            try:
                return recognizer.recognize_sphinx(audio).lower()
            except Exception:
                raise

    # ── main loop ─────────────────────────────────────────────────────────────
    def run(self):
        if not SR_OK:
            self._update_status("SpeechRecognition not installed", RED)
            return

        # build recognizer
        r = sr.Recognizer()
        r.energy_threshold          = 300    # lower = more sensitive
        r.dynamic_energy_threshold  = True   # auto-adjust to ambient noise
        r.pause_threshold           = 0.6    # seconds of silence = end of phrase
        r.phrase_threshold          = 0.3
        r.non_speaking_duration     = 0.4

        # open microphone
        try:
            mic = sr.Microphone()
        except Exception as e:
            self._update_status(f"Mic error: {e}", RED)
            return

        self._update_status("Calibrating mic...", CYAN_DIM)
        try:
            with mic as src:
                r.adjust_for_ambient_noise(src, duration=2)
            print(f"[Mic] energy_threshold set to {r.energy_threshold:.0f}")
        except Exception as e:
            print(f"[Mic calibration] {e}")

        self._update_status("Say 'Hey Barviss' or 'Initiate'", CYAN_DIM)
        self._set_mic_color(CYAN_DIM)

        while self.alive:
            try:
                # ── PHASE 1: listen for wake word ─────────────────────────
                if self._phase == "idle":
                    self._update_status("Waiting... Say 'Hey Barviss'", CYAN_DIM)
                    self._set_mic_color(CYAN_DIM)

                    with mic as src:
                        try:
                            audio = r.listen(src, timeout=None,
                                             phrase_time_limit=5)
                        except sr.WaitTimeoutError:
                            continue

                    try:
                        text = self._try_recognize(r, audio)
                    except sr.UnknownValueError:
                        continue
                    except Exception as e:
                        print(f"[Wake recognize] {e}")
                        time.sleep(1)
                        continue

                    print(f"[Idle heard]: '{text}'")

                    if any(w in text for w in WAKE_WORDS):
                        self._phase = "command"
                        self._set_mic_color(GREEN)
                        self._update_status("Listening for command...", GREEN)
                        self.app.after(0, self.app.on_wake)

                # ── PHASE 2: listen for command ───────────────────────────
                elif self._phase == "command":
                    self._set_mic_color(GREEN)
                    self._update_status("Speak your command now!", GREEN)

                    with mic as src:
                        # give user 8 seconds to start speaking
                        try:
                            audio = r.listen(src, timeout=8,
                                             phrase_time_limit=10)
                        except sr.WaitTimeoutError:
                            print("[Command] timed out waiting")
                            self._phase = "idle"
                            self._update_status("Timed out. Say wake word again.", RED)
                            self._set_mic_color(CYAN_DIM)
                            speak("I didn't hear a command. Say Hey Barviss to try again.")
                            continue

                    try:
                        text = self._try_recognize(r, audio)
                        print(f"[Command heard]: '{text}'")
                    except sr.UnknownValueError:
                        self._phase = "idle"
                        self._update_status("Didn't understand. Try again.", RED)
                        self._set_mic_color(CYAN_DIM)
                        speak("Sorry, I couldn't understand. Say Hey Barviss and try again.")
                        continue
                    except Exception as e:
                        print(f"[Command recognize] {e}")
                        self._phase = "idle"
                        time.sleep(1)
                        continue

                    self._phase = "idle"
                    # send to app on main thread
                    self.app.after(0, lambda t=text: self.app.on_command(t))

            except Exception as e:
                print(f"[VoiceListener] unexpected error: {e}")
                time.sleep(2)


# ─────────────────────────────────────────────
#  MAIN APP
# ─────────────────────────────────────────────
class BarvissApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("BARVISS – AI ASSISTANT")
        self.geometry("1340x840+40+40")
        self.resizable(False, False)
        self.configure(bg=BG)

        # state
        self._cpu=23; self._ram=46; self._bat=85; self._disk=62; self._net=98
        self._angle=0.0; self._dot_phase=0.0
        self._listen_blink=True; self._tick=0
        self._wave_items=[]; self._arc_items=[]; self._arc2_items=[]
        self._dot_items=[]; self._greet_wave=[]; self._mic_ring_dots=[]
        self._bars={}; self._pct_lbl={}
        self._act_texts=[]; self._act_dots=[]
        self._activity_log=[
            ("--:--","System Booted"),
            ("--:--","All Systems Online"),
            ("--:--","Barviss Activated"),
            ("--:--","Listening..."),
        ]

        self._build_ui()

        # start voice listener
        self._vl = VoiceListener(self)
        if SR_OK:
            self._vl.start()
        else:
            self.set_status("No voice – install SpeechRecognition", RED)

        self._animate()
        self.protocol("WM_DELETE_WINDOW", self._quit)

        # update activity timestamps
        ts = datetime.datetime.now().strftime("%I:%M:%S %p")
        self._activity_log = [(ts, ev) for _,ev in self._activity_log]
        self._refresh_activity()

        # startup greeting
        h = datetime.datetime.now().hour
        g = "Good morning" if h<12 else "Good afternoon" if h<17 else "Good evening"
        speak(f"{g} Prajwal! Barviss is ready. Say Hey Barviss or Initiate to begin.")

    # ── voice callbacks (called from listener thread via after()) ─────────────
    def on_wake(self):
        self.deiconify(); self.lift(); self.focus_force()
        self._log("Wake word detected")
        self._set_input("Speak your command now...")
        self.set_status("Listening for command...", GREEN)
        # flash mic panel green
        if hasattr(self, "_mic_circle"):
            self.main.itemconfig(self._mic_circle, outline=GREEN)

    def on_command(self, text):
        if hasattr(self, "_mic_circle"):
            self.main.itemconfig(self._mic_circle, outline=CYAN)
        reply, label = handle_command(text, self)
        self._set_input(reply[:65])
        self._log(label)
        self.set_status("Say 'Hey Barviss' or 'Initiate'", CYAN_DIM)
        speak(reply)

    def set_status(self, msg, col=CYAN_DIM):
        if hasattr(self, "_listen_lbl"):
            self.main.itemconfig(self._listen_lbl, text=msg[:40], fill=col)

    def set_mic_color(self, col):
        if hasattr(self, "_mic_circle"):
            self.main.itemconfig(self._mic_circle, outline=col)

    def _set_input(self, text):
        if hasattr(self, "_input_var"):
            self._input_var.set(text)

    def _log(self, msg):
        ts = datetime.datetime.now().strftime("%I:%M:%S %p")
        self._activity_log.append((ts, msg))
        if len(self._activity_log)>6:
            self._activity_log = self._activity_log[-6:]
        self._refresh_activity()

    def _quit(self):
        self._vl.alive = False
        _tts_q.put(None)
        self.destroy()

    # ── TYPE-IN fallback ──────────────────────────────────────────────────────
    def _type_submit(self):
        text = self._input_var.get().strip()
        if text and not text.startswith(("Say","Speak","Waiting","Listening")):
            reply, label = handle_command(text, self)
            self._set_input(reply[:65])
            self._log(label)
            speak(reply)

    # ══════════════════════════════════════════
    #  UI
    # ══════════════════════════════════════════
    def _build_ui(self):
        self._build_titlebar()
        self.main = tk.Canvas(self, bg=BG, highlightthickness=0,
                              width=1340, height=810)
        self.main.place(x=0, y=30)
        self._draw_bg()
        self._build_system_status()
        self._build_voice_panel()
        self._build_commands_panel()
        self._build_center_ring()
        self._build_input_bar()
        self._build_quick_btns()
        self._build_clock_panel()
        self._build_greeting_panel()
        self._build_activity_panel()
        self._build_network_panel()

    def _build_titlebar(self):
        tb = tk.Canvas(self, bg="#010b14", highlightthickness=0,
                       width=1340, height=30)
        tb.place(x=0, y=0)
        tb.create_text(670,15,text="BARVISS  AI ASSISTANT",
                       fill=CYAN,font=("Consolas",11,"bold"),anchor="center")
        tb.create_rectangle(1295,8,1305,22,fill=TEXT_DIM,outline="")
        tb.create_rectangle(1309,8,1319,22,fill=TEXT_DIM,outline="")
        cb = tb.create_rectangle(1323,8,1333,22,fill=RED,outline="")
        tb.tag_bind(cb,"<Button-1>",lambda e:self._quit())
        self._dx=self._dy=0
        tb.bind("<ButtonPress-1>",
                lambda e: (setattr(self,"_dx",e.x),setattr(self,"_dy",e.y)))
        tb.bind("<B1-Motion>",
                lambda e: self.geometry(
                    f"+{self.winfo_x()+e.x-self._dx}+{self.winfo_y()+e.y-self._dy}"))

    def _draw_bg(self):
        c=self.main
        for y in range(0,810,40): c.create_line(0,y,1340,y,fill="#061822")
        for x in range(0,1340,40): c.create_line(x,0,x,810,fill="#061822")
        for path in [
            [(30,0),(30,20),(60,20),(60,10),(120,10)],
            [(0,60),(20,60),(20,100)],
            [(0,750),(20,750),(20,720),(60,720),(60,810)],
            [(1310,0),(1310,20),(1280,20),(1280,10),(1220,10)],
            [(1340,60),(1320,60),(1320,100)],
            [(1340,750),(1320,750),(1320,720),(1280,720),(1280,810)],
        ]:
            c.create_line(path,fill=CYAN_DIM,width=1)

    def _panel(self,x,y,w,h,title=None,r=8):
        c=self.main
        round_rect(c,x-1,y-1,x+w+1,y+h+1,r+1,fill="",outline=CYAN_DIM,width=1)
        round_rect(c,x,y,x+w,y+h,r,fill=PANEL_BG,outline=BORDER2,width=1)
        c.create_line(x+r,y,x+w-r,y,fill=CYAN,width=1)
        for ox,oy,a in [(x,y,180),(x+w,y,270),(x,y+h,90),(x+w,y+h,0)]:
            c.create_arc(ox-6,oy-6,ox+6,oy+6,start=a,extent=90,
                         style="arc",outline=CYAN,width=1)
        if title:
            c.create_rectangle(x+12,y-1,x+12+len(title)*8+12,y+16,
                                fill=PANEL_BG,outline="")
            c.create_text(x+18,y+7,text=title,
                          fill=CYAN,font=("Consolas",8,"bold"),anchor="w")
        for i in range(3):
            c.create_oval(x+w-22+i*7,y+5,x+w-18+i*7,y+9,fill=CYAN_DIM,outline="")

    def _build_system_status(self):
        px,py,pw,ph=18,10,305,220
        self._panel(px,py,pw,ph,"SYSTEM STATUS")
        c=self.main
        rows=[("CPU","⏱"),("RAM","🖥"),("BATTERY","🔋"),("DISK","💾"),("NETWORK","📶")]
        for i,(name,icon) in enumerate(rows):
            ry=py+32+i*34
            c.create_text(px+18,ry+8,text=icon,fill=CYAN,
                          font=("Segoe UI Symbol",9),anchor="w")
            c.create_text(px+38,ry+8,text=name,fill=TEXT_W,
                          font=("Consolas",8,"bold"),anchor="w")
            bx1,bx2=px+110,px+pw-45
            c.create_rectangle(bx1,ry+3,bx2,ry+13,fill="#041830",outline=BORDER,width=1)
            bar=c.create_rectangle(bx1+1,ry+4,bx1+1,ry+12,fill=CYAN,outline="")
            pct=c.create_text(px+pw-38,ry+8,text="0%",fill=CYAN,
                               font=("Consolas",8,"bold"),anchor="w")
            self._bars[name]=(bar,bx1+1,ry+4,bx2-1,ry+12)
            self._pct_lbl[name]=pct
        c.create_oval(px+18,py+ph-26,px+26,py+ph-18,fill=GREEN,outline="")
        c.create_text(px+32,py+ph-22,text="SYSTEM ONLINE",
                      fill=GREEN,font=("Consolas",8,"bold"),anchor="w")
        for n,v in [("CPU",23),("RAM",46),("BATTERY",85),("DISK",62),("NETWORK",98)]:
            self._set_bar(n,v)

    def _set_bar(self,name,pct):
        bar,bx1,by1,bx2,by2=self._bars[name]
        fw=int((bx2-bx1)*pct/100)
        col=GREEN if pct<50 else YELLOW if pct<80 else RED
        if name=="BATTERY": col=GREEN if pct>50 else YELLOW if pct>20 else RED
        self.main.coords(bar,bx1,by1,bx1+fw,by2)
        self.main.itemconfig(bar,fill=col)
        self.main.itemconfig(self._pct_lbl[name],text=f"{pct}%")

    def _build_voice_panel(self):
        px,py,pw,ph=18,245,305,145
        self._panel(px,py,pw,ph,"VOICE STATUS")
        c=self.main
        cx=px+pw//2; cy=py+65
        c.create_oval(cx-38,cy-38,cx+38,cy+38,outline=CYAN_DIM,width=1)
        c.create_oval(cx-30,cy-30,cx+30,cy+30,outline=CYAN,width=1)
        self._mic_circle=c.create_oval(cx-24,cy-24,cx+24,cy+24,
                                        fill=ACCENT_BG,outline=CYAN,width=2)
        # mic icon
        c.create_rectangle(cx-7,cy-16,cx+7,cy+4,fill=CYAN,outline="")
        c.create_arc(cx-12,cy-6,cx+12,cy+14,start=0,extent=-180,
                     style="arc",outline=CYAN,width=2)
        c.create_line(cx,cy+13,cx,cy+20,fill=CYAN,width=2)
        c.create_line(cx-8,cy+20,cx+8,cy+20,fill=CYAN,width=2)
        for ang in range(0,360,20):
            a=math.radians(ang)
            dot=c.create_oval(cx+44*math.cos(a)-1.5,cy+44*math.sin(a)-1.5,
                               cx+44*math.cos(a)+1.5,cy+44*math.sin(a)+1.5,
                               fill=CYAN_DIM,outline="")
            self._mic_ring_dots.append((dot,cx,cy,44,ang))
        self._listen_lbl=c.create_text(cx,py+ph-18,
                                        text="Initializing..." if SR_OK else "No voice",
                                        fill=CYAN_DIM,font=("Consolas",8,"bold"),
                                        anchor="center")

    def _build_commands_panel(self):
        px,py,pw,ph=18,405,305,385
        self._panel(px,py,pw,ph,"COMMANDS")
        c=self.main
        cmds=[("yt","Open YouTube"),("yt","Play a YouTube video"),
              ("g","Search on Google"),("sp","Open Spotify"),
              ("pwr","Shutdown Laptop"),("rst","Restart Laptop"),
              ("clk","Tell me the time"),("sys","Show system status"),
              ("np","Open Notepad")]
        gc=["#4285F4","#EA4335","#FBBC05","#34A853"]
        for i,(itype,label) in enumerate(cmds):
            ry=py+30+i*38
            if itype=="yt":
                c.create_rectangle(px+18,ry,px+34,ry+14,fill="#ff0000",outline="")
                c.create_polygon(px+23,ry+2,px+23,ry+12,px+33,ry+7,
                                 fill="white",outline="")
            elif itype=="g":
                for ga,gco in zip([0,90,180,270],gc):
                    c.create_arc(px+18,ry,px+34,ry+14,start=ga,extent=90,
                                 style="arc",outline=gco,width=2)
            elif itype=="sp":
                c.create_oval(px+20,ry+1,px+33,ry+13,fill="#1db954",outline="")
                c.create_text(px+26,ry+7,text="♫",fill="white",
                              font=("Segoe UI Symbol",8),anchor="center")
            else:
                s={"pwr":"⏻","rst":"↺","clk":"◷","sys":"▐","np":"☰"}.get(itype,"•")
                c.create_text(px+26,ry+7,text=s,fill=CYAN,
                              font=("Segoe UI Symbol",10),anchor="center")
            c.create_text(px+42,ry+7,text=label,fill=TEXT_W,
                          font=("Consolas",9),anchor="w")

    def _build_center_ring(self):
        cx,cy=670,370
        self._rcx,self._rcy=cx,cy
        c=self.main
        for r,col in [(230,"#0a2030"),(220,BORDER),(210,"#0a2535")]:
            c.create_oval(cx-r,cy-r,cx+r,cy+r,outline=col,width=1,fill="")
        for r,col in [(180,"#00293d"),(170,"#003850"),(160,"#004060"),(155,"#004a70")]:
            c.create_oval(cx-r,cy-r,cx+r,cy+r,outline=col,width=2,fill="")
        self._ring1=c.create_oval(cx-150,cy-150,cx+150,cy+150,
                                   outline=CYAN,width=3,fill="")
        c.create_oval(cx-140,cy-140,cx+140,cy+140,outline=CYAN_GLOW,width=1,fill="")
        c.create_oval(cx-130,cy-130,cx+130,cy+130,outline=CYAN_DIM,width=1,fill="")
        c.create_oval(cx-125,cy-125,cx+125,cy+125,fill=BG,outline=BORDER2,width=1)
        c.create_oval(cx-100,cy-100,cx+100,cy+100,outline=CYAN_DIM,width=1,fill="")
        for i,col in enumerate([CYAN,CYAN_GLOW,CYAN_DIM,"#005577"]):
            a=c.create_arc(cx-148,cy-148,cx+148,cy+148,
                            start=i*90,extent=60,style="arc",outline=col,width=3)
            self._arc_items.append(a)
        for i,col in enumerate([CYAN_DIM,CYAN,"#003344"]):
            a=c.create_arc(cx-120,cy-120,cx+120,cy+120,
                            start=i*120,extent=45,style="arc",outline=col,width=2)
            self._arc2_items.append(a)
        c.create_text(cx,cy-18,text="BARVISS",fill=CYAN,
                      font=("Consolas",22,"bold"),anchor="center")
        c.create_text(cx,cy+10,text="ONLINE",fill=GREEN,
                      font=("Consolas",10,"bold"),anchor="center")
        for _ in range(60):
            self._wave_items.append(c.create_line(0,0,0,0,fill=CYAN,width=1))
        for ang in range(0,360,6):
            a=math.radians(ang)
            r1=152 if ang%30==0 else 155; r2=162 if ang%30==0 else 158
            c.create_line(cx+r1*math.cos(a),cy+r1*math.sin(a),
                          cx+r2*math.cos(a),cy+r2*math.sin(a),
                          fill=CYAN if ang%30==0 else CYAN_DIM,width=1)
        for ang in [210,150,330,30]:
            a=math.radians(ang)
            c.create_line(cx+155*math.cos(a),cy+155*math.sin(a),
                          cx+335*math.cos(a),cy+335*math.sin(a),
                          fill=CYAN_DIM,width=1,dash=(3,4))

    def _build_input_bar(self):
        px,py,pw,ph=340,680,640,44
        c=self.main
        round_rect(c,px,py,px+pw,py+ph,6,fill=ACCENT_BG,outline=BORDER2,width=1)
        c.create_line(px+6,py,px+pw-6,py,fill=CYAN,width=1)
        self._input_var=tk.StringVar(value='Say "Hey Barviss" or "Initiate"')
        ent=tk.Entry(self,textvariable=self._input_var,
                     bg=ACCENT_BG,fg=TEXT_DIM,insertbackground=CYAN,
                     font=("Consolas",10),relief="flat",bd=0,width=52)
        ent.place(x=px+16,y=py+12)
        ent.bind("<FocusIn>",lambda e:(
            self._input_var.set("")
            if self._input_var.get().startswith(("Say","Speak","Wait","Init","Listen"))
            else None))
        ent.bind("<Return>",lambda e:self._type_submit())
        for i in range(9):
            d=c.create_oval(px+pw-130+i*13,py+18,px+pw-126+i*13,py+22,
                             fill=CYAN_DIM,outline="")
            self._dot_items.append(d)
        round_rect(c,px+pw-36,py+8,px+pw-6,py+ph-8,4,
                   fill="#003044",outline=CYAN,width=1)
        c.create_text(px+pw-21,py+22,text="▶",fill=CYAN,
                      font=("Consolas",10,"bold"),anchor="center")

    def _build_quick_btns(self):
        buttons=[("▶","YOUTUBE","#ff0000","open youtube"),
                 ("G","GOOGLE",CYAN,"open google"),
                 ("♫","SPOTIFY","#1db954","open spotify"),
                 ("☰","NOTEPAD",CYAN,"open notepad"),
                 ("⚙","SETTINGS",CYAN,""),
                 ("⏻","SHUTDOWN",CYAN,"shutdown"),
                 ("↺","RESTART",CYAN,"restart")]
        bw,bh,gap=76,68,8
        sx=(1340-len(buttons)*(bw+gap)+gap)//2; sy=735
        c=self.main
        for i,(icon,label,col,cmd) in enumerate(buttons):
            bx=sx+i*(bw+gap)
            round_rect(c,bx,sy,bx+bw,sy+bh,5,fill=ACCENT_BG,outline=BORDER2,width=1)
            c.create_line(bx+5,sy,bx+bw-5,sy,fill=CYAN,width=1)
            if label=="YOUTUBE":
                c.create_rectangle(bx+bw//2-14,sy+14,bx+bw//2+14,sy+34,
                                   fill="#ff0000",outline="")
                c.create_polygon(bx+bw//2-4,sy+17,bx+bw//2-4,sy+31,
                                 bx+bw//2+12,sy+24,fill="white",outline="")
            elif label=="GOOGLE":
                for ga,gco in zip([0,90,180,270],
                                   ["#4285F4","#EA4335","#FBBC05","#34A853"]):
                    c.create_arc(bx+bw//2-14,sy+10,bx+bw//2+14,sy+38,
                                 start=ga,extent=90,style="arc",outline=gco,width=3)
            elif label=="SPOTIFY":
                c.create_oval(bx+bw//2-14,sy+10,bx+bw//2+14,sy+38,
                              fill="#1db954",outline="")
                c.create_text(bx+bw//2,sy+24,text="♫",fill="white",
                              font=("Segoe UI Symbol",14,"bold"),anchor="center")
            else:
                c.create_text(bx+bw//2,sy+24,text=icon,fill=col,
                              font=("Segoe UI Symbol",16),anchor="center")
            c.create_text(bx+bw//2,sy+bh-12,text=label,fill=CYAN,
                          font=("Consolas",7,"bold"),anchor="center")
            if cmd:
                tag=f"qb{i}"
                c.create_rectangle(bx,sy,bx+bw,sy+bh,fill="",outline="",tags=tag)
                c.tag_bind(tag,"<Button-1>",
                           lambda e,cm=cmd:self._btn_cmd(cm))

    def _btn_cmd(self,cmd):
        reply,label=handle_command(cmd,self)
        self._set_input(reply[:65])
        self._log(label)
        speak(reply)

    def _build_clock_panel(self):
        px,py,pw,ph=1005,10,315,160
        self._panel(px,py,pw,ph)
        c=self.main
        self._tlbl=c.create_text(px+pw//2-30,py+50,text="",
                                   fill=CYAN,font=("Consolas",36,"bold"),anchor="center")
        self._albl=c.create_text(px+pw//2+65,py+50,text="",
                                   fill=CYAN,font=("Consolas",14,"bold"),anchor="center")
        self._dlbl=c.create_text(px+pw//2-30,py+80,text="",
                                   fill=TEXT_W,font=("Consolas",12),anchor="center")
        self._dtlbl=c.create_text(px+pw//2-30,py+100,text="",
                                    fill=TEXT_W,font=("Consolas",12),anchor="center")
        ccx,ccy=px+pw-38,py+ph//2
        c.create_oval(ccx-28,ccy-28,ccx+28,ccy+28,outline=CYAN_DIM,fill=PANEL_BG)
        for hr in range(12):
            a=math.radians(hr*30-90)
            c.create_line(ccx+22*math.cos(a),ccy+22*math.sin(a),
                          ccx+26*math.cos(a),ccy+26*math.sin(a),
                          fill=CYAN_DIM,width=1)
        self._ccx,self._ccy=ccx,ccy
        self._hh=c.create_line(ccx,ccy,ccx,ccy,fill=CYAN,width=2)
        self._mh=c.create_line(ccx,ccy,ccx,ccy,fill=CYAN,width=1)
        self._sh=c.create_line(ccx,ccy,ccx,ccy,fill=GREEN,width=1)
        c.create_oval(ccx-2,ccy-2,ccx+2,ccy+2,fill=CYAN,outline="")
        self._upd_clock()

    def _upd_clock(self):
        n=datetime.datetime.now()
        self.main.itemconfig(self._tlbl,text=n.strftime("%I:%M:%S"))
        self.main.itemconfig(self._albl,text=n.strftime("%p"))
        self.main.itemconfig(self._dlbl,text=n.strftime("%A").upper())
        self.main.itemconfig(self._dtlbl,text=n.strftime("%d %B %Y").upper())
        cx,cy=self._ccx,self._ccy
        s=math.radians(n.second*6-90)
        m=math.radians(n.minute*6+n.second*0.1-90)
        h=math.radians((n.hour%12)*30+n.minute*0.5-90)
        self.main.coords(self._sh,cx,cy,cx+20*math.cos(s),cy+20*math.sin(s))
        self.main.coords(self._mh,cx,cy,cx+18*math.cos(m),cy+18*math.sin(m))
        self.main.coords(self._hh,cx,cy,cx+12*math.cos(h),cy+12*math.sin(h))

    def _build_greeting_panel(self):
        px,py,pw,ph=1005,185,315,195
        self._panel(px,py,pw,ph,"GREETING")
        c=self.main
        h=datetime.datetime.now().hour
        g="GOOD MORNING" if h<12 else "GOOD AFTERNOON" if h<17 else "GOOD EVENING"
        c.create_text(px+16,py+38,text=f"{g}, PRAJWAL",
                      fill=TEXT_W,font=("Consolas",11,"bold"),anchor="w")
        c.create_text(px+16,py+62,text="I'm online and ready to assist you.",
                      fill=TEXT_DIM,font=("Consolas",9),anchor="w")
        c.create_text(px+16,py+78,text="How may I help you today?",
                      fill=TEXT_DIM,font=("Consolas",9),anchor="w")
        wy=py+ph-38
        for i in range(80):
            item=c.create_line(px+15+i*3.6,wy,px+15+i*3.6,wy,fill=CYAN_DIM,width=1)
            self._greet_wave.append((item,px+15+i*3.6,wy))

    def _build_activity_panel(self):
        px,py,pw,ph=1005,395,315,175
        self._panel(px,py,pw,ph,"LIVE ACTIVITY")
        c=self.main
        for i in range(5):
            dot=c.create_oval(px+18,py+35+i*28,px+24,py+41+i*28,fill=GREEN,outline="")
            ts=c.create_text(px+32,py+38+i*28,text="",
                              fill=TEXT_DIM,font=("Consolas",8),anchor="w")
            ev=c.create_text(px+118,py+38+i*28,text="",
                              fill=TEXT_W,font=("Consolas",8),anchor="w")
            self._act_dots.append(dot)
            self._act_texts.append((ts,ev))
        self._refresh_activity()

    def _refresh_activity(self):
        c=self.main; recent=self._activity_log[-5:]
        for i in range(5):
            ts_t,ev_t=self._act_texts[i]
            if i<len(recent):
                ts,ev=recent[i]
                c.itemconfig(ts_t,text=ts)
                c.itemconfig(ev_t,text=ev[:22])
                c.itemconfig(self._act_dots[i],fill=GREEN)
            else:
                c.itemconfig(ts_t,text="")
                c.itemconfig(ev_t,text="")
                c.itemconfig(self._act_dots[i],fill="")

    def _build_network_panel(self):
        px,py,pw,ph=1005,585,315,110
        self._panel(px,py,pw,ph,"NETWORK")
        c=self.main
        cx,cy=px+45,py+60
        for r,col in [(22,CYAN_DIM),(15,CYAN_DIM),(8,CYAN)]:
            c.create_arc(cx-r,cy-r,cx+r,cy+r,start=30,extent=120,
                         style="arc",outline=col,width=2)
        c.create_oval(cx-3,cy+2,cx+3,cy+8,fill=CYAN,outline="")
        c.create_text(px+70,py+40,text="CONNECTED",
                      fill=GREEN,font=("Consolas",11,"bold"),anchor="w")
        c.create_text(px+70,py+60,text="IP: 192.168.1.105",
                      fill=TEXT_DIM,font=("Consolas",9),anchor="w")
        bx=px+70
        for i in range(5):
            bh2=6+i*4
            c.create_rectangle(bx+i*10,py+85-bh2,bx+i*10+6,py+85,
                                fill=CYAN if i<4 else GREEN,outline="")
        c.create_text(bx+60,py+80,text="STRENGTH: 98%",
                      fill=TEXT_DIM,font=("Consolas",8),anchor="w")

    # ── ANIMATION ─────────────────────────────────────────────────────────────
    def _animate(self):
        self._tick+=1
        c=self.main; t=self._tick*0.15
        self._angle=(self._angle+1.5)%360
        for i,item in enumerate(self._arc_items):
            c.itemconfig(item,start=(self._angle+i*90)%360)
        for i,item in enumerate(self._arc2_items):
            c.itemconfig(item,start=(-self._angle*1.3+i*120)%360)
        cx,cy=self._rcx,self._rcy+35
        for i,item in enumerate(self._wave_items):
            f=i/len(self._wave_items)
            h=12*math.sin(f*math.pi*4+t)*math.sin(f*math.pi)
            x=(cx-100)+f*200; y0=cy-abs(h); y1=cy+abs(h)
            if y0>=y1: y1=y0+1
            c.coords(item,x,y0,x,y1)
        for i,(item,gx,gy) in enumerate(self._greet_wave):
            h=7*math.sin(i*0.25+t*1.2)*(0.4+0.6*random.random())
            c.coords(item,gx,gy-abs(h),gx,gy+abs(h))
        self._dot_phase=(self._dot_phase+0.08)%1.0
        for i,dot in enumerate(self._dot_items):
            p=(self._dot_phase+i/len(self._dot_items))%1.0
            b=int(40+160*(0.5+0.5*math.sin(p*2*math.pi)))
            try: c.itemconfig(dot,fill=f"#{b:02x}{min(b+80,255):02x}{min(b+80,255):02x}")
            except: pass
        if self._tick%25==0:
            self._listen_blink=not self._listen_blink
        if self._tick%20==0:
            self._cpu=max(5,min(95,self._cpu+random.randint(-3,3)))
            self._ram=max(30,min(80,self._ram+random.randint(-2,2)))
            self._net=max(80,min(99,self._net+random.randint(-2,2)))
            self._set_bar("CPU",self._cpu)
            self._set_bar("RAM",self._ram)
            self._set_bar("NETWORK",self._net)
        pw2=2+abs(math.sin(self._tick*0.05))*2
        c.itemconfig(self._ring1,width=pw2)
        if self._tick%10==0:
            self._upd_clock()
        self.after(50,self._animate)


if __name__=="__main__":
    app=BarvissApp()
    app.mainloop()
