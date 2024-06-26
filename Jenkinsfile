pipeline {
    agent any
    stages {
        stage('Prepare Python venv') {
            steps {
                sh '''
                    python3 -m venv venv
                    . ./venv/bin/activate
                    pip install --upgrade pip setuptools
                    cd server
                    pip --verbose install '.[dev,tests]'
                '''
            }

        }
        stage('Python Testing') {
            steps {
                sh '''
                    . ./venv/bin/activate
                    export PYTHONPATH=$(pwd)/server/src:$(pwd)/server/tests
                    cd server
                    pytest --junitxml results.xml tests --cov=src/scimodom --cov-report xml
                '''
            }
        }
        stage('Setup NodeJS') {
            steps {
                sh '''
                    cd client
                    npm install --save-dev
                '''
            }
        }
        stage('Test Frontend') {
            steps {
                sh '''
                    cd client
                    npm run test:unit run
                '''
            }
        }
    }
    post {
        always {
            junit 'results.xml'
        }
        failure {
            emailext to: "${SCIMODOM_DEV_EMAILS}",
            subject: "jenkins build:${currentBuild.currentResult}: ${env.JOB_NAME}",
            body: "${currentBuild.currentResult}: Job ${env.JOB_NAME}\nMore Info can be found here: ${env.BUILD_URL}"
        }
    }
}
