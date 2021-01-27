# Health Check script - Lambda Version

This script can be used to Check Health of servers and services not only on AWS, but anywhere where it can access via TCP.


### Features 
* ping check
* TCP port check
* http/https code status check (eg. 200)
* http/https return string check
* ICAP check if returned file is modified
* Output to console - set in config.yml
* Output to file - set in config.yml
* Output to syslog - set in config.yml

### Prerequisites
* AWS CLI 2 installed https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html and configured

```bash
aws configure
```

* You can test access issuing:
```bash
aws ec2 describe-instances
```

* Docker installed https://docs.docker.com/engine/install/

```bash
sudo yum update -y
sudo amazon-linux-extras install docker
sudo service docker start
sudo usermod -a -G docker ec2-user
docker info
```

* Clone repository

```bash
git clone --recursive https://github.com/k8-proxy/vmware-scripts.git
cd vmware-scripts/HealthCheck-Lambda
```

* Edit config

```bash
vi app/config.yml
```


### Create ECR Amazon Elastic Container Registry and get credentials for it

```bash
aws ecr create-repository --repository-name healthchecklambda --image-scanning-configuration scanOnPush=false
aws ecr get-login-password | docker login --username AWS --password-stdin 938576707481.dkr.ecr.us-east-1.amazonaws.com
```

### Create and push Dcoker Image with Helth Checks

```bash
docker build -t 938576707481.dkr.ecr.us-east-1.amazonaws.com/healthchecklambda:0.9 .
docker push 938576707481.dkr.ecr.us-east-1.amazonaws.com/healthchecklambda:0.9
```

### Create amd tets Lambda function using portal

* Use https://console.aws.amazon.com/lambda/
* Choose Container Image and uploaded image
* Choose Test - use defaults

### Create amd tets Lambda function using CLI (to_implement/check)
```
aws lambda create-function  --runtime to_implement/check -role to_implement/check --function-name HealthCheck2 --code ImageUri=938576707481.dkr.ecr.us-east-1.amazonaws.com/healthchecklambda:0.9 --package-type Image
```
