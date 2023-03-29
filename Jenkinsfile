pipeline {
    agent {
        dockerfile {
            filename "Dockerfile"
            dir "jenkins"
        }
    }

    stages {
        stage("Cleanup") {
            steps {
                sh "git clean -fdx"
                sh "git submodule update --init"
                sh "git lfs pull"
            }
        }

        stage("Build") {
            steps {
                sh """#!/bin/sh -ex
rm -fR public/
./build.sh
tar -cvzf .build/content.tgz -C public/ .
"""
                archive ".build/content.tgz"
            }
        }

        stage("Publish (master)") {
            when {
                branch "master"
            }
            steps {
                withCredentials([sshUserPrivateKey(credentialsId: 'web-deploy', keyFileVariable: 'SSH_KEY')]) {
                    sh 'rsync -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=no" -rlvzc --no-owner --no-group --delete-after public/ deploy@ivy.bozaro.ru:bozaro.ru/'
                }
            }
        }
    }
}
