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
        //
        // Ot seems that the issue described in
        //
        // https://github.com/nodejs/node/issues/51477
        //
        // 1) Is present in Debian 12
        // 2) actually matters if mode_modules (or ~/.npm ??) ist located on BeeGFS.
        //
        // So so no Jenkins tests for the client part - until Debian 13 or so
        //
        // stage('Setup NodeJS') {
        //     steps {
        //         sh '''
        //             cd client
        //             npm install --save-dev
        //         '''
        //     }
        // }
        // stage('Test Frontend') {
        //     steps {
        //         sh '''
        //             cd client
        //             npm run test:unit run
        //         '''
        //     }
        // }
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
