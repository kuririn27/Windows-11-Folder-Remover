import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
import datetime
import threading
import webbrowser
import shutil
from pathlib import Path

class RemoverPastaPro(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Remover Pastas Profissional v2.0")
        self.geometry("800x600")
        self.resizable(True, True)
        self.paths = []
        self.stop_flag = False
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Log file setup
        log_dir = os.path.join(os.getcwd(), "logs")
        os.makedirs(log_dir, exist_ok=True)
        self.log_file = os.path.join(log_dir, f"remover_pasta_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")

        # Configure style
        style = ttk.Style()
        style.configure("TButton", padding=6)
        style.configure("TLabel", font=("Segoe UI", 11))

        # Main container
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Instruction label
        ttk.Label(main_frame, text="Clique em 'Selecionar Pastas' para adicionar pastas").pack(pady=10)

        # Listbox for paths
        self.listbox = tk.Listbox(main_frame, width=90, height=8, font=("Segoe UI", 10))
        self.listbox.pack(pady=5, fill=tk.X)
        self.listbox.bind("<Delete>", self.remover_selecionados)

        # Buttons frame
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=5)

        self.btn_browse = ttk.Button(btn_frame, text="Selecionar Pastas", command=self.selecionar_pastas)
        self.btn_browse.pack(side=tk.LEFT, padx=5)

        self.btn_remove = ttk.Button(btn_frame, text="Remover Pastas", command=self.start_remover_pastas, style="Accent.TButton")
        self.btn_remove.pack(side=tk.LEFT, padx=5)

        self.btn_clear = ttk.Button(btn_frame, text="Limpar Lista", command=self.limpar_lista)
        self.btn_clear.pack(side=tk.LEFT, padx=5)

        self.btn_cancel = ttk.Button(btn_frame, text="Cancelar", command=self.cancelar, state='disabled')
        self.btn_cancel.pack(side=tk.LEFT, padx=5)

        self.btn_log = ttk.Button(btn_frame, text="Abrir Log", command=self.abrir_log)
        self.btn_log.pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress = ttk.Progressbar(main_frame, length=750, mode='determinate')
        self.progress.pack(pady=10)

        # Log area
        self.log = scrolledtext.ScrolledText(main_frame, width=90, height=15, state='disabled', font=("Consolas", 10))
        self.log.pack(pady=10, fill=tk.BOTH)

        # Status bar
        self.status_var = tk.StringVar(value="Pronto")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def log_msg(self, msg):
        self.log.config(state='normal')
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        formatted_msg = f"[{timestamp}] {msg}"
        self.log.insert(tk.END, formatted_msg + "\n")
        self.log.see(tk.END)
        self.log.config(state='disabled')
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(formatted_msg + "\n")
        except Exception as e:
            self.log_msg(f"Erro ao escrever no log: {str(e)}")
        self.update()

    def update_status(self, msg):
        self.status_var.set(msg)
        self.update()

    def abrir_log(self):
        try:
            if os.path.exists(self.log_file):
                webbrowser.open(f"file://{self.log_file}")
            else:
                messagebox.showwarning("Aviso", "Arquivo de log não encontrado.")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao abrir log: {str(e)}")

    def selecionar_pastas(self):
        try:
            path = filedialog.askdirectory(title="Selecione Pastas", mustexist=True)
            if path and path not in self.paths:
                self.paths.append(path)
                self.listbox.insert(tk.END, path)
                self.log_msg(f"Pasta selecionada: {path}")
                self.update_status(f"{len(self.paths)} pastas selecionadas")
        except Exception as e:
            self.log_msg(f"Erro ao selecionar pasta: {str(e)}")

    def remover_selecionados(self, event=None):
        try:
            selected = list(self.listbox.curselection())
            selected.reverse()
            for i in selected:
                removed_path = self.paths.pop(i)
                self.listbox.delete(i)
                self.log_msg(f"Pasta removida da lista: {removed_path}")
            self.update_status(f"{len(self.paths)} pastas selecionadas")
        except Exception as e:
            self.log_msg(f"Erro ao remover seleção: {str(e)}")

    def limpar_lista(self):
        try:
            self.paths.clear()
            self.listbox.delete(0, tk.END)
            self.log_msg("Lista de pastas limpa")
            self.update_status("Pronto")
        except Exception as e:
            self.log_msg(f"Erro ao limpar lista: {str(e)}")

    def cancelar(self):
        self.stop_flag = True
        self.btn_remove.config(state='normal')
        self.btn_cancel.config(state='disabled')
        self.log_msg("⚠️ Operação cancelada pelo usuário!")

    def start_remover_pastas(self):
        if not self.paths:
            messagebox.showerror("Erro", "Nenhuma pasta selecionada!")
            return
        if not messagebox.askyesno("Confirmação", f"Tem certeza que deseja apagar {len(self.paths)} pastas selecionadas?"):
            return
        self.stop_flag = False
        self.btn_remove.config(state='disabled')
        self.btn_cancel.config(state='normal')
        threading.Thread(target=self.remover_pastas, daemon=True).start()

    def executar(self, comando, descricao):
        if self.stop_flag:
            raise Exception("Operação cancelada pelo usuário")
        self.log_msg(descricao)
        try:
            resultado = subprocess.run(comando, shell=True, capture_output=True, text=True, timeout=300)
            if resultado.returncode != 0:
                self.log_msg(f"⚠️ Erro em: {descripcion}\n{resultado.stderr}")
        except subprocess.TimeoutExpired:
            self.log_msg(f"⚠️ Tempo esgotado em: {descripcion}")
        except Exception as e:
            self.log_msg(f"⚠️ Erro ao executar comando: {str(e)}")

    def remover_pastas(self):
        total = len(self.paths)
        self.update_status("Processando...")
        for i, path in enumerate(self.paths[:]):  # Copy to avoid modification during iteration
            if self.stop_flag:
                break
            if not os.path.exists(path):
                self.log_msg(f"⚠️ Caminho não existe: {path}")
                continue

            try:
                # Count total files for progress
                total_files = sum(1 for _ in Path(path).rglob('*') if _.is_file())
                processed_files = 0

                # Try using shutil first (faster for simple cases)
                try:
                    shutil.rmtree(path, ignore_errors=False)
                    self.log_msg(f"✅ Pasta {path} removida com sucesso!")
                except (PermissionError, OSError):
                    # Fallback to detailed permission handling
                    self.executar(f'takeown /f "{path}" /r /d Y', f"Assumindo propriedade de {path}...")
                    user = os.getlogin()
                    self.executar(f'icacls "{path}" /grant {user}:(F) /t /c', f"Concedendo permissões ao usuário {user}...")
                    self.executar(f'attrib -r -s -h "{path}\\*" /S', "Removendo atributos especiais...")
                    self.executar(f'powershell -Command "Remove-Item \\"{path}\\" -Recurse -Force"', f"Removendo {path}...")

                # Update progress
                processed_files += 1
                self.progress['value'] = ((i + processed_files/max(total_files, 1))/total)*100
                self.update()

            except Exception as e:
                self.log_msg(f"❌ Erro ao remover {path}: {str(e)}")

        self.progress['value'] = 100
        self.btn_remove.config(state='normal')
        self.btn_cancel.config(state='disabled')
        messagebox.showinfo("Concluído", f"Processamento finalizado.\nLog salvo em:\n{self.log_file}")
        self.limpar_lista()
        self.update_status("Pronto")

    def on_closing(self):
        if messagebox.askokcancel("Sair", "Deseja realmente sair?"):
            self.stop_flag = True
            self.destroy()

if __name__ == "__main__":
    try:
        app = RemoverPastaPro()
        app.mainloop()
    except Exception as e:
        messagebox.showerror("Erro Fatal", f"Aplicação terminou com erro: {str(e)}")