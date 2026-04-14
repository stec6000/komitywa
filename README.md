## Automatyczny deploy po merge do GitHub

Repo ma teraz workflow `/.github/workflows/deploy.yml`, który odpala deploy po każdym `push` na `main` oraz pozwala uruchomić go ręcznie przez `workflow_dispatch`.

### Jak to działa

1. Merge do `main` uruchamia GitHub Actions.
2. Workflow łączy się po SSH z serwerem produkcyjnym.
3. Na serwerze wykonywany jest `deploy.sh`.
4. Skrypt robi `git pull --ff-only origin main`, `pip install -r requirements.txt`, `migrate`, `collectstatic` i restart Passenger.

### Konfiguracja GitHub

Dodaj w repozytorium albo w environment `production`:

Variables:
- `DEPLOY_HOST` - host SSH serwera, np. `s84.mydevil.net`
- `DEPLOY_USER` - użytkownik SSH na serwerze
- `DEPLOY_PATH` - ścieżka do katalogu projektu na serwerze
- `DEPLOY_PORT` - opcjonalnie port SSH, jeśli nie jest to `22`

Secrets:
- `DEPLOY_SSH_KEY` - prywatny klucz SSH, którego publiczna część jest dodana do `~/.ssh/authorized_keys` na serwerze
- `DEPLOY_KNOWN_HOSTS` - wynik `ssh-keyscan -H <DEPLOY_HOST>` zapisany jako sekret, żeby workflow weryfikował host key

### Minimalny setup po stronie serwera

- Repozytorium na serwerze musi być sklonowane i ustawione na branch `main`
- Konto SSH musi mieć dostęp do `git pull origin main`
- Na serwerze musi istnieć virtualenv `~/.virtualenvs/komitywa`
- `deploy.sh` musi być uruchamialny i leżeć w katalogu projektu

### Ważne

Automatyczny deploy odpala się po merge do `main`, nie po każdym pushu na gałęzie robocze.
