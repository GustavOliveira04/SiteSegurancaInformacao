import os
import uuid
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, send_from_directory, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

from banco import consultarTodos, consultarUm, criarTabelas, executar

app = Flask(__name__)

# ===== CONFIGURAÇÃO =====
pastaBase = os.path.dirname(os.path.abspath(__file__))
pastaUploads = os.path.join(pastaBase, "uploads")
extensoesPermitidas = ["pdf", "png", "jpg", "jpeg"]
perfisValidos = ["administrador", "operador", "cliente"]
equipe = ("administrador", "operador")

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

os.makedirs(pastaUploads, exist_ok=True)
criarTabelas()


# ===== FORMATAÇÃO NOS TEMPLATES =====
@app.template_filter("dataBr")
def dataBr(valor):
    partes = valor[:10].split("-")
    return partes[2] + "/" + partes[1] + "/" + partes[0]


@app.template_filter("moeda")
def moeda(valor):
    texto = "{:,.2f}".format(valor)
    texto = texto.replace(",", "X").replace(".", ",").replace("X", ".")
    return "R$ " + texto


# ===== LOGIN E PERMISSÕES (RBAC) =====
@app.before_request
def carregarUsuario():
    g.usuario = None
    usuarioId = session.get("usuarioId")
    if usuarioId is not None:
        g.usuario = consultarUm(
            "SELECT id, nome, email, perfil, contratoId FROM usuarios WHERE id = ?", (usuarioId,))
        if g.usuario is None:
            session.clear()


def loginObrigatorio(funcao):
    @wraps(funcao)
    def verificar(*args, **kwargs):
        if g.usuario is None:
            return redirect(url_for("login"))
        return funcao(*args, **kwargs)
    return verificar


def perfilObrigatorio(*perfisPermitidos):
    def decorador(funcao):
        @wraps(funcao)
        def verificar(*args, **kwargs):
            if g.usuario is None:
                return redirect(url_for("login"))
            if g.usuario["perfil"] not in perfisPermitidos:
                abort(403)
            return funcao(*args, **kwargs)
        return verificar
    return decorador


