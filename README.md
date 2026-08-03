# Github Activity

CLI em Python que consulta a API publica do GitHub e exibe a atividade recente de um usuario, como pushes, issues, estrelas e forks, em formato legivel.

## Funcionalidades

- Busca os eventos recentes de um usuario via API do GitHub.
- Apresenta eventos em formato legivel com data.
- Suporta PushEvent, IssuesEvent, WatchEvent e ForkEvent.
- Limita a exibicao aos 10 eventos mais recentes.
- Remove eventos duplicados.
- Trata erros da API, como usuario nao encontrado e rate limit.

## Como usar

```bash
python main.py <usuario_github>
```

Sem dependencias externas, apenas a biblioteca padrao do Python.

## Licenca

MIT
