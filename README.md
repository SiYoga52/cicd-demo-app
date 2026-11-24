
# 🚀 CI/CD Demo App (Python)

![CI](https://github.com/ThisIsMikeyS/cicd-demo-app/actions/workflows/python-app.yml/badge.svg)
![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen.svg)
![Lint](https://img.shields.io/badge/lint-passing-brightgreen.svg)
![Last Commit](https://img.shields.io/github/last-commit/ThisIsMikeyS/cicd-demo-app)
[![codecov](https://codecov.io/gh/ThisIsMikeyS/cicd-demo-app/branch/main/graph/badge.svg)](https://codecov.io/gh/ThisIsMikeyS/cicd-demo-app)


A minimal Python project to demonstrate continuous integration (CI) and code quality enforcement using GitHub Actions, `unittest`, `coverage.py`, and `flake8`.

---

## Локальный CI/CD: Jenkins, Docker, Ansible

Jenkins, Docker Engine и Ansible работают на одном компьютере. Образ собирается в локальном Docker Engine, Ansible подключается как `hosts: localhost` / `connection: local` и создаёт контейнер `student-app`. Вторая VM, SSH и Docker Registry не используются.

Fork: https://github.com/SiYoga52/cicd-demo-app

Параметры Jenkins Job `cicd-demo-pipeline` (тип Pipeline, в настройках Definition = **Pipeline script**, тот же текст, что в `Jenkinsfile`):

| Параметр | По умолчанию | Назначение |
| --- | --- | --- |
| `REPO_URL` | `https://github.com/SiYoga52/cicd-demo-app.git` | Откуда делать Checkout |
| `GIT_BRANCH` | `master` | Ветка |
| `RUN_TESTS` | `true` | Запускать тесты и coverage |
| `DEPLOY` | `false` | Разрешить локальный деплой |
| `APP_PORT` | `18080` | Порт на хосте, приложение слушает `127.0.0.1` |

При `DEPLOY=true` и `RUN_TESTS=false` стадия Validate завершает Pipeline с ошибкой до сборки образа и деплоя.

### Тесты и lint

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python3 -m unittest discover -s tests -v
coverage run -m unittest discover -s tests
coverage xml -o coverage.xml
flake8 src tests
```

HTTP-тесты поднимают сервер только внутри процесса `unittest` и останавливают его в `tearDownClass`.

### Docker

```bash
docker build -t student-app:manual .
docker run --rm --name student-app -p 127.0.0.1:18080:8080 student-app:manual
curl --fail http://127.0.0.1:18080/health
curl --fail "http://127.0.0.1:18080/add?a=2&b=3"
```

Внутри контейнера процесс слушает `0.0.0.0:8080`. Образ запускается от пользователя `appuser`, у него есть `HEALTHCHECK`.

Jenkins помечает образ тегом `student-app:BUILD_NUMBER-SHORT_SHA` и записывает SHA, ветку, номер сборки и имя образа в `build-info.txt`. Архив образа не сохраняется.

Остановить и удалить только учебный контейнер:

```bash
docker stop student-app
docker rm student-app
```

### Ansible

Playbook использует `community.docker` 4.x/5.x (`pull: never`). Для этой коллекции нужен ansible-core 2.17 или новее. В Ubuntu 24.04 пакет `ansible-core` — 2.16, поэтому интерпретатор ставится в `/opt/ansible-venv`, а `ansible-playbook` доступен как `/usr/local/bin/ansible-playbook`.

```bash
sudo apt install docker.io python3-venv python3-pip
sudo python3 -m venv /opt/ansible-venv
sudo /opt/ansible-venv/bin/pip install 'ansible-core>=2.17' docker
sudo /opt/ansible-venv/bin/ansible-galaxy collection install \
  'community.docker:>=4.0.0' -p /usr/share/ansible/collections
sudo ln -sfn /opt/ansible-venv/bin/ansible-playbook /usr/local/bin/ansible-playbook
sudo usermod -aG docker "$USER" jenkins
ansible-playbook --syntax-check ansible/deploy.yml
ansible-playbook ansible/deploy.yml \
  -e image=student-app:manual \
  -e app_port=18080
```

Повторный запуск с тем же образом и портом оставляет один контейнер `student-app` и не перезапускает его: `recreate` не включён, `restart: false`. Проверка идемпотентности — второй запуск Playbook, затем `docker ps` (один контейнер) и сравнение `StartedAt` у `docker inspect student-app` до и после. В выводе Ansible у задачи контейнера должно быть `changed=0` / `ok`.

Откат на предыдущий локальный тег: Jenkins перед деплоем пишет текущий образ в артефакт `previous-image.txt`.

```bash
ansible-playbook ansible/deploy.yml \
  -e image="$(cat previous-image.txt)" \
  -e app_port=18080
```

Образ из Registry не скачивается (`pull: never`). После старта Playbook сам запрашивает `http://127.0.0.1:APP_PORT/health`, пока ответ не станет HTTP 200 и JSON `{"status": "ok"}`.

Сервис после деплоя: http://127.0.0.1:18080/health и http://127.0.0.1:18080/add?a=2&b=3

### Почему здесь нет SSH

Ansible и Docker Engine находятся на той же машине, где Jenkins собрал образ. Playbook указывает `connection: local`, поэтому Ansible не открывает SSH-сессию: модуль `community.docker.docker_container` говорит с локальным сокетом Docker (`/var/run/docker.sock`) и запускает уже существующий локальный образ. Проверка `/health` тоже идёт на `127.0.0.1`.

### Ветка broken-tests

После рабочей ветки `master` в `broken-tests` намеренно сломан один unit-тест (`test_add` ожидает 0). При `RUN_TESTS=true` Pipeline останавливается на стадии Test, Build Image и Deploy не выполняются.

---

## ✨ Features

- ✅ Basic Python calculator module (`add`, `subtract`, `multiply`, `divide`)
- 🧪 Unit-tested with `unittest`
- 📊 Coverage reporting via `coverage.py`
- 🧼 Linting enforced using `flake8` for code quality
- 🔁 CI pipeline with GitHub Actions
- 🛠 Compatible with Visual Studio 2022 on Windows 11

---

## 📁 Project Structure

```
cicd-demo-app/
├── src/
│   ├── calculator.py            # Arithmetic functions
│   └── server.py                # HTTP wrapper, port 8080
├── tests/
│   ├── test_calculator.py
│   └── test_server.py           # HTTP tests, no permanent server
├── ansible/
│   └── deploy.yml               # localhost container deploy
├── Dockerfile
├── .dockerignore
├── Jenkinsfile                  # Declarative Pipeline
├── .github/workflows/python-app.yml
├── requirements.txt
└── README.md
```

---

## 🧪 Running the Tests Locally

```bash
# Run unit tests
python -m unittest discover -s tests

# Run tests with coverage
coverage run -m unittest discover -s tests
coverage report
```

---

## 🧼 Lint Check (flake8)

```bash
flake8 src tests
```

---

## ⚙️ CI/CD Pipeline (GitHub Actions)

This repo includes a GitHub Actions workflow that:

- Runs on `push` and `pull_request` to `main`
- Installs Python 3.10
- Installs dependencies from `requirements.txt`
- Runs `flake8` for code linting
- Runs `unittest` with coverage tracking
- Fails the build if linting or tests fail

Workflow location:

```
.github/workflows/python-app.yml
```

---

## 🚀 Getting Started (Development)

### Prerequisites

- Python 3.10+
- GitHub account
- (Optional) Visual Studio 2022 with Python development tools

### Clone and Run

```bash
git clone https://github.com/ThisIsMikeyS/cicd-demo-app.git
cd cicd-demo-app
python src/calculator.py
```

---

## 🧑‍💻 Author

**Michael Saunders**  
Freelance Software & Systems Developer | Technical Writer  
[LinkedIn](https://www.linkedin.com/in/michael-saunders-805785128/) · [GitHub](https://github.com/ThisIsMikeyS)

---

## 📚 License

This project is licensed under the MIT License – see the `LICENSE` file for details.