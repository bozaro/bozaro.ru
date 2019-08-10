pipeline {
    agent {
        dockerfile {
            filename 'Dockerfile.build'
        }
    }

    stages {
        stage('Cleanup') {
            steps {
                sh "git clean -fdx"
                sh 'git submodule update --init'
            }
        }

        stage('Build') {
            steps {
                sh '''#!/bin/sh -ex
rm -fR public/
./build.sh
tar -cvzf .build/content.tgz -C public/ .
'''
                archive '.build/content.tgz'
            }
        }

        stage('Publish (master)') {
            when {
                branch 'master'
            }
            steps {
                sshagent(credentials: ['web-deploy']) {
                    sh 'rsync -e "ssh -o StrictHostKeyChecking=no" -rlvzc --no-owner --no-group --delete-after public/ deploy@ivy.bozaro.ru:bozaro.ru/'
                }
            }
        }
    }
}
