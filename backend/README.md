# ServiceFlow — backend

Base Django do ServiceFlow, com a camada de modelos alinhada ao `docs/tech_spec`.

## Executar localmente

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py check
python manage.py test
```

O projeto usa SQLite por padrão para desenvolvimento. Para PostgreSQL, defina
`DATABASE_URL` no formato `postgresql://usuario:senha@host:5432/banco`.

## Modelos principais

- `apps.usuarios.Usuario`: autenticação, perfil e ativação do funcionário.
- `apps.clientes.Cliente` e `apps.equipamentos.Equipamento`: cadastro e vínculo do proprietário.
- `apps.ordens.OrdemServico`: recebimento, fluxo operacional, retornos, atividades, peças, anexos e entrega.
- `apps.orcamentos.Orcamento`: versões, itens e decisão vinculada à versão exata.
- `apps.financeiro.Pagamento`, `Estorno` e `Cancelamento`: valores, identificadores de operação e tratamento financeiro.
- `apps.auditoria.HistoricoAlteracao`: trilha de alterações sem exclusão em cascata.

As validações que dependem de agregações ou transições (por exemplo, autorização
para iniciar reparo, transição de situação e registro transacional do histórico)
devem ser expostas pelos serviços de negócio antes das rotas da API.
