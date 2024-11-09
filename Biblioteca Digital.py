import tkinter as tk
from tkinter import ttk, messagebox
import csv
import os
import requests
from datetime import datetime, timedelta
from ttkbootstrap import Style
from PIL import ImageTk, Image

class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None

        self.widget.bind('<Enter>', self.show_tooltip)
        self.widget.bind('<Leave>', self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)
        self.tooltip_window.wm_geometry(f"+{x}+{y}")
        label = ttk.Label(self.tooltip_window, text=self.text, relief='solid', borderwidth=1)
        label.pack()

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

class LoginScreen:
    def __init__(self, root, on_success):
        self.root = root
        self.on_success = on_success

        self.frame_login = ttk.Frame(self.root)
        self.frame_login.pack(expand=True)

        self.titulo = ttk.Label(self.frame_login, text="Biblioteca Digital", font=("Arial", 24))
        self.titulo.grid(row=0, column=0, columnspan=2, pady=(0, 20))

        ttk.Label(self.frame_login, text="Usuário:").grid(row=1, column=0, pady=(0, 5), sticky='w')
        self.username_entry = ttk.Entry(self.frame_login)
        self.username_entry.grid(row=1, column=1, pady=(0, 10))

        ttk.Label(self.frame_login, text="Senha:").grid(row=2, column=0, pady=(0, 5), sticky='w')
        self.password_entry = ttk.Entry(self.frame_login, show="*")
        self.password_entry.grid(row=2, column=1, pady=(0, 20))

        self.data_hora = ttk.Label(self.frame_login, text="", font=("Arial", 10))
        self.data_hora.grid(row=3, column=0, columnspan=2, pady=(0, 10))

        ttk.Button(self.frame_login, text="Entrar", command=self.check_login).grid(row=4, column=0, columnspan=2, pady=(5, 5))
        ttk.Button(self.frame_login, text="Criar Usuário", command=self.open_create_user_window).grid(row=5, column=0, columnspan=2, pady=(5, 5))

        self.atualizar_data_hora()

    def atualizar_data_hora(self):
        agora = datetime.now()
        self.data_hora.config(text=agora.strftime('%d/%m/%Y %H:%M:%S'))
        self.root.after(1000, self.atualizar_data_hora)

    def check_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if self.check_existing_user(username, password):
            self.frame_login.pack_forget()  # Esconde a tela de login
            self.on_success()  # Abre a tela principal
        else:
            messagebox.showerror("Erro", "Usuário ou senha incorretos.")

    def check_existing_user(self, username, password):
        """Verifica se o usuário existe e se a senha está correta."""
        if os.path.exists('.usuarios.csv'):
            with open('.usuarios.csv', mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'Usuário' in row and 'Senha' in row:
                        if row['Usuário'] == username and row['Senha'] == password:
                            return True
        return False

    def open_create_user_window(self):
        CreateUserWindow(self)

    def user_exists(self, username):
        """Verifica se o usuário já existe no arquivo CSV."""
        if os.path.exists('.usuarios.csv'):
            with open('.usuarios.csv', mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if 'Usuário' in row and row['Usuário'] == username:
                        return True
        return False

    def create_user(self, username, password):
        """Cria um novo usuário e salva no arquivo CSV."""
        # Checa se o arquivo existe e cria se não existir
        if not os.path.exists('.usuarios.csv'):
            with open('.usuarios.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['Usuário', 'Senha'])  # Adiciona cabeçalho

        with open('.usuarios.csv', mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([username, password])

class CreateUserWindow:
    def __init__(self, login_screen):
        self.login_screen = login_screen

        self.window = tk.Toplevel(self.login_screen.root)
        self.window.title("Criar Usuário")

        ttk.Label(self.window, text="Novo Usuário:", font=("Arial", 14)).pack(pady=10)

        ttk.Label(self.window, text="Usuário:").pack(anchor='w', padx=10)
        self.username_entry = ttk.Entry(self.window, width=30)
        self.username_entry.pack(pady=5, padx=10)

        ttk.Label(self.window, text="Senha:").pack(anchor='w', padx=10)
        self.password_entry = ttk.Entry(self.window, show="*")
        self.password_entry.pack(pady=5, padx=10)

        ttk.Button(self.window, text="Criar", command=self.create_user).pack(pady=10)

    def create_user(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if username and password:
            if self.login_screen.user_exists(username):
                messagebox.showerror("Erro", "Este usuário já existe.")
            else:
                self.login_screen.create_user(username, password)
                messagebox.showinfo("Sucesso", "Usuário criado com sucesso!")
                self.window.destroy()
                self.login_screen.username_entry.delete(0, tk.END)  # Limpa o campo de usuário
                self.login_screen.password_entry.delete(0, tk.END)  # Limpa o campo de senha
        else:
            messagebox.showerror("Erro", "Usuário e senha são obrigatórios.")

class BibliotecaDigital:
    def __init__(self, root):
        self.root = root
        self.root.title("Biblioteca Digital")
        self.root.state('zoomed')

        self.alunos = {}
        self.livros = {}
        self.status_livros = {}
        self.emprestimos = {}

        self.criar_diretorio_csv()
        self.carregar_dados()

        # Criar abas
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(expand=True, fill='both', padx=20, pady=20)

        self.criar_abas()

        # Rodapé
        self.rodape_label = ttk.Label(self.root, text="Criado e Desenvolvido por Tharcisio Estrella - 2024", font=("Arial", 8))
        self.rodape_label.pack(side=tk.BOTTOM, pady=(10, 10))

        # Botão de logout
        self.logout_button = ttk.Button(self.root, text="Logout", command=self.logout)
        self.logout_button.pack(pady=(0, 10), side=tk.BOTTOM)

        # Relógio
        self.relogio_label = ttk.Label(self.root, font=("Arial", 10))
        self.relogio_label.place(relx=0.95, rely=0.02, anchor='ne')
        self.atualizar_relogio()

    def criar_abas(self):
        self.aba_cadastro_alunos = CadastroAlunos(self)
        self.aba_cadastro_livros = CadastroLivros(self)
        self.aba_emprestimos = Emprestimos(self)
        self.aba_pesquisa = Pesquisa(self)
        self.aba_relatorios = Relatorios(self)

        self.tab_control.add(self.aba_cadastro_alunos, text='Cadastro de Alunos')
        self.tab_control.add(self.aba_cadastro_livros, text='Cadastro de Livros')
        self.tab_control.add(self.aba_emprestimos, text='Empréstimos')
        self.tab_control.add(self.aba_pesquisa, text='Pesquisar')
        self.tab_control.add(self.aba_relatorios, text='Relatórios')

    def atualizar_relogio(self):
        agora = datetime.now()
        self.relogio_label.config(text=agora.strftime('%d/%m/%Y %H:%M:%S'))
        self.root.after(1000, self.atualizar_relogio)

    def criar_diretorio_csv(self):
        if not os.path.exists('dados'):
            os.makedirs('dados')

        if not os.path.exists('dados/livros'):
            os.makedirs('dados/livros')

        if not os.path.exists('dados/alunos.csv'):
            with open('dados/alunos.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['REMA', 'Nome', 'Telefone', 'Endereço', 'Ano/Turma'])
        if not os.path.exists('dados/livros.csv'):
            with open('dados/livros.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID', 'Nome do Livro', 'Autor', 'Categoria', 'Capa'])
        if not os.path.exists('dados/status_livros.csv'):
            with open('dados/status_livros.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID Livro', 'Nome do Livro', 'Status'])
        if not os.path.exists('dados/emprestimos.csv'):
            with open('dados/emprestimos.csv', mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['ID Empréstimo', 'REMA', 'ID Livro', 'Data do Empréstimo', 'Data de Devolução'])

    def carregar_dados(self):
        self.carregar_alunos()
        self.carregar_livros()
        self.carregar_status_livros()
        self.carregar_emprestimos()

    def carregar_alunos(self):
        try:
            with open('dados/alunos.csv', mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    rema = int(row['REMA'])
                    self.alunos[rema] = row
        except FileNotFoundError:
            pass

    def carregar_livros(self):
        try:
            with open('dados/livros.csv', mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    row['ID'] = int(row['ID'])
                    self.livros[row['ID']] = row
        except FileNotFoundError:
            pass

    def carregar_status_livros(self):
        try:
            with open('dados/status_livros.csv', mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    self.status_livros[int(row['ID Livro'])] = row
        except FileNotFoundError:
            pass

    def carregar_emprestimos(self):
        try:
            with open('dados/emprestimos.csv', mode='r') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    row['ID Empréstimo'] = int(row['ID Empréstimo'])
                    self.emprestimos[row['ID Empréstimo']] = row
        except FileNotFoundError:
            pass

    def atualizar_csv_status_livros(self):
        with open('dados/status_livros.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['ID Livro', 'Nome do Livro', 'Status'])
            writer.writeheader()
            for livro in self.status_livros.values():
                writer.writerow(livro)

    def logout(self):
        self.tab_control.pack_forget()  # Remove as abas
        self.logout_button.pack_forget()  # Remove o botão de logout
        self.rodape_label.pack_forget()  # Remove o rodapé
        LoginScreen(self.root, self.abrir_biblioteca)  # Retorna à tela de login

    def abrir_biblioteca(self):
        self.tab_control.pack(expand=True, fill='both', padx=20, pady=20)


class CadastroAlunos(ttk.Frame):
    def __init__(self, biblioteca):
        super().__init__(biblioteca.root)
        self.biblioteca = biblioteca

        ttk.Label(self, text="Adicione Aluno", font=('Arial', 14)).pack(pady=10)

        ttk.Label(self, text="REMA:").pack(anchor='w', padx=10)
        self.rema_aluno = ttk.Entry(self, width=30)
        self.rema_aluno.pack(pady=5, padx=10)
        ToolTip(self.rema_aluno, "Digite o REMA do aluno.")

        ttk.Label(self, text="Nome:").pack(anchor='w', padx=10)
        self.nome_aluno = ttk.Entry(self, width=30)
        self.nome_aluno.pack(pady=5, padx=10)
        ToolTip(self.nome_aluno, "Digite o nome completo do aluno.")

        ttk.Label(self, text="Telefone:").pack(anchor='w', padx=10)
        self.telefone_aluno = ttk.Entry(self, width=30)
        self.telefone_aluno.pack(pady=5, padx=10)
        ToolTip(self.telefone_aluno, "Digite o telefone do aluno.")

        ttk.Label(self, text="Endereço:").pack(anchor='w', padx=10)
        self.endereco_aluno = ttk.Entry(self, width=30)
        self.endereco_aluno.pack(pady=5, padx=10)
        ToolTip(self.endereco_aluno, "Digite o endereço do aluno.")

        ttk.Label(self, text="Ano/Turma:").pack(anchor='w', padx=10)
        self.ano_turma_aluno = ttk.Entry(self, width=30)
        self.ano_turma_aluno.pack(pady=5, padx=10)
        ToolTip(self.ano_turma_aluno, "Digite o ano ou turma do aluno.")

        ttk.Button(self, text="Adicionar Aluno", command=self.adicionar_aluno).pack(pady=10)

    def adicionar_aluno(self):
        try:
            rema = int(self.rema_aluno.get())
            nome = self.nome_aluno.get()
            telefone = int(self.telefone_aluno.get())
            endereco = self.endereco_aluno.get()
            ano_turma = self.ano_turma_aluno.get()

            if rema and nome:
                novo_aluno = {
                    'REMA': rema,
                    'Nome': nome,
                    'Telefone': telefone,
                    'Endereço': endereco,
                    'Ano/Turma': ano_turma
                }
                self.biblioteca.alunos[rema] = novo_aluno
                self.salvar_aluno(novo_aluno)
                messagebox.showinfo("Sucesso", "Aluno adicionado com sucesso!")
                self.limpar_campos()
            else:
                messagebox.showerror("Erro", "REMA e Nome são obrigatórios.")
        except ValueError:
            messagebox.showerror("Erro", "REMA e Telefone devem ser números inteiros.")

    def limpar_campos(self):
        self.rema_aluno.delete(0, tk.END)
        self.nome_aluno.delete(0, tk.END)
        self.telefone_aluno.delete(0, tk.END)
        self.endereco_aluno.delete(0, tk.END)
        self.ano_turma_aluno.delete(0, tk.END)

    def salvar_aluno(self, aluno):
        with open('dados/alunos.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=aluno.keys())
            writer.writerow(aluno)

class CadastroLivros(ttk.Frame):
    def __init__(self, biblioteca):
        super().__init__(biblioteca.root)
        self.biblioteca = biblioteca

        ttk.Label(self, text="Adicione Livro", font=('Arial', 14)).pack(pady=10)

        ttk.Label(self, text="Nome do Livro:").pack(anchor='w', padx=10)
        self.nome_livro = ttk.Entry(self, width=30)
        self.nome_livro.pack(pady=5, padx=10)
        ToolTip(self.nome_livro, "Digite o nome do livro.")

        ttk.Label(self, text="Autor:").pack(anchor='w', padx=10)
        self.autor_livro = ttk.Entry(self, width=30)
        self.autor_livro.pack(pady=5, padx=10)
        ToolTip(self.autor_livro, "Digite o autor do livro.")

        ttk.Label(self, text="Categoria:").pack(anchor='w', padx=10)
        self.categoria_livro = ttk.Entry(self, width=30)
        self.categoria_livro.pack(pady=5, padx=10)
        ToolTip(self.categoria_livro, "Digite a categoria do livro.")

        ttk.Label(self, text="URL da Capa do Livro:").pack(anchor='w', padx=10)
        self.url_livro = ttk.Entry(self, width=30)
        self.url_livro.pack(pady=5, padx=10)
        ToolTip(self.url_livro, "Digite a URL da capa em formato JPEG.")

        ttk.Button(self, text="Adicionar Livro", command=self.adicionar_livro).pack(pady=10)

    def adicionar_livro(self):
        nome = self.nome_livro.get()
        autor = self.autor_livro.get()
        categoria = self.categoria_livro.get()
        url_imagem = self.url_livro.get()

        if nome:
            id_livro = str(len(self.biblioteca.livros) + 1)
            caminho_imagem = self.baixar_imagem(url_imagem)

            if caminho_imagem:
                novo_livro = {
                    'ID': id_livro,
                    'Nome do Livro': nome,
                    'Autor': autor,
                    'Categoria': categoria,
                    'Capa': caminho_imagem
                }
                self.biblioteca.livros[int(id_livro)] = novo_livro
                self.salvar_livro(novo_livro)
                self.adicionar_status_livro(novo_livro)
                messagebox.showinfo("Sucesso", "Livro adicionado com sucesso!")
                self.limpar_campos()
            else:
                messagebox.showerror("Erro", "Falha ao baixar a imagem.")
        else:
            messagebox.showerror("Erro", "Nome do Livro é obrigatório.")

    def limpar_campos(self):
        self.nome_livro.delete(0, tk.END)
        self.autor_livro.delete(0, tk.END)
        self.categoria_livro.delete(0, tk.END)
        self.url_livro.delete(0, tk.END)

    def baixar_imagem(self, url):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                caminho_imagem = f"dados/livros/capa_{len(self.biblioteca.livros) + 1}.jpg"
                with open(caminho_imagem, 'wb') as img_file:
                    img_file.write(response.content)
                return caminho_imagem
            else:
                return None
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao baixar a imagem: {str(e)}")
            return None

    def salvar_livro(self, livro):
        with open('dados/livros.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=livro.keys())
            writer.writerow(livro)

    def adicionar_status_livro(self, livro):
        status_livro = {
            'ID Livro': livro['ID'],
            'Nome do Livro': livro['Nome do Livro'],
            'Status': 'DISPONÍVEL'
        }
        self.biblioteca.status_livros[int(livro['ID'])] = status_livro
        self.atualizar_csv_status_livros()

    def atualizar_csv_status_livros(self):
        with open('dados/status_livros.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['ID Livro', 'Nome do Livro', 'Status'])
            writer.writeheader()
            for livro in self.biblioteca.status_livros.values():
                writer.writerow(livro)

class Emprestimos(ttk.Frame):
    def __init__(self, biblioteca):
        super().__init__(biblioteca.root)
        self.biblioteca = biblioteca

        ttk.Label(self, text="Empréstimo de Livros", font=('Arial', 14)).pack(pady=10)

        self.label_rema = ttk.Label(self, text='Identificação do Aluno (REMA):')
        self.label_rema.pack(anchor='w', padx=10)
        self.input_identificacao_aluno = ttk.Entry(self, width=30)
        self.input_identificacao_aluno.pack(pady=5, padx=10)

        ToolTip(self.input_identificacao_aluno, "Digite o REMA do aluno que deseja emprestar o livro.")

        self.label_id_livro = ttk.Label(self, text='Identificação do Livro (ID):')
        self.label_id_livro.pack(anchor='w', padx=10)
        self.input_identificacao_livro = ttk.Entry(self, width=30)
        self.input_identificacao_livro.pack(pady=5, padx=10)

        ToolTip(self.input_identificacao_livro, "Digite o ID do livro que deseja emprestar.")

        ttk.Button(self, text="EMPRÉSTIMO", command=self.emprestar_livro, style="success.TButton").pack(pady=10)
        ttk.Button(self, text="DEVOLVER", command=self.devolver_livro, style="warning.TButton").pack(pady=10)

    def emprestar_livro(self):
        try:
            rema = int(self.input_identificacao_aluno.get())
            id_livro = int(self.input_identificacao_livro.get())

            if self.biblioteca.status_livros[id_livro]['Status'] != 'DISPONÍVEL':
                messagebox.showerror("Erro", "Este livro já está emprestado.")
                return

            id_emprestimo = str(len(self.biblioteca.emprestimos) + 1)
            data_emprestimo = datetime.now().strftime('%Y-%m-%d')
            data_devolucao = (datetime.now() + timedelta(days=15)).strftime('%Y-%m-%d')

            novo_emprestimo = {
                'ID Empréstimo': id_emprestimo,
                'REMA': rema,
                'ID Livro': id_livro,
                'Data do Empréstimo': data_emprestimo,
                'Data de Devolução': data_devolucao
            }
            self.biblioteca.emprestimos[id_emprestimo] = novo_emprestimo

            self.biblioteca.status_livros[id_livro]['Status'] = 'EMPRESTADO'
            self.biblioteca.atualizar_csv_status_livros()

            self.salvar_emprestimo(novo_emprestimo)
            messagebox.showinfo("Sucesso", f"Empréstimo realizado com sucesso!\nDevolução em: {data_devolucao}")
            self.limpar_campos()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def devolver_livro(self):
        try:
            rema = int(self.input_identificacao_aluno.get())
            id_livro = int(self.input_identificacao_livro.get())

            for id_emprestimo, dados in self.biblioteca.emprestimos.items():
                if dados['REMA'] == rema and dados['ID Livro'] == id_livro:
                    del self.biblioteca.emprestimos[id_emprestimo]
                    self.biblioteca.status_livros[id_livro]['Status'] = 'DISPONÍVEL'
                    self.biblioteca.atualizar_csv_status_livros()
                    messagebox.showinfo("Sucesso", "Livro devolvido com sucesso!")
                    self.limpar_campos()
                    return

            messagebox.showerror("Erro", "Empréstimo não encontrado.")
        except ValueError:
            messagebox.showerror("Erro", "REMA e ID do livro devem ser números inteiros.")

    def salvar_emprestimo(self, emprestimo):
        with open('dados/emprestimos.csv', mode='a', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=emprestimo.keys())
            writer.writerow(emprestimo)

    def limpar_campos(self):
        self.input_identificacao_aluno.delete(0, tk.END)
        self.input_identificacao_livro.delete(0, tk.END)

class Pesquisa(ttk.Frame):
    def __init__(self, biblioteca):
        super().__init__(biblioteca.root)
        self.biblioteca = biblioteca

        self.tab_control = ttk.Notebook(self)

        # Guia para pesquisa de Alunos
        self.pesquisa_alunos = ttk.Frame(self.tab_control)
        self.tab_control.add(self.pesquisa_alunos, text='Alunos')

        ttk.Label(self.pesquisa_alunos, text='Filtrar por:').pack(pady=5, padx=10)
        self.filtro_alunos = ttk.Combobox(self.pesquisa_alunos, values=['REMA', 'Nome', 'Telefone', 'Endereço', 'Ano/Turma'])
        self.filtro_alunos.set('REMA')
        self.filtro_alunos.pack(pady=5, padx=10)

        self.input_pesquisa_aluno = ttk.Entry(self.pesquisa_alunos, width=30)
        self.input_pesquisa_aluno.pack(pady=5, padx=10)

        ttk.Button(self.pesquisa_alunos, text="Pesquisar", command=self.pesquisar_alunos).pack(pady=10)

        self.tree_resultados_alunos = ttk.Treeview(self.pesquisa_alunos, columns=('REMA', 'Nome', 'Telefone', 'Endereço', 'Ano/Turma'), show='headings')
        self.tree_resultados_alunos.heading('REMA', text='REMA')
        self.tree_resultados_alunos.heading('Nome', text='Nome')
        self.tree_resultados_alunos.heading('Telefone', text='Telefone')
        self.tree_resultados_alunos.heading('Endereço', text='Endereço')
        self.tree_resultados_alunos.heading('Ano/Turma', text='Ano/Turma')
        self.tree_resultados_alunos.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self.pesquisa_alunos, text="Editar", command=self.editar_aluno).pack(pady=5)
        ttk.Button(self.pesquisa_alunos, text="Excluir", command=self.excluir_aluno).pack(pady=5)

        # Guia para pesquisa de Livros
        self.pesquisa_livros = ttk.Frame(self.tab_control)
        self.tab_control.add(self.pesquisa_livros, text='Livros')

        ttk.Label(self.pesquisa_livros, text='Filtrar por:').pack(pady=5, padx=10)
        self.filtro_livros = ttk.Combobox(self.pesquisa_livros, values=['ID', 'Nome do Livro', 'Autor', 'Categoria'])
        self.filtro_livros.set('ID')
        self.filtro_livros.pack(pady=5, padx=10)

        self.input_pesquisa_livro = ttk.Entry(self.pesquisa_livros, width=30)
        self.input_pesquisa_livro.pack(pady=5, padx=10)

        ttk.Button(self.pesquisa_livros, text="Pesquisar", command=self.pesquisar_livros).pack(pady=10)

        self.tree_resultados_livros = ttk.Treeview(self.pesquisa_livros, columns=('ID', 'Nome do Livro', 'Autor', 'Categoria', 'Capa'), show='headings')
        self.tree_resultados_livros.heading('ID', text='ID')
        self.tree_resultados_livros.heading('Nome do Livro', text='Nome do Livro')
        self.tree_resultados_livros.heading('Autor', text='Autor')
        self.tree_resultados_livros.heading('Categoria', text='Categoria')
        self.tree_resultados_livros.heading('Capa', text='Capa')
        self.tree_resultados_livros.pack(fill=tk.BOTH, expand=True)

        self.tree_resultados_livros.bind("<<TreeviewSelect>>", self.on_select)

        ttk.Button(self.pesquisa_livros, text="Editar", command=self.editar_livro).pack(pady=5)
        ttk.Button(self.pesquisa_livros, text="Excluir", command=self.excluir_livro).pack(pady=5)

        # Contêiner para exibir a imagem da capa
        self.container_imagem = ttk.Frame(self.pesquisa_livros)
        self.container_imagem.pack(pady=10)
        self.label_imagem = tk.Label(self.container_imagem)
        self.label_imagem.pack()

        self.tab_control.pack(expand=True, fill='both')

    def pesquisar_alunos(self):
        termo = self.input_pesquisa_aluno.get().strip()
        coluna = self.filtro_alunos.get()

        resultados = []
        for aluno in self.biblioteca.alunos.values():
            if coluna == 'REMA' and termo.lower() in str(aluno['REMA']).lower():
                resultados.append(aluno)
            elif coluna == 'Nome' and termo.lower() in aluno['Nome'].lower():
                resultados.append(aluno)
            elif coluna == 'Telefone' and termo in str(aluno['Telefone']):
                resultados.append(aluno)
            elif coluna == 'Endereço' and termo.lower() in aluno['Endereço'].lower():
                resultados.append(aluno)
            elif coluna == 'Ano/Turma' and termo.lower() in aluno['Ano/Turma'].lower():
                resultados.append(aluno)

        self.mostrar_resultados_alunos(resultados)

    def mostrar_resultados_alunos(self, resultados):
        self.tree_resultados_alunos.delete(*self.tree_resultados_alunos.get_children())

        for aluno in resultados:
            self.tree_resultados_alunos.insert('', 'end', values=(aluno['REMA'], aluno['Nome'], aluno['Telefone'], aluno['Endereço'], aluno['Ano/Turma']))

    def editar_aluno(self):
        selected_item = self.tree_resultados_alunos.selection()
        if selected_item:
            aluno = self.tree_resultados_alunos.item(selected_item)['values']
            EditarAluno(self.biblioteca, aluno)

    def excluir_aluno(self):
        selected_item = self.tree_resultados_alunos.selection()
        if selected_item:
            aluno = self.tree_resultados_alunos.item(selected_item)['values']
            rema = int(aluno[0])
            del self.biblioteca.alunos[rema]
            self.atualizar_csv_alunos()
            messagebox.showinfo("Sucesso", "Aluno excluído com sucesso!")
            self.pesquisar_alunos()

    def atualizar_csv_alunos(self):
        with open('dados/alunos.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['REMA', 'Nome', 'Telefone', 'Endereço', 'Ano/Turma'])
            writer.writeheader()
            for aluno in self.biblioteca.alunos.values():
                writer.writerow(aluno)

    def pesquisar_livros(self):
        termo = self.input_pesquisa_livro.get().strip()
        coluna = self.filtro_livros.get()

        resultados = []
        for livro in self.biblioteca.livros.values():
            if coluna == 'ID' and termo in str(livro['ID']):
                resultados.append(livro)
            elif coluna == 'Nome do Livro' and termo.lower() in livro['Nome do Livro'].lower():
                resultados.append(livro)
            elif coluna == 'Autor' and termo.lower() in livro['Autor'].lower():
                resultados.append(livro)
            elif coluna == 'Categoria' and termo.lower() in livro['Categoria'].lower():
                resultados.append(livro)

        self.mostrar_resultados_livros(resultados)

    def mostrar_resultados_livros(self, resultados):
        self.tree_resultados_livros.delete(*self.tree_resultados_livros.get_children())

        for livro in resultados:
            self.tree_resultados_livros.insert('', 'end', values=(livro['ID'], livro['Nome do Livro'], livro['Autor'], livro['Categoria'], livro['Capa']))

    def on_select(self, event):
        selected_item = self.tree_resultados_livros.selection()
        if selected_item:
            item = self.tree_resultados_livros.item(selected_item)
            livro = item['values']
            self.exibir_capa(livro[4])  # Capa é o 5º item (índice 4)

    def exibir_capa(self, caminho_imagem):
        # Tente carregar a imagem e mostre-a no contêiner
        try:
            image = Image.open(caminho_imagem)
            image = image.resize((150, 200), Image.LANCZOS)  # Ajuste o tamanho da imagem
            photo = ImageTk.PhotoImage(image)

            # Atualize o label da imagem no contêiner
            self.label_imagem.config(image=photo)
            self.label_imagem.image = photo  # Mantenha uma referência para evitar garbage collection
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível exibir a imagem.\n{str(e)}")

    def editar_livro(self):
        selected_item = self.tree_resultados_livros.selection()
        if selected_item:
            livro = self.tree_resultados_livros.item(selected_item)['values']
            EditarLivro(self.biblioteca, livro)

    def excluir_livro(self):
        selected_item = self.tree_resultados_livros.selection()
        if selected_item:
            livro = self.tree_resultados_livros.item(selected_item)['values']
            livro_id = int(livro[0])
            del self.biblioteca.livros[livro_id]
            self.atualizar_csv_livros()
            messagebox.showinfo("Sucesso", "Livro excluído com sucesso!")
            self.pesquisar_livros()

    def atualizar_csv_livros(self):
        with open('dados/livros.csv', mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['ID', 'Nome do Livro', 'Autor', 'Categoria', 'Capa'])
            writer.writeheader()
            for livro in self.biblioteca.livros.values():
                writer.writerow(livro)

class EditarAluno:
    def __init__(self, biblioteca, aluno):
        self.biblioteca = biblioteca
        self.aluno = aluno

        self.janela = tk.Toplevel()
        self.janela.title("Editar Aluno")

        ttk.Label(self.janela, text="Editar Aluno", font=('Arial', 14)).pack(pady=10)

        self.rema_aluno = ttk.Entry(self.janela, width=30)
        self.rema_aluno.pack(pady=5, padx=10)
        self.rema_aluno.insert(0, str(aluno[0]))

        self.nome_aluno = ttk.Entry(self.janela, width=30)
        self.nome_aluno.pack(pady=5, padx=10)
        self.nome_aluno.insert(0, aluno[1])

        self.telefone_aluno = ttk.Entry(self.janela, width=30)
        self.telefone_aluno.pack(pady=5, padx=10)
        self.telefone_aluno.insert(0, aluno[2])

        self.endereco_aluno = ttk.Entry(self.janela, width=30)
        self.endereco_aluno.pack(pady=5, padx=10)
        self.endereco_aluno.insert(0, aluno[3])

        self.ano_turma_aluno = ttk.Entry(self.janela, width=30)
        self.ano_turma_aluno.pack(pady=5, padx=10)
        self.ano_turma_aluno.insert(0, aluno[4])

        ttk.Button(self.janela, text="Salvar Alterações", command=self.salvar_alteracoes).pack(pady=10)

    def salvar_alteracoes(self):
        try:
            rema = int(self.rema_aluno.get())
            nome = self.nome_aluno.get()
            telefone = int(self.telefone_aluno.get())
            endereco = self.endereco_aluno.get()
            ano_turma = self.ano_turma_aluno.get()

            aluno_atualizado = {
                'REMA': rema,
                'Nome': nome,
                'Telefone': telefone,
                'Endereço': endereco,
                'Ano/Turma': ano_turma
            }
            self.biblioteca.alunos[rema] = aluno_atualizado
            self.biblioteca.atualizar_csv_alunos()
            messagebox.showinfo("Sucesso", "Aluno atualizado com sucesso!")
            self.janela.destroy()
            self.biblioteca.aba_pesquisa.pesquisar_alunos()
        except ValueError:
            messagebox.showerror("Erro", "Verifique os dados inseridos.")

class EditarLivro:
    def __init__(self, biblioteca, livro):
        self.biblioteca = biblioteca
        self.livro = livro

        self.janela = tk.Toplevel()
        self.janela.title("Editar Livro")

        ttk.Label(self.janela, text="Editar Livro", font=('Arial', 14)).pack(pady=10)

        self.nome_livro = ttk.Entry(self.janela, width=30)
        self.nome_livro.pack(pady=5, padx=10)
        self.nome_livro.insert(0, livro[1])

        self.autor_livro = ttk.Entry(self.janela, width=30)
        self.autor_livro.pack(pady=5, padx=10)
        self.autor_livro.insert(0, livro[2])

        self.categoria_livro = ttk.Entry(self.janela, width=30)
        self.categoria_livro.pack(pady=5, padx=10)
        self.categoria_livro.insert(0, livro[3])

        ttk.Button(self.janela, text="Salvar Alterações", command=self.salvar_alteracoes).pack(pady=10)

    def salvar_alteracoes(self):
        try:
            nome = self.nome_livro.get()
            autor = self.autor_livro.get()
            categoria = self.categoria_livro.get()

            livro_atualizado = {
                'ID': self.livro[0],
                'Nome do Livro': nome,
                'Autor': autor,
                'Categoria': categoria,
                'Capa': self.livro[4]  # Mantém o caminho da imagem
            }
            self.biblioteca.livros[int(livro_atualizado['ID'])] = livro_atualizado
            self.biblioteca.atualizar_csv_livros()
            messagebox.showinfo("Sucesso", "Livro atualizado com sucesso!")
            self.janela.destroy()
            self.biblioteca.aba_pesquisa.pesquisar_livros()
        except ValueError:
            messagebox.showerror("Erro", "Verifique os dados inseridos.")

class Relatorios(ttk.Frame):
    def __init__(self, biblioteca):
        super().__init__(biblioteca.root)
        self.biblioteca = biblioteca

        ttk.Label(self, text="Relatórios de Empréstimos", font=('Arial', 14)).pack(pady=10)

        self.tree_resultados_emprestimos = ttk.Treeview(self, columns=('ID Empréstimo', 'REMA', 'Nome do Aluno', 'ID Livro', 'Nome do Livro', 'Data do Empréstimo', 'Data de Devolução'), show='headings')
        
        self.tree_resultados_emprestimos.heading('ID Empréstimo', text='ID Empréstimo')
        self.tree_resultados_emprestimos.heading('REMA', text='REMA')
        self.tree_resultados_emprestimos.heading('Nome do Aluno', text='Nome do Aluno')
        self.tree_resultados_emprestimos.heading('ID Livro', text='ID Livro')
        self.tree_resultados_emprestimos.heading('Nome do Livro', text='Nome do Livro')
        self.tree_resultados_emprestimos.heading('Data do Empréstimo', text='Data do Empréstimo')
        self.tree_resultados_emprestimos.heading('Data de Devolução', text='Data de Devolução')
        
        self.tree_resultados_emprestimos.pack(fill=tk.BOTH, expand=True)

        ttk.Button(self, text="Atualizar Empréstimos", command=self.carregar_relatorios).pack(pady=10)

        self.carregar_relatorios()

    def carregar_relatorios(self):
        self.tree_resultados_emprestimos.delete(*self.tree_resultados_emprestimos.get_children()) 

        for emprestimo in self.biblioteca.emprestimos.values():
            rema = emprestimo['REMA']
            aluno = self.biblioteca.alunos.get(rema, {})
            nome_aluno = aluno.get('Nome', 'Desconhecido')
            id_livro = emprestimo['ID Livro']
            livro = self.biblioteca.livros.get(id_livro, {})
            nome_livro = livro.get('Nome do Livro', 'Desconhecido')
            self.tree_resultados_emprestimos.insert('', 'end', values=(emprestimo['ID Empréstimo'], rema, nome_aluno, id_livro, nome_livro, emprestimo['Data do Empréstimo'], emprestimo['Data de Devolução']))

def main():
    root = tk.Tk()
    style = Style(theme='vapor')

    style.configure('success.TButton', background='green', foreground='white')
    style.configure('warning.TButton', background='yellow', foreground='black')

    # Inicia com a tela de login
    LoginScreen(root, lambda: BibliotecaDigital(root))

    root.mainloop()

if __name__ == "__main__":
    main()