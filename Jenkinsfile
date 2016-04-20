node ('linux') {
  stage 'Checkout'
  checkout scm
  sh 'git reset --hard'
  sh 'git clean -ffdx'
  sh 'git submodule update --init'

  stage 'Build'
  sh '''#!/bin/bash -ex
HUGO=0.15
mkdir -p .build
tar -xzvf .jenkins/distrib/hugo_${HUGO}_linux_amd64.tar.gz -C .build
.build/hugo_${HUGO}_linux_amd64/hugo_${HUGO}_linux_amd64 -t beg
tar -cvzf .build/content.tgz -C public/ .
'''
  archive '.build/content.tgz'

  if (env.BRANCH_NAME == 'master') {
    stage 'Publish'
    sshagent(credentials: ['0d1e35cd-a719-4ab9-afed-fb5d9c8ff9af']) {
      sh 'rsync -e "ssh -o StrictHostKeyChecking=no" -rlvz --delete-after public/ deploy@bozaro.ru:bozaro.ru/'
    }
  }
}
