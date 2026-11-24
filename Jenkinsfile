pipeline {
    agent any

    options {
        skipDefaultCheckout()
        disableConcurrentBuilds()
    }

    parameters {
        string(
            name: 'REPO_URL',
            defaultValue: 'https://github.com/SiYoga52/cicd-demo-app.git',
            description: 'HTTPS-ссылка на свой Fork'
        )
        string(
            name: 'GIT_BRANCH',
            defaultValue: 'master',
            description: 'Ветка для Checkout'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Запускать unit-тесты и coverage'
        )
        booleanParam(
            name: 'DEPLOY',
            defaultValue: false,
            description: 'Разрешить локальный деплой через Ansible'
        )
        string(
            name: 'APP_PORT',
            defaultValue: '18080',
            description: 'Порт хоста для приложения (127.0.0.1:APP_PORT)'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                script {
                    if (!params.REPO_URL?.trim() || !params.GIT_BRANCH?.trim()) {
                        error('REPO_URL и GIT_BRANCH не должны быть пустыми')
                    }
                }
                deleteDir()
                git branch: "${params.GIT_BRANCH}", url: "${params.REPO_URL}"
                sh '''
                    echo "BUILD_NUMBER=${BUILD_NUMBER}"
                    echo "BRANCH=${GIT_BRANCH}"
                    echo "SHA=$(git rev-parse HEAD)"
                '''
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    set -eu
                    echo "Проверка параметров и состава репозитория"

                    if [ -z "${REPO_URL}" ] || [ -z "${GIT_BRANCH}" ]; then
                        echo "Ошибка: REPO_URL и GIT_BRANCH не должны быть пустыми."
                        exit 1
                    fi

                    if ! printf '%s' "${APP_PORT}" | grep -Eq '^[0-9]+$'; then
                        echo "Ошибка: APP_PORT должен быть целым числом от 1024 до 65535. Получено: ${APP_PORT}"
                        exit 1
                    fi
                    port=$((10#${APP_PORT}))
                    if [ "${port}" -lt 1024 ] || [ "${port}" -gt 65535 ]; then
                        echo "Ошибка: APP_PORT должен быть целым числом от 1024 до 65535. Получено: ${APP_PORT}"
                        exit 1
                    fi

                    if [ "${DEPLOY}" = "true" ] && [ "${RUN_TESTS}" != "true" ]; then
                        echo "Ошибка: деплой запрещён без тестов (DEPLOY=true, RUN_TESTS=false)."
                        echo "Сборка остановлена до Build Image и Deploy. Контейнер не изменяется."
                        exit 1
                    fi

                    missing=0
                    for item in \
                        README.md \
                        requirements.txt \
                        Dockerfile \
                        .dockerignore \
                        Jenkinsfile \
                        ansible/deploy.yml \
                        src/calculator.py \
                        src/server.py \
                        tests/test_calculator.py \
                        tests/test_server.py
                    do
                        if [ ! -e "${item}" ]; then
                            echo "Отсутствует обязательный файл: ${item}"
                            missing=1
                        else
                            echo "Найден: ${item}"
                        fi
                    done
                    if [ "${missing}" -ne 0 ]; then
                        exit 1
                    fi
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '''
                    set -eu
                    python3 -m venv .venv
                    . .venv/bin/activate
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    flake8 src tests
                '''
            }
        }

        stage('Test') {
            when {
                expression { return params.RUN_TESTS }
            }
            steps {
                sh '''
                    set -eu
                    . .venv/bin/activate
                    coverage run -m unittest discover -s tests -v
                    coverage xml -o coverage.xml
                    coverage report
                '''
            }
        }

        stage('Build Image') {
            steps {
                sh '''
                    set -eu
                    SHA=$(git rev-parse HEAD)
                    SHORT_SHA=$(git rev-parse --short=7 HEAD)
                    IMAGE="student-app:${BUILD_NUMBER}-${SHORT_SHA}"
                    docker build -t "${IMAGE}" .
                    cat > build-info.txt <<EOF
SHA=${SHA}
SHORT_SHA=${SHORT_SHA}
BRANCH=${GIT_BRANCH}
BUILD_NUMBER=${BUILD_NUMBER}
IMAGE=${IMAGE}
EOF
                    echo "Собран локальный образ ${IMAGE}"
                    cat build-info.txt
                '''
            }
        }

        stage('Deploy') {
            when {
                expression { return params.DEPLOY }
            }
            steps {
                sh '''
                    set -eu
                    IMAGE=$(awk -F= '/^IMAGE=/{print substr($0, 7)}' build-info.txt)
                    if [ -z "${IMAGE}" ]; then
                        echo "Ошибка: в build-info.txt нет имени образа."
                        exit 1
                    fi
                    if docker inspect student-app >/dev/null 2>&1; then
                        docker inspect --format '{{.Config.Image}}' student-app > previous-image.txt
                        echo "Предыдущий локальный тег записан в previous-image.txt:"
                        cat previous-image.txt
                    else
                        echo "Контейнер student-app ещё не существует. Откатывать нечего."
                        echo > previous-image.txt
                    fi
                    ansible-playbook ansible/deploy.yml \
                        -e "image=${IMAGE}" \
                        -e "app_port=${APP_PORT}"
                '''
            }
        }

        stage('Verify') {
            when {
                expression { return params.DEPLOY }
            }
            steps {
                sh '''
                    set -eu
                    echo "Проверка http://127.0.0.1:${APP_PORT}/health"
                    curl --noproxy '*' --fail --silent --show-error \
                        "http://127.0.0.1:${APP_PORT}/health"
                    echo
                '''
            }
        }
    }

    post {
        always {
            echo "Итоговый статус Pipeline: ${currentBuild.currentResult}"
            archiveArtifacts(
                artifacts: 'build-info.txt,coverage.xml,previous-image.txt',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }
    }
}
