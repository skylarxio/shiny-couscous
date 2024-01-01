import os
import random
import subprocess
from datetime import datetime, timedelta
import sys

# --- KONFIGURASI ---
REPO_PATH = "."
FILENAME = "history.txt"

# --- DEFINISI WARNA ANSI ---
# Pastikan ini berfungsi di terminal Windows (Git Bash/MINGW64)
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RED = '\033[91m'
BLUE = '\033[94m'
RST = '\033[0m'

def run_command_quietly(command):
    """Menjalankan perintah terminal tanpa menampilkan output (untuk add/commit)."""
    try:
        subprocess.run(command, shell=True, check=True, cwd=REPO_PATH, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"\n{RED}ERROR: Perintah Git gagal: {e.cmd}{RST}")
        print(f"{RED}Pesan Kesalahan: {e.stderr}{RST}")
        sys.exit(1)

def get_date_from_user(prompt_message: str) -> datetime:
    """Meminta input tanggal dari pengguna dan memvalidasinya."""
    while True:
        date_str = input(prompt_message)
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            print(f"{RED}Format tanggal salah. Harap gunakan format YYYY-MM-DD (contoh: 2021-01-25). Coba lagi.{RST}")

def get_integer_from_user(prompt_message: str, min_value: int = 1) -> int:
    """Meminta input angka dari pengguna dan memvalidasinya."""
    while True:
        try:
            value = int(input(prompt_message))
            if value >= min_value:
                return value
            else:
                print(f"{RED}Input harus angka yang lebih besar atau sama dengan {min_value}. Coba lagi.{RST}")
        except ValueError:
            print(f"{RED}Input tidak valid. Harap masukkan angka bulat. Coba lagi.{RST}")

def push_with_pat(pat_token: str):
    """Mendapatkan URL remote dan menjalankan git push --force menggunakan PAT."""
    print("-" * 50)
    print(f"{CYAN}Mencoba PUSH paksa menggunakan Personal Access Token (PAT)...{RST}")

    # 1. Dapatkan URL remote 'origin'
    try:
        # Menjalankan git remote get-url origin untuk mendapatkan URL remote
        remote_url = subprocess.check_output(
            ['git', 'remote', 'get-url', 'origin'],
            cwd=REPO_PATH,
            text=True
        ).strip()
    except subprocess.CalledProcessError:
        print(f"{RED}❌ Gagal mendapatkan URL remote 'origin'. Pastikan Anda berada di repositori Git.{RST}")
        return

    # 2. Modifikasi URL untuk menyematkan PAT
    # Kami akan mengganti URL SSH (git@github.com:user/repo.git) atau HTTPS (https://github.com/user/repo.git)
    # menjadi format https://oauth2:PAT@github.com/user/repo.git
    
    pat_url = None

    if remote_url.startswith("https://") or remote_url.startswith("http://"):
        # Jika sudah HTTPS, pastikan tidak ada kredensial lama di dalamnya.
        # Langkah 1: Ambil bagian URL setelah potensi kredensial lama (jika ada)
        clean_url = remote_url.split('@')[-1] 
        
        # Langkah 2: Hapus protokol (https:// atau http://) dari awal clean_url untuk mencegah duplikasi
        host_and_path = clean_url
        if clean_url.startswith("https://"):
            host_and_path = clean_url[8:] # Menghapus "https://"
        elif clean_url.startswith("http://"):
            host_and_path = clean_url[7:] # Menghapus "http://"
            
        # Langkah 3: Bangun ulang URL dengan PAT di depan host
        pat_url = f"https://oauth2:{pat_token}@{host_and_path}"
        
    elif remote_url.startswith("git@github.com:"):
        # Jika menggunakan SSH, ubah ke HTTPS
        # git@github.com:skylarxio/glowing-sniffle.git -> github.com/skylarxio/glowing-sniffle.git
        repo_path_ssh = remote_url.split(":")[-1]
        pat_url = f"https://oauth2:{pat_token}@github.com/{repo_path_ssh}"
    else:
        print(f"{RED}❌ Format URL remote tidak dikenal: {remote_url}{RST}")
        print(f"{CYAN}Silakan coba menjalankan manual:{RST} {YELLOW}git push --force origin main{RST}")
        return

    # 3. Menjalankan perintah push dengan PAT
    # Perintahnya akan menjadi: git push --force https://oauth2:PAT@github.com/user/repo.git main
    # Menggunakan f-string dengan tanda kutip untuk menangani PAT dan URL yang mungkin berisi karakter khusus.
    final_push_command = f'git push --force "{pat_url}" main'

    # Menampilkan perintah yang akan dieksekusi, menyembunyikan PAT
    display_command = final_push_command.replace(f"oauth2:{pat_token}", "oauth2:******************")
    print(f"{CYAN}Perintah yang dieksekusi:{RST} {YELLOW}{display_command}{RST}")

    try:
        # Jalankan perintah. stdout tidak disembunyikan agar user melihat output Git.
        subprocess.run(
            final_push_command,
            shell=True,
            check=True,
            cwd=REPO_PATH
        )
        print(f"\n{GREEN}🎉 PUSH ke GitHub Berhasil! Kontribusi Anda telah diperbarui.{RST}")
    except subprocess.CalledProcessError:
        print(f"\n{RED}❌ PUSH GAGAL. Pesan error 403 mungkin masih terjadi.{RST}")
        print(f"{RED}Pastikan PAT Anda benar, memiliki izin 'repo', dan cabang 'main' mengizinkan force push.{RST}")


