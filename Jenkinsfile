pipeline {
    agent any
    stages {
        stage('Prepare Python venv') {
            steps {
                sh '''
                    [ -d venv ] || uv venv --python 3.11 venv
                    . ./venv/bin/activate
                    cd server
                    uv pip install -e . --group dev
                '''
            }
        }
        stage('Validate OpenAPI specs') {
            steps {
                sh '''
                    . ./venv/bin/activate
                    cd server
                    python docs/source/include_swagger_api_spec.py
                    openapi-spec-validator docs/source/openapi/_include/*.yaml
                '''
            }
        }
        stage('Check API version') {
            steps {
                sh '''
                    . ./venv/bin/activate

                    SERVER_VERSION=$(grep -oP 'API_VERSION = "\\K[^"]+' server/src/scimodom/services/url.py)
                    CLIENT_VERSION=$(grep -oP "API_VERSION = '\\K[^']+" client/src/services/API.ts)
                    echo "server=$SERVER_VERSION  client=$CLIENT_VERSION"
                    if [ -z "$SERVER_VERSION" ] || [ -z "$CLIENT_VERSION" ]; then
                        echo "Could not extract API_VERSION"
                        exit 1
                    fi
                    if [ "$SERVER_VERSION" != "$CLIENT_VERSION" ]; then
                        echo "API_VERSION mismatch"
                        exit 1
                    fi
                '''
            }
        }
        stage('Setup bedtools') {
            steps {
                sh '''
                    if [ ! -f bin/bedtools ]
                    then
                        wget -q https://github.com/arq5x/bedtools2/releases/download/v2.31.0/bedtools.static
                        mkdir -p bin
                        mv bedtools.static bin/bedtools
                        chmod 755 bin/bedtools
                    fi
                '''
            }
        }
        stage('Run server tests') {
            steps {
                sh '''
                    export PATH="$(pwd)/bin:$PATH"
                    . ./venv/bin/activate
                    export PYTHONPATH=$(pwd)/server/src:$(pwd)/server/tests
                    cd server
                    pytest --junitxml results.xml -m "not cifail" tests --cov=src/scimodom --cov-report xml
                '''
            }
        }
        stage('Setup NodeJS') {
            steps {
                sh '''
                    cd client
                    npm ci
                '''
            }
        }
        stage('Run client tests') {
            steps {
                sh '''
                    cd client
                    npm run test:unit:ci
                '''
            }
        }
        stage('Type check client') {
            steps {
                sh '''
                    cd client
                    npm run type-check
                '''
            }
        }
        // needs the merged specs from 'Validate OpenAPI specs'
        stage('Run API contract (client) tests') {
            steps {
                sh '''
                    cd client
                    npm run test:openapi
                '''
            }
        }
    }
    post {
        always {
            junit 'server/results.xml'
        }
        failure {
            emailext to: "${SCIMODOM_DEV_EMAILS}",
            subject: "jenkins build:${currentBuild.currentResult}: ${env.JOB_NAME}",
            body: "${currentBuild.currentResult}: Job ${env.JOB_NAME}\nMore Info can be found here: ${env.BUILD_URL}"
        }
    }
}
