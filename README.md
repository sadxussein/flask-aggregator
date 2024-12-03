# Функциональный агрегатор для виртуализаций ОИТИ
## Установка
1. dnf install -y nginx postgresql16-server postgresql16
2. /usr/pgsql-16/bin/postgresql-16-setup initdb
3. Создать пользователя и базу в postgres (как указаны в install.sh)
4. Скопировать содержимое папки linux на нужный хост
5. Запустить install.sh
После установки можно запустить сбор информации с виртуализаций (пока что только oVirt). Активируем venv:
`source /app/flask-aggregator/bin/activate`
И запускаем сборщик для всех сущностей (для первого наполнения базы) - `fa_collect_all_data`
Отдельные функции для обновления базы:
 - `fa_get_vms`
 - `fa_get_hosts` (сервис с запуском стоит на таймере, раз в 30 минут)
 - `fa_get_storages` (сервис с запуском стоит на таймере, раз в 15 минут)
 - `fa_get_clusters`
 - `fa_get_data_centers`
Функции для выдачи json в мониторнинг:
 - `fa_mon_hosts`
 - `fa_mon_storages`
Эти функции нужны только для userparameters заббикс-агента.
## front
1. endpoint `/` - пустая индекс страница
2. endpoint `/ovirt/create_vm` (POST only) - эндпоинт для передачи JSON файла с конфигурациями создаваемых вм. Пример JSON:
```
[
    {
        "meta": {
            "document_num": "6666",
            "inf_system": "Ред Виртуализация",
            "owner": "ОИТИ",
            "environment": "Тест"
        },
        "ovirt": {
            "engine": "e15-test",
            "cluster": "Default",
            "storage_domain": "hosted_storage",
            "host_nic": "bond0"
        },
        "vm": {
            "name": "test_vm_11",
            "hostname": "test_vm_11",
            "cores": 2,
            "memory": 2,
            "disks": [
                {
                    "size": 40,
                    "type": 1,
                    "mount_point": "/",
                    "sparse": 0     # where 0 is false, 1 is true
                }
            ],
            "template": "template-packer-redos8-03092024",
            "os": "RedOS 8",
            "nic_name": "enp1s0",
            "gateway": "10.105.249.1",
            "netmask": "255.255.255.192",
            "address": "10.105.249.51",
            "dns_servers": "10.82.254.32 10.82.254.31"
        },
        "vlan": {
            "name": "2921-redvt-eqp-test-e15",
            "id": 2921,
            "suffix": ""
        }
    }
]
```
Передавать через curl, пример команды: `curl -X POST -F "jsonfile=@files/vm_configs/vm4004.json" http://10.105.253.252:6299/ovirt/create_vm`.
Ключ ovirt -> engine должен коррелировать с содержимым `config.py` или параметрами, передаваемыми в конструктор экземпляра класса `OvirtHelper`. 
Например, стандартная конфигурация `DPC_LIST` и `DPC_URLS` в `config.py`:
```
DPC_LIST = ["e15-test", "e15", "e15-2", "n32", "n32-2", "k45"]
DPC_URLS = {
    "e15-test": "https://e15-redvirt-engine-test2.rncb.ru/ovirt-engine/api",
    "e15": "https://e15-redvirt-engine1.rncb.ru/ovirt-engine/api",
    "e15-2": "https://e15-redvirt-engine2.rncb.ru/ovirt-engine/api",
    "n32": "https://n32-redvirt-engine1.rncb.ru/ovirt-engine/api",
    "n32-2": "https://n32-redvirt-engine2.rncb.ru/ovirt-engine/api",
    "k45": "https://k45-redvirt-engine1.rncb.ru/ovirt-engine/api"
}
```
3. endpoint `/ovirt/create_vlan`: создание VLAN. Пример JSON:
```
[
    {
        "meta": {
            "document_num": "6666",
            "inf_system": "Ред Виртуализация",
            "owner": "ОИТИ",
            "environment": "Тест"
        },
        "ovirt": {
            "engine": "e15-test",
            "cluster": "Default",
            "storage_domain": "hosted_storage",
            "host_nic": "bond0"
        },
        "vlan": {
            "name": "2921-redvt-eqp-test-e15",
            "id": 2921,
            "suffix": ""
        }
    }
]
```
Та же самая конструкция как в `create_vm`, только без ключа `vm`.
4. endpoint `/view/vms` - список ВМ
5. endpoint `/view/hosts` - список гипервизоров
6. endpoint `/view/clusters` - список кластеров
7. endpoint `/view/data_centers` - список датацентров
8. endpoint `/view/storages` - список хранилок