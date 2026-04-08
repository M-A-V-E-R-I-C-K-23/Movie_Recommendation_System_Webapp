pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Clean Up') {
            steps {
                sh '''
                echo "Killing any process listening on port 8501..."
                lsof -ti:8501 | xargs kill -9 || true
                '''
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                echo "Setting up Python virtual environment..."
                python3 -m venv venv
                source venv/bin/activate
                pip install --upgrade pip
                pip install -r requirements.txt
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                echo "Starting Streamlit..."
                source venv/bin/activate
                # JENKINS_NODE_COOKIE=dontKillMe prevents Jenkins from killing the background process
                JENKINS_NODE_COOKIE=dontKillMe nohup streamlit run webapp.py --server.port=8501 --server.address=0.0.0.0 > streamlit.log 2>&1 &
                '''
            }
        }
    }
}
