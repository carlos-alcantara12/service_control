# ServiceFlow UI

A interface fica disponível na raiz do Django quando o backend é executado:

```powershell
cd backend
python manage.py runserver
```

Depois, abra `http://localhost:8000/`. O frontend usa a sessão do Django e os
endpoints existentes em `/api/`; não há dados fictícios nem um segundo serviço
de autenticação.

## Estrutura de telas

Cada tela fica isolada em `static/screens/<tela>/` e possui seus três arquivos:

```text
static/screens/
├── login/
├── dashboard/
├── ordens/
├── clientes/
├── equipamentos/
├── orcamentos/
├── financeiro/
├── relatorios/
└── usuarios/
```

Cada URL é uma página Django independente. O `index.html` de uma tela já contém
seu próprio layout, referencia somente o `styles.css` e o `script.js` da mesma
pasta, e não é injetado por um router central. `shared/core.js` contém apenas
utilitários pequenos e transversais, como sessão, API, formatação e modais; a
renderização, os eventos e os formulários ficam no `script.js` da própria tela.
