"""Inicialização por duplo clique: chave em janela e protótipo via IPv4."""
import os
import sys
from app import main as iniciar_servidor


def solicitar_chave():
    from tkinter import Tk, StringVar, TclError, ttk

    janela = Tk()
    janela.title("AulaIA — iniciar protótipo")
    janela.resizable(False, False)
    painel = ttk.Frame(janela, padding=20)
    painel.grid()
    ttk.Label(painel, text="Chave da API Gemini", font=("Segoe UI", 12, "bold")).grid(
        row=0, column=0, columnspan=2, sticky="w")
    ttk.Label(painel, text="Copie sua chave e clique em Colar chave.").grid(
        row=1, column=0, columnspan=2, sticky="w", pady=(6, 12))
    entrada = ttk.Entry(painel, width=52, show="*")
    entrada.grid(row=2, column=0, columnspan=2, sticky="ew")
    aviso = StringVar(value="A chave fica apenas na memória enquanto o servidor está aberto.")
    ttk.Label(painel, textvariable=aviso).grid(row=3, column=0, columnspan=2, sticky="w", pady=10)
    resultado = None

    def colar():
        try:
            # A área de transferência só é lida quando o usuário clica no botão.
            chave = janela.clipboard_get().strip()
        except TclError:
            aviso.set("Copie a chave primeiro e clique em Colar chave novamente.")
            return
        entrada.delete(0, "end")
        entrada.insert(0, chave)
        aviso.set("Chave colada. Clique em Iniciar protótipo." if chave else "A área de transferência está vazia.")
        entrada.focus_set()

    def confirmar(event=None):
        nonlocal resultado
        chave = entrada.get().strip()
        if not chave:
            aviso.set("Cole a chave antes de iniciar.")
            entrada.focus_set()
            return
        resultado = chave
        janela.destroy()

    ttk.Button(painel, text="Colar chave", command=colar).grid(row=4, column=0, sticky="w")
    ttk.Button(painel, text="Iniciar protótipo", command=confirmar).grid(row=4, column=1, sticky="e")
    janela.bind("<Return>", confirmar)
    janela.bind("<Escape>", lambda event: janela.destroy())
    janela.after(100, entrada.focus_set)
    janela.mainloop()
    return resultado


def main():
    chave_anterior = os.environ.get("GEMINI_API_KEY")
    if not (chave_anterior or "").strip():
        chave = solicitar_chave()
        if not chave:
            print("Inicialização cancelada.")
            return 0
        os.environ["GEMINI_API_KEY"] = chave
    try:
        iniciar_servidor(["--modo", "lexical", "--gerador", "ia", "--ipv4", "--abrir"])
        return 0
    finally:
        if chave_anterior is None:
            os.environ.pop("GEMINI_API_KEY", None)
        else:
            os.environ["GEMINI_API_KEY"] = chave_anterior


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("Inicialização cancelada.")
