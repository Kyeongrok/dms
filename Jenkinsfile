#!/usr/bin/env groovy

def notifySlack(String buildStatus = 'passed') {
    // Build status of null means success.
    buildStatus = buildStatus ?: 'passed'
    def color = (buildStatus == 'passed') ? 'good' : 'danger'
    def msg = "Build <${env.BUILD_URL}|#${env.BUILD_NUMBER}> ${buildStatus}: ${env.JOB_NAME} (<${env.REPO_URL}|${env.COMMIT_ID}>) by ${env.AUTHOR_NAME}"
    slackSend(color: color, message: msg, channel: '#external-volvo')
}

def testIngestion(String sourceArg = "mount/input", String sourcePath = "${pwd()}/mount/input", String targetPath = "${pwd()}/mount/output") {
    try {
        sh "mkdir -p ${sourcePath} ${targetPath}"
        withEnv(['SIZE_MB=128', 'NUM_DRIVES=4', 'NUM_FILES=3']) {
            sh "./samples/gen-drive-data.sh ${sourcePath}"
        }
        sh 'dms_utils -c config.ini clean_all'
        sh "dms_utils -c config.ini cluster_create --cluster-id test-cluster-1 --mount-prefix ${targetPath}"
        sh "dms_utils -c config.ini reader_create --host=jenkins --device=/dev/md127 --mount=/dms/dev/md127 --port=U1_Slot1 --reader-id=jenkins-slot1"
        sh 'sleep 5'
        sh "ingest -c config.ini -m ${sourceArg} -r jenkins-slot1"
        sh "dms_utils -c config.ini ingest_verify ${sourcePath}"
        // Validate reingestion
        sh "ingest -c config.ini -m ${sourceArg}"
        sh "dms_utils -c config.ini ingest_verify ${sourcePath}"
        sh "tree ${sourcePath} ${targetPath}"
    } finally {
        dir(sourcePath){
            deleteDir()
        }
        dir(targetPath){
            deleteDir()
        }
        sh 'dms_utils -c config.ini clean_all'
    }
}

def testSensorIngestion(String sourceArg = "mount/input", String sourcePath = "${pwd()}/mount/input", String targetPath = "${pwd()}/mount/output") {
    try {
        sh "mkdir -p ${sourcePath} ${targetPath}"
        withEnv(['SIZE_MB=1', 'NUM_DRIVES=20', 'NUM_FILES=20']) {
            sh "./samples/gen-drive-data.sh ${sourcePath}"
        }
        sh 'dms_utils -c config.ini clean_all'
        sh "dms_utils -c config.ini cluster_create --cluster-id test-cluster-1 --mount-prefix ${targetPath}"
        sh "dms_utils -c config.ini reader_create --host=jenkins --device=/dev/md127 --mount=/dms/dev/md127 --port=U1_Slot1 --reader-id=jenkins-slot1"
        sh "dms_utils -c config.ini reader_create --host=jenkins --device=/dev/md127 --mount=/dms/dev/md127 --port=U1_Slot2 --reader-id=jenkins-slot2"
        sh "dms_utils -c config.ini reader_create --host=jenkins --device=/dev/md127 --mount=/dms/dev/md127 --port=U1_Slot3 --reader-id=jenkins-slot3"
        sh "dms_utils -c config.ini reader_create --host=jenkins --device=/dev/md127 --mount=/dms/dev/md127 --port=U1_Slot4 --reader-id=jenkins-slot4"
        sh 'sleep 5'
        sh "ingest -c config.ini -m ${sourceArg}"

        // Create sensor documents
        sh 'python3 ./samples/create-sensor-data.py -c config.ini --sensor-type FLC'
        // Enable sensor mode
        sh 'sed -i \'s/enabled = False/enabled = True/g\' config.ini'
        // Lower the min space required
        sh 'sed -i \'s/min_disk_space = 107374182400/min_disk_space = 104857600/g\' config.ini'
        // Egest data
        parallel(
          slot1: {
            sh "ingest -c config.ini -m ${sourceArg} -r jenkins-slot1"
          },
          slot2: {
            sh "ingest -c config.ini -m ${sourceArg} -r jenkins-slot2"
          },
          slot3: {
            sh "ingest -c config.ini -m ${sourceArg} -r jenkins-slot3"
          },
          slot4: {
            sh "ingest -c config.ini -m ${sourceArg} -r jenkins-slot4"
          }
        )

        // Verify all sensors have been copied
        sh "tree ${sourcePath}/egest"
        sh "test `find ${sourcePath}/egest -type f | wc -l` -eq 400"

        // Try to re-egest data
        sh "ingest -c config.ini -m ${sourceArg}"


        // Ingest data
        sh "mkdir ${sourcePath}/ingest"
        sh "python3 ./samples/request-sensor-versions.py -c config.ini --ingest-dir ${sourcePath}/ingest"
        sh "tree ${sourcePath}/ingest"
        sh "ingest -c config.ini -m ${sourceArg}"
        // Verify ingest files have been deleted after ingestion
        sh "test `ls -1A ${sourcePath}/ingest | wc -l` -eq 0"
        // Try to re-ingest data
        sh "ingest -c config.ini -m ${sourceArg}"
        sh "tree ${targetPath}"

    } finally {
        dir(sourcePath){
            deleteDir()
        }
        dir(targetPath){
            deleteDir()
        }
        sh 'dms_utils -c config.ini clean_all'
    }
}

