# ServiceFlow

Plataforma web para gestão de ordens de serviço em assistências técnicas e empresas de manutenção. O ServiceFlow organiza o atendimento completo de um equipamento — do recebimento à entrega — em um único fluxo, com controle de responsabilidades, orçamento, autorização, execução, pagamento e histórico.

## Para que serve

O sistema foi criado para substituir controles espalhados em planilhas, mensagens e anotações. Cada atendimento recebe uma ordem de serviço única, que concentra:

- dados do cliente e do equipamento;
- defeito relatado e condições de entrada;
- técnico responsável, prioridade e prazo;
- diagnóstico, atividades, peças utilizadas e testes;
- orçamentos versionados e decisão do cliente;
- pagamentos, saldo pendente, estornos e cancelamentos;
- anexos, comprovantes, retornos e histórico de alterações.

O backend aplica as regras do negócio e impede operações críticas fora da sequência permitida — por exemplo, iniciar um reparo sem aprovação válida do orçamento ou entregar uma ordem com saldo pendente sem uma exceção autorizada.

## Aplicação no mercado

O produto atende principalmente:

- assistências técnicas de celulares, computadores, eletroeletrônicos e outros equipamentos;
- oficinas de manutenção e reparo;
- empresas que recebem equipamentos de clientes e precisam acompanhar serviços, prazos e pagamentos;
- operações que desejam sair de planilhas e centralizar o atendimento em uma ferramenta própria.

Na prática, o ServiceFlow ajuda a empresa a reduzir extravios de informação, evitar reparos sem autorização, dar visibilidade aos prazos, separar o status operacional do financeiro e preservar evidências para resolver dúvidas sobre danos, valores, alterações e entregas.

O modelo atual é adequado como MVP para uma assistência técnica. Ele também pode servir como base para uma solução comercial multiunidade ou SaaS, após a implementação de isolamento entre empresas, rotinas de backup, monitoramento, notificações e integrações externas conforme a estratégia do produto.

## Fluxo de atendimento

1. O atendente cadastra o cliente, o equipamento e abre a ordem de serviço.
2. O gerente atribui a ordem a um técnico.
3. O técnico registra o diagnóstico e prepara o orçamento.
4. O atendente registra a aprovação, recusa ou expiração da versão enviada.
5. O reparo só pode ser iniciado quando existe aprovação válida.
6. O técnico registra atividades, peças e testes.
7. O atendente registra o pagamento e a entrega do equipamento.
8. Se necessário, a empresa abre um retorno vinculado à ordem original, mantendo o histórico do atendimento.

## Módulos

| Módulo | Aplicação |
| --- | --- |
| Painel | Visão geral de ordens abertas, atrasadas, aguardando aprovação e prontas para entrega. |
| Clientes | Cadastro, pesquisa e consulta do histórico de atendimentos. |
| Equipamentos | Identificação do equipamento e vínculo com seu proprietário e ordens anteriores. |
| Ordens de serviço | Recebimento, atribuição, prazos, diagnóstico, execução, testes, anexos, retornos e entrega. |
| Orçamentos | Itens, valores, versões, validade e decisão do cliente. |
| Financeiro | Pagamentos, situação financeira, saldo pendente, estornos e cancelamentos. |
| Relatórios | Indicadores operacionais e financeiros para acompanhamento da gestão. |
| Usuários | Controle de acesso, perfis e ativação de funcionários. |
| Auditoria | Registro das alterações, responsáveis e dados relevantes da ordem. |

## Perfis de acesso

| Perfil | Responsabilidades principais |
| --- | --- |
| Gerente | Gerencia usuários, distribui ordens, consulta relatórios, autoriza exceções e estornos. |
| Atendente | Cadastra clientes, recebe equipamentos, registra decisões, pagamentos e entregas. |
| Técnico | Registra diagnóstico, orçamento, atividades, peças e testes nas ordens atribuídas. |

As permissões são verificadas no backend, além dos controles apresentados na interface.

## Destaques de controle

- Número de ordem único e imutável.
- Orçamentos preservados por versão, com aprovação vinculada à versão exata.
- Transições de status controladas por regras de negócio.
- Valores monetários calculados e validados no backend.
- Situação operacional independente da situação financeira.
- Estornos limitados ao valor efetivamente pago.
- Entrega condicionada à quitação, salvo exceção autorizada pelo gerente.
- Histórico de alterações preservado sem apagar o atendimento.
- Controle de acesso por perfil e, quando aplicável, por técnico responsável pela ordem.
- Paginação e filtros nas listagens da interface.

## Arquitetura e tecnologias

O projeto usa uma arquitetura web monolítica, com frontend e API servidos pelo mesmo projeto Django:

