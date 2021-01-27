#!/bin/bash
pushd $( dirname $0 )
if [ -f ./env ] ; then
source ./env
fi

# install wizard to setup network (for OVA)
if [ -f ./install-wizard.sh ] ; then
source ./install-wizard.sh
fi

# install k3s
curl -sfL https://get.k3s.io | sh -
mkdir ~/.kube && sudo install -T /etc/rancher/k3s/k3s.yaml ~/.kube/config -m 600 -o $USER

# install kubectl and helm
curl -LO "https://storage.googleapis.com/kubernetes-release/release/$(curl -s https://storage.googleapis.com/kubernetes-release/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x ./kubectl
sudo mv ./kubectl /usr/local/bin/kubectl
echo "Done installing kubectl"

curl -sfL https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
echo "Done installing helm"

# get source code, we clone in in home dir so we can easilly update in place
cd ~
git clone https://github.com/k8-proxy/icap-infrastructure.git -b k8-develop && cd icap-infrastructure

# Create namespaces
kubectl create ns icap-adaptation
kubectl create ns management-ui
kubectl create ns icap-ncfs

kubectl create -n icap-adaptation secret docker-registry regcred \
	--docker-server=https://index.docker.io/v1/ \
	--docker-username=$DOCKER_USERNAME \
	--docker-password=$DOCKER_PASSWORD \
	--docker-email=$DOCKER_EMAIL

# Setup rabbitMQ
pushd rabbitmq && helm upgrade rabbitmq --install . --namespace icap-adaptation && popd

# Setup icap-server
cat >> openssl.cnf <<EOF
[ req ]
prompt = no
distinguished_name = req_distinguished_name

[ req_distinguished_name ]
C = GB
ST = London
L = London
O = Glasswall
OU = IT
CN = icap-server
emailAddress = admin@glasswall.com
EOF

openssl req -newkey rsa:2048 -config openssl.cnf -nodes -keyout  /tmp/tls.key -x509 -days 365 -out /tmp/certificate.crt
kubectl create secret tls icap-service-tls-config --namespace icap-adaptation --key /tmp/tls.key --cert /tmp/certificate.crt

pushd adaptation
kubectl create -n icap-adaptation secret generic policyupdateservicesecret --from-literal=username=policy-management --from-literal=password='long-password'
kubectl create -n icap-adaptation secret generic transactionqueryservicesecret --from-literal=username=query-service --from-literal=password='long-password'
helm upgrade adaptation --install . --namespace icap-adaptation
popd

# Setup icap policy management
pushd ncfs
kubectl create -n icap-ncfs secret generic ncfspolicyupdateservicesecret --from-literal=username=policy-update --from-literal=password='long-password'
helm upgrade ncfs --install . --namespace icap-ncfs
popd

# setup management ui
kubectl create -n management-ui secret generic transactionqueryserviceref --from-literal=username=query-service --from-literal=password='long-password'
kubectl create -n management-ui secret generic policyupdateserviceref --from-literal=username=policy-management --from-literal=password='long-password'
kubectl create -n management-ui secret generic ncfspolicyupdateserviceref --from-literal=username=policy-update --from-literal=password='long-password'

pushd administration
helm upgrade administration --install . --namespace management-ui
popd

cd ..

# deploy monitoring solution
git clone https://github.com/k8-proxy/k8-rebuild.git && cd k8-rebuild
helm install sow-monitoring monitoring --set monitoring.elasticsearch.host=$MONITORING_IP --set monitoring.elasticsearch.username=$MONITORING_USER --set monitoring.elasticsearch.password=$MONITORING_PASSWORD

# wait until the pods are up
# sleep 120s

# allow password login (useful when deployed to esxi)
SSH_PASSWORD=${SSH_PASSWORD:-glasswall}
printf "${SSH_PASSWORD}\n${SSH_PASSWORD}" | sudo passwd ubuntu
sudo sed -i "s/.*PasswordAuthentication.*/PasswordAuthentication yes/g" /etc/ssh/sshd_config
sudo service ssh restart
