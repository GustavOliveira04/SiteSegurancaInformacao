import datetime
import random
import secrets
import unicodedata

from werkzeug.security import generate_password_hash

from banco import conectar, criarTabelas

random.seed(2026)


def semAcento(texto):
    normalizado = unicodedata.normalize("NFD", texto)
    resultado = ""
    for letra in normalizado:
        if unicodedata.category(letra) != "Mn":
            resultado += letra
    return resultado


# ===== DADOS FICTÍCIOS =====
contratos = [
    {
        "empresa": "Alimentos Vale Verde S.A.", "cnpj": "41.208.553/0001-07", "dominio": "valeverde.com.br",
        "responsavel": "Helena Barbosa", "telefone": "(11) 3456-7801",
        "inicio": "2025-02-01", "fim": "2027-01-31", "valor": 18500.00, "prefixo": "AVV",
        "itens": ["Arroz tipo 1 - fardo 30 kg", "Feijão carioca - fardo 30 kg", "Óleo de soja - caixa 20 un",
                  "Açúcar cristal - fardo 50 kg", "Macarrão espaguete - caixa 20 un", "Farinha de trigo - saco 25 kg",
                  "Café torrado - caixa 40 un", "Molho de tomate - caixa 24 un"],
    },
    {
        "empresa": "FarmaVida Distribuidora Ltda", "cnpj": "27.915.304/0001-62", "dominio": "farmavida.com.br",
        "responsavel": "Ricardo Menezes", "telefone": "(19) 3322-4410",
        "inicio": "2025-05-15", "fim": "2027-05-14", "valor": 24300.00, "prefixo": "FVD",
        "itens": ["Dipirona 500 mg - caixa 100 un", "Álcool 70% - caixa 12 un", "Luvas de procedimento - caixa 10 cx",
                  "Máscara descartável - caixa 50 un", "Gaze estéril - pacote 500 un", "Soro fisiológico 500 ml - caixa 24 un",
                  "Seringa 10 ml - caixa 100 un", "Termômetro digital - caixa 20 un"],
    },
    {
        "empresa": "TecnoPeças Eletrônicos Ltda", "cnpj": "33.671.089/0001-45", "dominio": "tecnopecas.com.br",
        "responsavel": "Patrícia Nunes", "telefone": "(11) 4002-7788",
        "inicio": "2025-08-01", "fim": "2026-07-31", "valor": 15200.00, "prefixo": "TPE",
        "itens": ["Placa-mãe ATX - caixa 10 un", "Memória RAM DDR4 8 GB - caixa 50 un", "SSD 480 GB - caixa 40 un",
                  "Fonte 500 W - caixa 20 un", "Cabo HDMI 2 m - caixa 100 un", "Monitor 24 pol. - caixa 6 un",
                  "Teclado USB - caixa 20 un", "Mouse óptico - caixa 50 un"],
    },
    {
        "empresa": "Moda Estilo Têxtil Ltda", "cnpj": "18.442.760/0001-23", "dominio": "modaestilo.com.br",
        "responsavel": "Fernanda Lacerda", "telefone": "(41) 3030-2190",
        "inicio": "2026-01-10", "fim": "2028-01-09", "valor": 12800.00, "prefixo": "MET",
        "itens": ["Camiseta algodão - fardo 100 un", "Calça jeans - caixa 50 un", "Jaqueta corta-vento - caixa 30 un",
                  "Meia esportiva - caixa 200 pares", "Vestido casual - caixa 40 un", "Boné aba curva - caixa 100 un",
                  "Camisa polo - caixa 60 un", "Moletom - caixa 40 un"],
    },
    {
        "empresa": "AutoParts Brasil Comércio S.A.", "cnpj": "52.037.918/0001-84", "dominio": "autopartsbr.com.br",
        "responsavel": "Sérgio Tavares", "telefone": "(13) 3251-9034",
        "inicio": "2025-11-03", "fim": "2027-11-02", "valor": 21700.00, "prefixo": "APB",
        "itens": ["Filtro de óleo - caixa 50 un", "Pastilha de freio - caixa 30 jogos", "Amortecedor dianteiro - caixa 8 un",
                  "Bateria 60 Ah - caixa 6 un", "Vela de ignição - caixa 100 un", "Correia dentada - caixa 40 un",
                  "Pneu aro 15 - lote 20 un", "Lâmpada H7 - caixa 50 un"],
    },
    {
        "empresa": "Bebidas Serra Azul Ltda", "cnpj": "09.586.447/0001-31", "dominio": "serraazul.com.br",
        "responsavel": "Márcia Prado", "telefone": "(15) 3411-6620",
        "inicio": "2026-03-01", "fim": "2027-02-28", "valor": 16900.00, "prefixo": "BSA",
        "itens": ["Água mineral 500 ml - fardo 12 un", "Refrigerante cola 2 L - fardo 6 un", "Suco de laranja 1 L - caixa 12 un",
                  "Cerveja lata 350 ml - caixa 12 un", "Energético 250 ml - caixa 24 un", "Chá gelado 450 ml - caixa 12 un",
                  "Água com gás 500 ml - fardo 12 un", "Isotônico 500 ml - caixa 12 un"],
    },
    {
        "empresa": "Casa & Lar Utilidades Ltda", "cnpj": "64.120.835/0001-56", "dominio": "casaelar.com.br",
        "responsavel": "Otávio Brandão", "telefone": "(67) 3318-5502",
        "inicio": "2025-09-20", "fim": "2027-09-19", "valor": 11400.00, "prefixo": "CLU",
        "itens": ["Jogo de panelas 5 peças - caixa 6 un", "Conjunto de talheres 24 peças - caixa 12 un", "Liquidificador 700 W - caixa 8 un",
                  "Ventilador de mesa - caixa 6 un", "Jogo de toalhas - fardo 20 un", "Aspirador de pó - caixa 4 un",
                  "Ferro de passar a vapor - caixa 10 un", "Cesto organizador - fardo 30 un"],
    },
    {
        "empresa": "Papelaria Central Atacado Ltda", "cnpj": "75.903.261/0001-18", "dominio": "papelariacentral.com.br",
        "responsavel": "Cláudia Rangel", "telefone": "(11) 2789-3345",
        "inicio": "2026-02-02", "fim": "2028-02-01", "valor": 9800.00, "prefixo": "PCA",
        "itens": ["Papel sulfite A4 - caixa 10 resmas", "Caneta esferográfica - caixa 50 un", "Caderno 96 folhas - fardo 20 un",
                  "Grampeador - caixa 12 un", "Pasta suspensa - caixa 50 un", "Marca-texto - caixa 12 un",
                  "Cola branca 90 g - caixa 24 un", "Tesoura escolar - caixa 24 un"],
    },
]

