# vm4150
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4150.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4150.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4150.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4150_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4150.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4150.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4150_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4150.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4004
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4004.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4004.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4004.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4004_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4004.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4004.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4004_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4004.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4307
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4307.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4307.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4307.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4307_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4307.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4307.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4307_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4307.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4188
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4188.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4188.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4188.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4188_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4188.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4188.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4188_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4188.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4214
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4214.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4214.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4214.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4214_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4214.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4214.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4214_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4214.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4150
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4150.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4150.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4150.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4150_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4150.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4150.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4150_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4150.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4004
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4004.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4004.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4004.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4004_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4004.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4004.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4004_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4004.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4307
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4307.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4307.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4307.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4307_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4307.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4307.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4307_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4307.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4188
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4188.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4188.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4188.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4188_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4188.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4188.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4188_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4188.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4214
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4214.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4214.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4214.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4214_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4214.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4214.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4214_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4214.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4150
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4150.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4150.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4150.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4150_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4150.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4150.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4150.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4150_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4150.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4004
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4004.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4004.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4004.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4004_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4004.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4004.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4004.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4004_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4004.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4307
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4307.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4307.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4307.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4307_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4307.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4307.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4307.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4307_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4307.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4188
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4188.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4188.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4188.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4188_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4188.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4188.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4188.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4188_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4188.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4365
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4365.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4365.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4365.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4365.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4365.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4365_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4365.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4365.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4365.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4365.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4365_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4365.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4214
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/back/files/vm_configs/vm4214.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/default/inventories/vm4214.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4214.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4214_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/internal/vm4214.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_network_check/vm4214.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4214.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/back/files/logs/ipa_integration/vm4214_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/back/files/ansible/ipa/inventories/dmz/vm4214.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4436
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/src/server/back/files/vm_configs/vm4436.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/default/inventories/vm4436.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4436.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4436.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/internal/vm4436.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_integration/vm4436_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/internal/vm4436.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4436.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4436.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/dmz/vm4436.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_integration/vm4436_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/dmz/vm4436.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

# vm4434
# CURL POST VM
curl -X POST -F 'jsonfile=@/home/krasnoschekovvd/flask_aggregator/src/server/back/files/vm_configs/vm4434.json' http://10.105.253.252:6299/ovirt/create_vm
# PREPARE VM
ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/default/inventories/vm4434.yml default-playbook.yml
# IPA INTERNAL
rm -f /home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4434.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4434.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/internal/vm4434.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_integration/vm4434_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/internal/vm4434.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause
# IPA DMZ
rm -f /home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4434.log && ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_network_check/vm4434.log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/dmz/vm4434.yml  network_check.yml -u svc_ansibleoiti
ANSIBLE_LOG_PATH=/home/krasnoschekovvd/flask_aggregator/src/server/back/files/logs/ipa_integration/vm4434_$(date +%Y-%m-%d_%H-%M-%S).log ansible-playbook -i /home/krasnoschekovvd/flask_aggregator/src/server/back/files/ansible/ipa/inventories/dmz/vm4434.yml host_prepare.yml -u svc_ansibleoiti --tags all,ipa_client_repair,splunk_reinstall --skip-tags pause