@app.route("/")
def raiz():
    return redirect(url_for("inicio"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario is not None:
        return redirect(url_for("inicio"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        senha = request.form.get("senha", "")
        usuario = consultarUm("SELECT id, senhaHash FROM usuarios WHERE email = ?", (email,))
        if usuario is not None and check_password_hash(usuario["senhaHash"], senha):
            session.clear()
            session["usuarioId"] = usuario["id"]
            return redirect(url_for("inicio"))
        return render_template("login.html", erro="E-mail ou senha incorretos."), 401

    return render_template("login.html", erro=None)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("login"))


# ===== INÍCIO =====
def resumoGalpoes():
    return consultarTodos("""
        SELECT g.id, g.nome, g.cidade, g.endereco, g.capacidade,
               COALESCE(SUM(m.paletes), 0) AS ocupados,
               ROUND(COALESCE(SUM(m.paletes), 0) * 100.0 / g.capacidade) AS ocupacao
        FROM galpoes g
        LEFT JOIN mercadorias m ON m.galpaoId = g.id
        GROUP BY g.id
        ORDER BY g.id""")


@app.route("/inicio")
@loginObrigatorio
def inicio():
    empresas = []
    if g.usuario["perfil"] == "cliente":
        resumo = consultarTodos("""
            SELECT ga.nome AS galpao, COUNT(m.id) AS itens, SUM(m.paletes) AS paletes
            FROM mercadorias m
            JOIN galpoes ga ON ga.id = m.galpaoId
            WHERE m.contratoId = ?
            GROUP BY ga.id
            ORDER BY ga.id""", (g.usuario["contratoId"],))
    else:
        resumo = resumoGalpoes()
        empresas = consultarTodos("SELECT empresa FROM contratos ORDER BY empresa")
    return render_template("inicio.html", resumo=resumo, empresas=empresas)


# ===== GALPÕES =====
@app.route("/galpoes")
@perfilObrigatorio(*equipe)
def galpoes():
    return render_template("galpoes.html", galpoes=resumoGalpoes())


# ===== INVENTÁRIO =====
@app.route("/inventario")
@loginObrigatorio
def inventario():
    busca = request.args.get("q", "").strip()
    sql = """
        SELECT m.id, m.codigo, m.descricao, m.quantidade, m.paletes, m.comprovante, m.entradaEm,
               ga.nome AS galpao, c.empresa AS empresa
        FROM mercadorias m
        JOIN galpoes ga ON ga.id = m.galpaoId
        JOIN contratos c ON c.id = m.contratoId
        WHERE (m.descricao LIKE ? OR m.codigo LIKE ?)"""
    parametros = ["%" + busca + "%", "%" + busca + "%"]

    if g.usuario["perfil"] == "cliente":
        sql += " AND m.contratoId = ?"
        parametros.append(g.usuario["contratoId"])

    sql += " ORDER BY m.id DESC"
    mercadorias = consultarTodos(sql, parametros)
    return render_template("inventario.html", mercadorias=mercadorias, busca=busca)


@app.route("/inventario/novo", methods=["GET", "POST"])
@perfilObrigatorio(*equipe)
def novaMercadoria():
    listaGalpoes = consultarTodos("SELECT id, nome, cidade FROM galpoes ORDER BY id")
    listaContratos = consultarTodos("SELECT id, empresa FROM contratos ORDER BY empresa")

    if request.method == "POST":
        codigo = request.form.get("codigo", "").strip()
        descricao = request.form.get("descricao", "").strip()
        quantidade = request.form.get("quantidade", "")
        paletes = request.form.get("paletes", "")
        galpaoId = request.form.get("galpaoId", "")
        contratoId = request.form.get("contratoId", "")
        arquivo = request.files.get("comprovante")

        erro = None
        if codigo == "" or descricao == "":
            erro = "Preencha o código e a descrição."
        elif len(codigo) > 30 or len(descricao) > 120:
            erro = "Código (até 30) ou descrição (até 120) muito longos."
        elif not quantidade.isdecimal() or not paletes.isdecimal() or int(quantidade) < 1 or int(paletes) < 1:
            erro = "Quantidade e paletes devem ser números maiores que zero."
        elif consultarUm("SELECT id FROM galpoes WHERE id = ?", (galpaoId,)) is None:
            erro = "Escolha um galpão válido."
        elif consultarUm("SELECT id FROM contratos WHERE id = ?", (contratoId,)) is None:
            erro = "Escolha uma empresa (contrato) válida."

        nomeArquivo = None
        if erro is None and arquivo is not None and arquivo.filename != "":
            extensao = os.path.splitext(arquivo.filename)[1].lower().lstrip(".")
            if extensao not in extensoesPermitidas:
                erro = "O comprovante deve ser PDF, PNG ou JPG."
            else:
                nomeArquivo = uuid.uuid4().hex + "." + extensao

        if erro is None:
            if nomeArquivo is not None:
                arquivo.save(os.path.join(pastaUploads, nomeArquivo))
            executar(
                "INSERT INTO mercadorias (codigo, descricao, quantidade, paletes, galpaoId, contratoId, comprovante) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (codigo, descricao, int(quantidade), int(paletes), galpaoId, contratoId, nomeArquivo))
            flash("Mercadoria cadastrada com sucesso.", "sucesso")
            return redirect(url_for("inventario"))

        flash(erro, "erro")

    return render_template("mercadoria.html", galpoes=listaGalpoes, contratos=listaContratos)


@app.route("/comprovante/<int:mercadoriaId>")
@loginObrigatorio
def comprovante(mercadoriaId):
    mercadoria = consultarUm("SELECT comprovante, contratoId FROM mercadorias WHERE id = ?", (mercadoriaId,))
    if mercadoria is None or mercadoria["comprovante"] is None:
        abort(404)
    if g.usuario["perfil"] == "cliente" and g.usuario["contratoId"] != mercadoria["contratoId"]:
        abort(403)
    return send_from_directory(pastaUploads, mercadoria["comprovante"])


# ===== CONTRATOS =====
@app.route("/contratos")
@perfilObrigatorio("administrador")
def contratos():
    lista = consultarTodos("SELECT * FROM contratos ORDER BY empresa")
    return render_template("contratos.html", contratos=lista)


# ===== ADMINISTRAÇÃO DE USUÁRIOS =====
@app.route("/admin")
@perfilObrigatorio("administrador")
def admin():
    busca = request.args.get("q", "").strip()
    usuarios = consultarTodos("""
        SELECT u.id, u.nome, u.email, u.perfil, c.empresa
        FROM usuarios u
        LEFT JOIN contratos c ON c.id = u.contratoId
        WHERE u.nome LIKE ? OR u.email LIKE ?
        ORDER BY u.id""", ("%" + busca + "%", "%" + busca + "%"))
    listaContratos = consultarTodos("SELECT id, empresa FROM contratos ORDER BY empresa")
    return render_template("admin.html", usuarios=usuarios, contratos=listaContratos, busca=busca)


@app.route("/admin/usuarios", methods=["POST"])
@perfilObrigatorio("administrador")
def criarUsuario():
    nome = request.form.get("nome", "").strip()
    email = request.form.get("email", "").strip().lower()
    senha = request.form.get("senha", "")
    perfil = request.form.get("perfil", "")
    contratoId = request.form.get("contratoId", "")

    erro = None
    if nome == "" or len(nome) > 100:
        erro = "Informe o nome (até 100 caracteres)."
    elif "@" not in email or len(email) > 120:
        erro = "Informe um e-mail válido."
    elif len(senha) < 8:
        erro = "A senha deve ter pelo menos 8 caracteres."
    elif perfil not in perfisValidos:
        erro = "Perfil inválido."
    elif consultarUm("SELECT id FROM usuarios WHERE email = ?", (email,)) is not None:
        erro = "Já existe um usuário com esse e-mail."

    if erro is None and perfil == "cliente":
        if not contratoId.isdecimal() or consultarUm("SELECT id FROM contratos WHERE id = ?", (contratoId,)) is None:
            erro = "Clientes precisam estar ligados a uma empresa (contrato)."

    if erro is not None:
        flash(erro, "erro")
        return redirect(url_for("admin"))

    if perfil != "cliente":
        contratoId = None
    executar("INSERT INTO usuarios (nome, email, senhaHash, perfil, contratoId) VALUES (?, ?, ?, ?, ?)",
             (nome, email, generate_password_hash(senha), perfil, contratoId))
    flash("Usuário criado com sucesso.", "sucesso")
    return redirect(url_for("admin"))


@app.route("/admin/usuarios/<int:usuarioId>/excluir", methods=["POST"])
@perfilObrigatorio("administrador")
def excluirUsuario(usuarioId):
    if usuarioId == g.usuario["id"]:
        flash("Você não pode excluir o seu próprio usuário.", "erro")
    else:
        executar("DELETE FROM usuarios WHERE id = ?", (usuarioId,))
        flash("Usuário excluído.", "sucesso")
    return redirect(url_for("admin"))


# ===== PÁGINAS DE ERRO =====
@app.errorhandler(403)
def erro403(erro):
    return render_template("erro.html", codigo=403, mensagem="Você não tem permissão para acessar esta página."), 403


@app.errorhandler(404)
def erro404(erro):
    return render_template("erro.html", codigo=404, mensagem="Página não encontrada."), 404


@app.errorhandler(413)
def erro413(erro):
    return render_template("erro.html", codigo=413, mensagem="Arquivo muito grande. O limite é de 2 MB."), 413


if __name__ == "__main__":
    app.run()
