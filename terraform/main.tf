resource "yandex_vpc_network" "net" {
  name = "net"
}

resource "yandex_vpc_subnet" "subnet_a" {
  name           = "subnet-a"
  zone           = "ru-central1-a"
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = ["192.168.10.0/24"]
}
resource "yandex_vpc_subnet" "subnet_e" {
  name           = "subnet-e"
  zone           = "ru-central1-e"
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = ["192.168.11.0/24"]
}
resource "yandex_vpc_subnet" "subnet_d" {
  name           = "subnet-d"
  zone           = "ru-central1-d"
  network_id     = yandex_vpc_network.net.id
  v4_cidr_blocks = ["192.168.12.0/24"]
}

module "master" {
  source          = "./modules/vm_module"
  vm_name         = "k3s-master-1"
  subnet_id       = yandex_vpc_subnet.subnet_a.id
  vm_cores        = 2
  vm_memory       = 4
  vm_size         = 20
  cloud_init_file = "${path.module}/cloud-init.yaml"
  zone            = "ru-central1-a"
}
module "worker_1" {
  source          = "./modules/vm_module"
  vm_name         = "k3s-worker-1"
  subnet_id       = yandex_vpc_subnet.subnet_e.id
  vm_cores        = 2
  vm_memory       = 4
  vm_size         = 20
  cloud_init_file = "${path.module}/cloud-init.yaml"
  zone            = "ru-central1-e"
}
module "worker_2" {
  source          = "./modules/vm_module"
  vm_name         = "k3s-worker-2"
  subnet_id       = yandex_vpc_subnet.subnet_d.id
  vm_cores        = 2
  vm_memory       = 4
  vm_size         = 20
  cloud_init_file = "${path.module}/cloud-init.yaml"
  zone            = "ru-central1-d"
}
