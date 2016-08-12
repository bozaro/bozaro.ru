node ('linux') {
  stage 'Checkout'
  checkout scm
  sh 'git reset --hard'
  sh 'git clean -ffdx'
  sh 'git submodule update --init'

  stage 'Build'
  sh '''#!/bin/bash -ex
rm -fR public/
./build.sh
tar -cvzf .build/content.tgz -C public/ .
'''
  archive '.build/content.tgz'

  if (env.BRANCH_NAME == 'master') {
    stage 'Publish'
    sshagent(credentials: ['0d1e35cd-a719-4ab9-afed-fb5d9c8ff9af']) {
      sh 'rsync -e "ssh -o StrictHostKeyChecking=no" -rlvzc --delete-after public/ deploy@bozaro.ru:bozaro.ru/'
    }
  }
}
