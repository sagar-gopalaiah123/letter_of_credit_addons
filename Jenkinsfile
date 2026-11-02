pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Checking out Letter of Credit source code'
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Validate Project') {
            steps {
                sh '''
                    test -f letter_of_credit/__manifest__.py
                    test -f letter_of_credit/tests/test_letter_of_credit.py
                    test -f docker-compose.ci.yml
                    test -f config/odoo.conf
                '''
            }
        }

        stage('Start PostgreSQL') {
            steps {
                sh '''
                    docker compose -p letter-credit-ci \
                    -f docker-compose.ci.yml up -d db
                '''
            }
        }

        stage('Install Module and Run Tests') {
            steps {
                sh '''
                    docker compose -p letter-credit-ci \
                    -f docker-compose.ci.yml run --rm odoo \
                    odoo \
                    -d letter_credit_test \
                    -i letter_of_credit \
                    --test-enable \
                    --test-tags /letter_of_credit \
                    --stop-after-init
                '''
            }
        }
    }

    post {
        always {
            echo 'Cleaning Letter of Credit CI environment'

            sh '''
                docker compose -p letter-credit-ci \
                -f docker-compose.ci.yml down -v
            '''
        }

        success {
            echo 'LETTER OF CREDIT CI SUCCESS'
        }

        failure {
            echo 'LETTER OF CREDIT CI FAILED'
        }
    }
}
