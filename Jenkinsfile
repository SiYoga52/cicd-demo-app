pipeline {
    agent any

    parameters {
        string(
            name: 'REPO_URL',
            defaultValue: 'https://github.com/SiYoga52/cicd-demo-app.git',
            description: 'HTTPS-ссылка на свой Fork'
        )
        string(
            name: 'GIT_BRANCH',
            defaultValue: 'master',
            description: 'Ветка, которую нужно собрать'
        )
        booleanParam(
            name: 'RUN_TESTS',
            defaultValue: true,
            description: 'Выполнять unit-тесты'
        )
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                git branch: "${params.GIT_BRANCH}", url: "${params.REPO_URL}"
                sh '''
                    echo "Branch: ${GIT_BRANCH}"
                    echo "SHA: $(git rev-parse HEAD)"
                '''
            }
        }

        stage('Validate') {
            steps {
                sh '''
                    missing=0
                    for item in README.md requirements.txt src tests; do
                        if [ ! -e "$item" ]; then
                            echo "Отсутствует обязательный файл или каталог: $item"
                            missing=1
                        else
                            echo "Найден: $item"
                        fi
                    done
                    if [ "$missing" -ne 0 ]; then
                        exit 1
                    fi
                '''
            }
        }

        stage('Test') {
            when {
                expression { return params.RUN_TESTS }
            }
            steps {
                sh 'python3 -m unittest discover -s tests -v'
            }
        }

        stage('Build') {
            steps {
                sh '''
                    SHA=$(git rev-parse HEAD)
                    printf 'BUILD_NUMBER=%s\nGIT_COMMIT=%s\n' "$BUILD_NUMBER" "$SHA" > build-info.txt
                    tar -czf app.tar.gz --exclude=app.tar.gz --exclude=.git .
                    echo "Создан архив app.tar.gz"
                    tar -tzf app.tar.gz | grep build-info.txt
                '''
            }
        }

        stage('Archive') {
            steps {
                archiveArtifacts artifacts: 'app.tar.gz', fingerprint: true
            }
        }
    }

    post {
        success {
            echo 'Сборка завершилась успешно'
        }
        failure {
            echo 'Сборка завершилась с ошибкой'
        }
    }
}
