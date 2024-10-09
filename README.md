# Функциональный агрегатор для виртуализаций ОИТИ
## back
Класс `OvirtHelper` в `ovirt_helper.py` - для работы в oVirt. Основной функционал:
1. `get_vm_list` - получает список ВМ в виде словаря из всех энжинов
2. `create_vm` - создание ВМ
## front
Класс `FlaskAggregator` в `app.py` - сервер фласка, вебморда для взаимодействий с виртуализациями. Основной функционал:
1. endpoint `/` - пустая индекс страница
2. endpoint `/ovirt_vm_list` - страница содержащая список всех вм с фильтром
3. endpoint `/create_vm` (POST only) - эндпоинт для передачи JSON файла с конфигурациями создаваемых вм. Пример JSON:
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
                    "mount_point": "/"
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
            "id": 2921
        }
    }
]
```
Передавать через curl, пример команды: `curl -X POST -F "jsonfile=@vm_queries/new/test.json" http://10.105.253.252:6299/create_vm`.
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
# (TBD) utils
Переписать утилиту для парса excel файла заявки на ВМ из элмы