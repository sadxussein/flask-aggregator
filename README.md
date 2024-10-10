# Функциональный агрегатор для виртуализаций ОИТИ
## Настройка
1. Положить содержимое в /usr/local/bin/flask_aggregator
2. Поставить в crontab геттеры по вкусу
3. Запустить приложение из корня flask_aggregator через `python3 -m front.app`
## back
Класс `OvirtHelper` в `ovirt_helper.py` - для работы в oVirt. Основной функционал:
1. `get_vm_list` - получает список ВМ в виде словаря из всех энжинов
2. `get_host_list` - получает список хостов в виде словаря из всех энжинов
3. `get_cluster_list` - получает список кластеров в виде словаря из всех энжинов
4. `create_vm` - создание ВМ
5. `create_vlan` - создание VLAN
Standalone геттеры нужны для выгрузки в JSON результатов геттеров класса `OvirtHelper`.
## front
Класс `FlaskAggregator` в `app.py` - сервер фласка, вебморда для взаимодействий с виртуализациями. Основной функционал:
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
Передавать через curl, пример команды: `curl -X POST -F "jsonfile=@vm_queries/new/test.json" http://10.105.253.252:6299/ovirt/create_vm`.
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
4. endpoint `/ovirt/vm_list` - список ВМ
5. endpoint `/ovirt/host_list` - список гипервизоров
6. endpoint `/ovirt/cluster_list` - список кластеров