galpoes = [
    {"nome": "Galpão A", "cidade": "São Paulo", "endereco": "Rod. Anhanguera, km 18", "ocupacao": 0.82},
    {"nome": "Galpão B", "cidade": "Campinas", "endereco": "Rod. Dom Pedro I, km 95", "ocupacao": 0.64},
    {"nome": "Galpão C", "cidade": "Santos", "endereco": "Av. Portuária, 450", "ocupacao": 0.91},
    {"nome": "Galpão D", "cidade": "Sorocaba", "endereco": "Rod. Raposo Tavares, km 100", "ocupacao": 0.47},
    {"nome": "Galpão E", "cidade": "Campo Grande", "endereco": "Av. Gury Marques, 3200", "ocupacao": 0.73},
    {"nome": "Galpão F", "cidade": "Curitiba", "endereco": "Rua das Indústrias, 800", "ocupacao": 0.58},
]

primeirosNomes = ["Ana", "Bruno", "Carla", "Diego", "Eduarda", "Felipe", "Gabriela", "Henrique", "Isabela",
                  "João", "Karina", "Lucas", "Mariana", "Nicolas", "Olívia", "Paulo", "Renata", "Rafael",
                  "Sabrina", "Thiago", "Vanessa", "Vinícius", "Wesley", "Yasmin", "Letícia"]
sobrenomes = ["Almeida", "Barbosa", "Cardoso", "Dias", "Teixeira", "Ferreira", "Gomes", "Lima", "Martins",
              "Nogueira", "Pinto", "Pereira", "Ramos", "Souza", "Silva", "Costa", "Rocha", "Moreira",
              "Araújo", "Batista", "Carvalho", "Duarte", "Fernandes", "Machado", "Monteiro"]

# ===== USUÁRIOS (3 contas de teste + 47 gerados = 50) =====
usuarios = []
usuarios.append({"nome": "Administrador Teste", "email": "admin@cargoconnect.com.br",
                 "senha": "Admin#Cargo2026", "perfil": "administrador", "contratoId": None})