def main():
    """Fungsi utama untuk menghasilkan commit historis."""
    os.chdir(REPO_PATH)
    
    print("-" * 50)
    print(f"{CYAN}Selamat datang di Skrip Mesin Waktu Kontribusi!{RST}")
    print(f"Gunakan format {YELLOW}YYYY-MM-DD{RST} untuk memasukkan tanggal.")
    print("-" * 50)
    
    start_date = get_date_from_user(f"{BLUE}Masukkan Tanggal Mulai (contoh: 2020-01-01): {RST}")
    end_date = get_date_from_user(f"{BLUE}Masukkan Tanggal Selesai (contoh: 2024-12-31): {RST}")

    if start_date > end_date:
        print(f"{RED}ERROR: Tanggal mulai tidak boleh lebih lambat dari tanggal selesai.{RST}")
        return
        
    # --- PROMPT BARU UNTUK AUTHOR/EMAIL ---
    print("-" * 50)
    print(f"{CYAN}Konfigurasi Author Commit (Penting untuk Grafik GitHub){RST}")
    author_name = input(f"{BLUE}Masukkan NAMA Anda (Harus sama dengan GitHub): {RST}").strip()
    author_email = input(f"{BLUE}Masukkan EMAIL Anda (Harus sama dengan GitHub): {RST}").strip()
    print("-" * 50)
    # --- AKHIR PROMPT BARU ---
        
    print(f"{BLUE}Pilih Mode Commit:{RST}")
    print("1. Mode Cepat (Membuat tepat 1 commit per hari. Proses sangat cepat)")
    print("2. Mode Realistis (Membuat jumlah acak per hari. Proses lebih lama)")
    choice = input(f"{BLUE}Pilihan Anda (1/2): {RST}").strip()

    min_commits = 1
    max_commits = 1

    if choice == '2':
        print("-" * 50)
        min_commits = get_integer_from_user(f"{BLUE}Masukkan jumlah MINIMAL commit per hari: {RST}", min_value=1)
        max_commits = get_integer_from_user(f"{BLUE}Masukkan jumlah MAKSIMAL commit per hari: {RST}", min_value=min_commits)
    else:
        print(f"{CYAN}Mode Cepat dipilih.{RST}")

    if not os.path.exists(FILENAME):
        with open(FILENAME, 'w') as f:
            f.write("Commit history for contribution graph.\n")

    current_date = start_date
    days_total = (end_date - start_date).days + 1
    days_processed = 0

    print(f"\n{CYAN}Memulai proses pembuatan commit dari {start_date.date()} hingga {end_date.date()}...{RST}")
    print(f"{CYAN}Setiap hari kerja akan memiliki {min_commits}-{max_commits} commit.{RST}")

    while current_date <= end_date:
        if current_date.weekday() < 5:  # Senin (0) sampai Jumat (4)
            num_commits_today = random.randint(min_commits, max_commits)
            
            for i in range(num_commits_today):
                commit_hour = random.randint(9, 17)
                commit_minute, commit_second = random.randint(0, 59), random.randint(0, 59)
                commit_date = current_date.replace(hour=commit_hour, minute=commit_minute, second=commit_second)
                date_str = commit_date.strftime("%Y-%m-%d %H:%M:%S")
                
                with open(FILENAME, 'a') as f:
                    f.write(f"Commit #{i+1} on {date_str} - {random.random()}\n")
                
                run_command_quietly('git add .')
                
                commit_env = os.environ.copy()
                commit_env['GIT_AUTHOR_DATE'] = date_str
                commit_env['GIT_COMMITTER_DATE'] = date_str
                
                # --- PENGATURAN AUTHOR DENGAN INPUT PENGGUNA ---
                commit_env['GIT_AUTHOR_NAME'] = author_name
                commit_env['GIT_AUTHOR_EMAIL'] = author_email
                commit_env['GIT_COMMITTER_NAME'] = author_name
                commit_env['GIT_COMMITTER_EMAIL'] = author_email
                # --- AKHIR PENGATURAN AUTHOR ---

                subprocess.run(
                    ['git', 'commit', '-m', f"Auto-commit for {current_date.date()} [UTC]"],
                    env=commit_env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )

        days_processed += 1
        progress = int((days_processed / days_total) * 100)
        bar = '█' * (progress // 2) + '-' * (50 - (progress // 2))
        print(f'\r{YELLOW}Progress: |{bar}| {progress}% ({current_date.date()}){RST}', end="")
        
        current_date += timedelta(days=1)

    print(f"\n\n{GREEN}✅ Selesai! Commit historis telah dibuat secara lokal.{RST}")
    
    # --- LOGIKA AUTH DENGAN PAT BARU ---
    print("-" * 50)
    print(f"{CYAN}Otentikasi GitHub Diperlukan untuk PUSH.{RST}")
    print(f"Pesan error 403 sebelumnya terjadi karena masalah izin atau kredensial.")
    print(f"Harap masukkan {YELLOW}Personal Access Token (PAT){RST} GitHub Anda.")
    print(f"PAT ini harus memiliki scope 'repo'.")
    pat_token = input(f"{BLUE}Masukkan Personal Access Token (PAT): {RST}").strip()

    if pat_token:
        push_with_pat(pat_token)
    else:
        print(f"\n{RED}PAT kosong. PUSH remote dibatalkan.{RST}")
        print(f"{CYAN}Silakan jalankan manual setelah memastikan Anda memiliki izin:{RST}")
        print(f"{YELLOW}git push --force origin main{RST}")

if __name__ == "__main__":
    try:
        # Cek apakah git tersedia
        subprocess.run(['git', '--version'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        main()
    except subprocess.CalledProcessError:
        print(f"\n{RED}ERROR: Perintah 'git' gagal. Pastikan Git sudah terinstall dan dikonfigurasi di Path Anda.{RST}")
    except KeyboardInterrupt:
        print(f"\n{RED}Proses dihentikan oleh pengguna.{RST}")