def runTests() {
    stage('Checkout') {
        checkout scm
        env.COMMIT_ID = sh(returnStdout: true, script: 'git rev-parse --short HEAD').trim()
        env.AUTHOR_NAME = sh(returnStdout: true, script: 'git show -s --pretty=%an HEAD').trim()
        env.REPO_URL = sh(returnStdout: true, script: 'git config --get remote.origin.url').trim()
        sh 'printenv'
    }

    stage('Setup Docker containers')

    def dmsImage = docker.build("volvo-dmsclient:${env.BUILD_ID}", "dmsclient")
    def ingestImage = docker.build("volvo-ingest:${env.BUILD_ID}", "ingest/tests")


    docker.image('docker.elastic.co/elasticsearch/elasticsearch:5.6.8').withRun('-p 9200:9200 -e "http.host=0.0.0.0" -e "transport.host=127.0.0.1"') { c ->
        sh 'sleep 20'
        dmsImage.inside("--link ${c.id}:elasticsearch") {
            stage('Setup DMSClient Environment')

            sh 'curl -X PUT -u elastic:changeme http://elasticsearch:9200/_cluster/settings -d \'{\"transient\": {\"script.max_compilations_per_minute\": 60}}\''
            sh 'python3 --version'
            sh 'pip3 --version'
            sh 'sudo pip3 install -r dmsclient/requirements.txt -r dmsclient/test-requirements.txt'

            parallel linter: {
                stage('Code linter DMSClient') {
                    sh 'flake8 dmsclient'
                }
            }, tests: {
                stage('Test DMSClient') {
                    sh 'sed -i \'s/127.0.0.1/elasticsearch/g\' dmsclient/tests/test.conf'
                    withEnv(["TEST_CONFIG_FILE=${WORKSPACE}/dmsclient/tests/test.conf"]) {
                        sh 'cat $TEST_CONFIG_FILE'
                        sh 'nosetests -v dmsclient/tests --with-coverage --cover-tests --cover-package=dmsclient'
                    }
                }
            }
        }

        stage('Setup Ingestion Environment')

        docker.image('nabeken/docker-volume-container-rsync').withRun('-p 873 -e OWNER=1000 -e GROUP=1000') { cRsync ->
            ingestImage.inside("--link ${c.id}:elasticsearch --link ${cRsync.id}:rsync --volumes-from ${cRsync.id}") {

                sh 'uname -a'
                sh 'python3 --version'
                sh 'pip3 --version'
                sh 'cd dmsclient && sudo python3 setup.py install'
                sh 'cd ingest && sudo python3 setup.py install'
                sh 'cp ingest/config.example.ini config.ini'
                sh 'sed -i \'s/check_mountpoints = True/check_mountpoints = False/g\' config.ini'

                stage('Test Local Ingestion')
                testIngestion()
                stage('Test Remote Ingestion')
                testIngestion('rsync://rsync:873/volume', '/docker', "${pwd()}/mount/output")
                stage('Test FLC Ingestion/Egestion')
                testSensorIngestion()
            }
        }

    }
}

node {
    try {
        lock('volvo') {
            timeout(time: 10, unit: 'MINUTES') {
                runTests()
            }
        }
    } catch (e) {
        currentBuild.result = 'failed'
        throw e
    } finally {
        notifySlack(currentBuild.result)
    }
}