usuarios.append({"nome": "Operador Teste", "email": "operador@cargoconnect.com.br",
                 "senha": "Oper#Cargo2026", "perfil": "operador", "contratoId": None})
usuarios.append({"nome": "Cliente Teste", "email": "cliente@valeverde.com.br",
                 "senha": "Cliente#Cargo2026", "perfil": "cliente", "contratoId": 1})

for i in range(47):
    primeiro = primeirosNomes[i % 25]
    sobrenome = sobrenomes[(i * 7 + i // 25) % 25]
    emailLocal = semAcento(primeiro).lower() + "." + semAcento(sobrenome).lower()

    if i == 0:
        perfil = "administrador"
        contratoId = None
        dominio = "cargoconnect.com.br"
    elif i <= 7:
        perfil = "operador"
        contratoId = None
        dominio = "cargoconnect.com.br"
    else:
        perfil = "cliente"
        contratoId = ((i - 8) % 8) + 1
        dominio = contratos[contratoId - 1]["dominio"]

    usuarios.append({"nome": primeiro + " " + sobrenome, "email": emailLocal + "@" + dominio,
                     "senha": secrets.token_urlsafe(12), "perfil": perfil, "contratoId": contratoId})


# ===== GRAVAÇÃO NO BANCO =====
criarTabelas()
conexao = conectar()

if conexao.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] > 0:
    print("O banco já está populado. Para recomeçar, apague o arquivo cargoconnect.db e rode de novo.")
    conexao.close()
    raise SystemExit

for contrato in contratos:
    conexao.execute(
        "INSERT INTO contratos (empresa, cnpj, responsavel, email, telefone, dataInicio, dataFim, valorMensal) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (contrato["empresa"], contrato["cnpj"], contrato["responsavel"],
         semAcento(contrato["responsavel"].split(" ")[0]).lower() + "@" + contrato["dominio"],
         contrato["telefone"], contrato["inicio"], contrato["fim"], contrato["valor"]))

for galpao in galpoes:
    conexao.execute("INSERT INTO galpoes (nome, cidade, endereco, capacidade) VALUES (?, ?, ?, 1)",
                    (galpao["nome"], galpao["cidade"], galpao["endereco"]))

for usuario in usuarios:
    conexao.execute("INSERT INTO usuarios (nome, email, senhaHash, perfil, contratoId) VALUES (?, ?, ?, ?, ?)",
                    (usuario["nome"], usuario["email"], generate_password_hash(usuario["senha"]),
                     usuario["perfil"], usuario["contratoId"]))

dataInicial = datetime.date(2026, 6, 1)
for indice in range(len(contratos)):
    contrato = contratos[indice]
    numero = 1
    for descricao in contrato["itens"]:
        codigo = contrato["prefixo"] + "-" + str(numero).zfill(3)
        entrada = dataInicial + datetime.timedelta(days=random.randint(0, 140))
        conexao.execute(
            "INSERT INTO mercadorias (codigo, descricao, quantidade, paletes, galpaoId, contratoId, entradaEm) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (codigo, descricao, random.randint(20, 800), random.randint(2, 18),
             random.randint(1, len(galpoes)), indice + 1, entrada.isoformat()))
        numero += 1

# a capacidade de cada galpão é ajustada para a ocupação ficar parecida com a do exemplo
for indice in range(len(galpoes)):
    soma = conexao.execute("SELECT COALESCE(SUM(paletes), 0) FROM mercadorias WHERE galpaoId = ?",
                           (indice + 1,)).fetchone()[0]
    capacidade = round(soma / galpoes[indice]["ocupacao"])
    if capacidade < 1:
        capacidade = 100
    conexao.execute("UPDATE galpoes SET capacidade = ? WHERE id = ?", (capacidade, indice + 1))

conexao.commit()

for tabela in ["usuarios", "contratos", "galpoes", "mercadorias"]:
    quantidade = conexao.execute("SELECT COUNT(*) FROM " + tabela).fetchone()[0]
    print(tabela + ": " + str(quantidade) + " registros")
conexao.close()

print("")
print("Contas de teste (troque estas senhas antes de subir o sistema para o desafio):")
print("  administrador -> admin@cargoconnect.com.br / Admin#Cargo2026")
print("  operador      -> operador@cargoconnect.com.br / Oper#Cargo2026")
print("  cliente       -> cliente@valeverde.com.br / Cliente#Cargo2026")
