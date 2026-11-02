# CargoConnect Logística (Grupo 6)

Sistema web de gestão de galpões, inventário de mercadorias de terceiros e contratos corporativos.
Feito com **Python + Flask** e banco **SQLite** (um arquivo, sem instalar servidor de banco).

## Como rodar

```powershell
cd SiteSegurancaInformacao
pip install -r requirements.txt
python popular.py
python app.py
```

Abra http://127.0.0.1:5000 no navegador.

- `popular.py` cria o banco (`cargoconnect.db`) e insere os dados de exemplo. Só precisa rodar uma vez.
  Para recomeçar do zero, apague o arquivo `cargoconnect.db` e rode de novo.
- **Não use `--debug` / `debug=True`** no sistema que vai para o desafio: o modo debug permite executar código no servidor.

## Contas de teste

| Perfil        | E-mail                          | Senha               |
|---------------|---------------------------------|---------------------|
| Administrador | admin@cargoconnect.com.br       | Admin#Cargo2026     |
| Operador      | operador@cargoconnect.com.br    | Oper#Cargo2026      |
| Cliente       | cliente@valeverde.com.br        | Cliente#Cargo2026   |

Os outros 47 usuários têm senhas aleatórias (ninguém sabe). Para ter outro login, crie um usuário pelo painel de administração.
**Troque as senhas das contas de teste antes de subir o sistema para o desafio.**

## Estrutura

| Arquivo / pasta          | Para que serve |
|--------------------------|----------------|
| `app.py`                 | Rotas do site, login/logout e controle de permissões |
| `banco.py`               | Conexão com o banco e criação das tabelas |
| `popular.py`             | Insere os 50 usuários e os demais dados fictícios |
| `templates/`             | Páginas HTML (`base.html` tem o header e o footer de todas) |
| `static/style.css`       | CSS de todas as páginas |
| `uploads/`               | Comprovantes enviados (não vai para o GitHub) |

## Permissões (RBAC)

| Área                              | Administrador | Operador | Cliente |
|-----------------------------------|:-------------:|:--------:|:-------:|
| Início                            | sim | sim | sim (resumo do próprio estoque) |
| Galpões                           | sim | sim | não |
| Inventário (consulta e busca)     | todos os itens | todos os itens | só os da própria empresa |
| Cadastrar mercadoria + comprovante| sim | sim | não |
| Contratos                         | sim | não | não |
| Usuários (criar e excluir)        | sim | não | não |

O perfil fica na coluna `perfil` da tabela `usuarios`. Em `app.py`, `@loginObrigatorio` exige estar logado e
`@perfilObrigatorio(...)` exige um dos perfis listados; quem não tem permissão recebe a página 403.

## Banco de dados

- `usuarios`: nome, e-mail, `senhaHash` (a senha nunca é guardada em texto), perfil, empresa (se for cliente)
- `contratos`: empresa, CNPJ, responsável, contato, vigência e valor mensal (as empresas dos clientes)
- `galpoes`: nome, cidade, endereço e capacidade em paletes
- `mercadorias`: código, descrição, quantidade, paletes, galpão, empresa dona, comprovante e data de entrada

Dados populados: 50 usuários (2 administradores, 8 operadores, 40 clientes), 8 contratos, 6 galpões e 64 mercadorias.
Todos os dados são fictícios.

## O que ainda falta (próximas semanas)

- Subir em VM ou Docker (semana 3)
- Logs ativos de acesso e erro do servidor web e do banco (semana 3)
- Cadastrar a conta do professor (semana 3)
- Hardening: limite de tentativas de login, token CSRF, cabeçalhos de segurança, validação do conteúdo dos uploads (semana 3)
- Falha "proposital" exigida pelo trabalho (decisão do grupo)
