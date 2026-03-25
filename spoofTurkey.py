import subprocess
import shutil
import os
import threading
import time
import sys
import argparse
import signal

# ----------------------------
# ARGPARSE
# ----------------------------
parser = argparse.ArgumentParser(description="SpoofDPI + Discord launcher")
parser.add_argument("--show", action="store_true", help="Çıktıları göster")
args = parser.parse_args()
show = args.show

# ----------------------------
# RENKLER
# ----------------------------
class c:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    RESET = '\033[0m'

def log(msg, color=c.GREEN):
    if show:
        print(f"{color}{msg}{c.RESET}")

def exists(cmd):
    return shutil.which(cmd) is not None

# ----------------------------
# SUDO BAŞTA AL
# ----------------------------
log("[*] Sudo yetkisi alınıyor...", c.YELLOW)
subprocess.run("sudo -v", shell=True)

def keep_sudo_alive():
    while True:
        subprocess.run("sudo -v", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(60)

threading.Thread(target=keep_sudo_alive, daemon=True).start()

# ----------------------------
# KURULUM KONTROLLERİ
# ----------------------------
if exists("go"):
    log("[OK] Go zaten yüklü")
else:
    log("[!] Go yok → kuruluyor", c.YELLOW)
    subprocess.run("sudo pacman -S --noconfirm go")

if exists("git"):
    log("[OK] Git zaten yüklü")
else:
    log("[!] Git yok → kuruluyor", c.YELLOW)
    subprocess.run("sudo pacman -S --noconfirm git")

spoof_path = shutil.which("spoofdpi")
if spoof_path:
    log(f"[OK] SpoofDPI zaten mevcut → {spoof_path}")
else:
    log("[!] SpoofDPI yok → kuruluyor", c.YELLOW)
    subprocess.run("curl -fsSL https://raw.githubusercontent.com/xvzc/SpoofDPI/main/install.sh | bash")

# ----------------------------
# PATH kontrolü
# ----------------------------
bashrc = os.path.expanduser("~/.bashrc")
path = os.environ.get("PATH", "")

if "/usr/local/bin" not in path:
    log("[!] /usr/local/bin PATH'te yok → ekleniyor", c.YELLOW)
    if os.path.exists(bashrc):
        with open(bashrc, "r") as f:
            content = f.read()
    else:
        content = ""
    if "/usr/local/bin" not in content:
        with open(bashrc, "a") as f:
            f.write('\nexport PATH="/usr/local/bin:$PATH"\n')
        log("[OK] .bashrc güncellendi")
else:
    log("[OK] PATH zaten doğru")

# ----------------------------
# HASH RESET
# ----------------------------
log("[*] shell cache temizleniyor", c.YELLOW)
subprocess.run("hash -r", shell=True)

spoof_path = shutil.which("spoofdpi")
if not spoof_path:
    log("[ERROR] spoofdpi bulunamadı → çıkılıyor", c.RED)
    sys.exit()
log(f"[SUCCESS] spoofdpi hazır → {spoof_path}")

# ----------------------------
# THREADLER İLE ÇALIŞTIRMA
# ----------------------------
processes = []

def run_command(name, cmd, env=None):
    log(f"[*] {name} başlatılıyor...", c.YELLOW)
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True)
    processes.append(p)
    for line in p.stdout:
        if show:
            print(f"[{name}] {line.strip()}")
    p.wait()
    log(f"[*] {name} kapandı", c.YELLOW)

# ----------------------------
# Discord için env
# ----------------------------
discord_env = os.environ.copy()
discord_env["http_proxy"] = "http://127.0.0.1:8080"
discord_env["https_proxy"] = "http://127.0.0.1:8080"

# ----------------------------
# Thread başlatma
# ----------------------------
threads = []
t1 = threading.Thread(target=run_command, args=("SpoofDPI", "sudo spoofdpi --dns-mode https --https-split-mode chunk --https-chunk-size 1 --https-fake-count 10"))
threads.append(t1)
t2 = threading.Thread(target=run_command, args=("Discord", "discord", discord_env))
threads.append(t2)

for t in threads:
    t.start()
    time.sleep(2)  # SpoofDPI’nin açılmasını biraz bekle

# ----------------------------
# Ctrl+C ile durdurma
# ----------------------------
try:
    while any(t.is_alive() for t in threads):
        time.sleep(1)
except KeyboardInterrupt:
    log("\n[*] Ctrl+C alındı → tüm processler sonlandırılıyor...", c.YELLOW)
    for p in processes:
        p.terminate()
    for t in threads:
        t.join()
    log("[*] Hepsi kapatıldı. Çıkılıyor.", c.GREEN)
    sys.exit(0)