- **Backend:** Python, Django e Django REST Framework.
- **Frontend:** HTML, CSS e JavaScript modular por tela.
- **Banco de dados:** SQLite por padrão no desenvolvimento e PostgreSQL via `DATABASE_URL`.
- **Autenticação:** sessão do Django, com proteção CSRF.
- **Arquivos:** anexos vinculados às ordens e protegidos por autenticação.
- **Testes:** suíte de testes do Django para modelos, serializers e serviços.

### Estrutura principal

```text
.
├── backend/
│   ├── apps/
│   │   ├── auditoria/
│   │   ├── clientes/
│   │   ├── equipamentos/
│   │   ├── financeiro/
│   │   ├── ordens/
│   │   ├── orcamentos/
│   │   ├── relatorios/
│   │   └── usuarios/
│   ├── config/
│   ├── tests/
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   └── static/screens/
└── docs/
    └── tech_spec
```

As operações críticas ficam em serviços transacionais no backend. Isso concentra as regras em um único lugar e mantém a API e a interface alinhadas ao fluxo operacional.

## Como executar localmente

### Pré-requisitos

- Python 3.11 ou superior recomendado;
- `pip`;
- PostgreSQL opcional — o desenvolvimento pode usar SQLite.

### Instalação

No PowerShell:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
```

Crie o primeiro usuário gerente:

```powershell
python manage.py createsuperuser
```

Inicie o servidor:

```powershell
python manage.py runserver
```

Depois, acesse [http://localhost:8000/](http://localhost:8000/). A aplicação redireciona para a tela de login. O painel administrativo fica disponível em `/admin/`.

### Variáveis de ambiente

| Variável | Finalidade |
| --- | --- |
| `DJANGO_SECRET_KEY` | Chave secreta da aplicação. Deve ser definida em ambientes reais. |
| `DJANGO_DEBUG` | Define o modo de debug; use `0` em produção. |
| `DJANGO_ALLOWED_HOSTS` | Hosts permitidos, separados por vírgula. |
| `DATABASE_URL` | Conexão PostgreSQL no formato `postgresql://usuario:senha@host:5432/banco`. |

Exemplo:

```powershell
$env:DJANGO_DEBUG = "0"
$env:DJANGO_ALLOWED_HOSTS = "app.exemplo.com"
$env:DJANGO_SECRET_KEY = "substitua-por-uma-chave-segura"
$env:DATABASE_URL = "postgresql://usuario:senha@localhost:5432/serviceflow"
```

## API principal

A API fica sob `/api/` e usa autenticação por sessão. Alguns endpoints disponíveis são:

| Método | Rota | Finalidade |
| --- | --- | --- |
| `GET`, `POST` | `/api/clientes/` | Listar e cadastrar clientes. |
| `GET`, `POST` | `/api/equipamentos/` | Listar e cadastrar equipamentos. |
| `GET`, `POST` | `/api/ordens/` | Consultar e abrir ordens de serviço. |
| `POST` | `/api/ordens/{id}/diagnostico/` | Registrar diagnóstico. |
| `POST` | `/api/ordens/{id}/iniciar-reparo/` | Iniciar reparo após validação das regras. |
| `POST` | `/api/ordens/{id}/orcamentos/` | Criar uma versão de orçamento. |
| `POST` | `/api/orcamentos/{id}/decisao/` | Registrar aprovação ou recusa. |
| `POST` | `/api/ordens/{id}/pagamentos/` | Registrar pagamento. |
| `POST` | `/api/ordens/{id}/entrega/` | Registrar entrega e recebedor. |
| `GET` | `/api/relatorios/operacional/` | Consultar indicadores operacionais. |
| `GET` | `/api/relatorios/financeiro/` | Consultar indicadores financeiros. |

As demais rotas estão organizadas nos arquivos `urls.py` de cada aplicação.

## Testes

Execute a suíte do backend com:

```powershell
cd backend
python manage.py test
```

Os testes cobrem, entre outros cenários, o fluxo até a entrega, bloqueio de reparo sem aprovação, permissões por perfil, estornos, entrega com saldo pendente, cancelamento com preservação de histórico e validações de integridade dos modelos.

## Escopo atual e próximos passos

O MVP já contempla o núcleo interno da operação. A comunicação com o cliente, no escopo atual, continua sendo feita pelos canais já utilizados pela empresa; o sistema registra a decisão e suas evidências.

Para uma implantação comercial em escala, recomenda-se complementar o produto com:

- isolamento de dados por empresa ou unidade;
- backups automatizados e testes de restauração;
- HTTPS, servidor de aplicação e proxy reverso;
- monitoramento, logs e alertas;
- notificações por e-mail ou WhatsApp;
- portal do cliente e integrações de pagamento;
- estoque de peças, emissão fiscal e integrações contábeis, se necessários.

## Documentação complementar

- [Especificação técnica](docs/tech_spec)
- [Documentação do backend](backend/README.md)
- [Documentação do frontend](frontend/README.md)
