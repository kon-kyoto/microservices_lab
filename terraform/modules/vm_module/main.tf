resource "yandex_compute_instance" "vm" {
  name                      = var.vm_name
  platform_id               = var.platform_id
  zone                      = var.zone
  allow_stopping_for_update = true

  resources {
    cores  = var.vm_cores
    memory = var.vm_memory
  }

  boot_disk {
    initialize_params {
      image_id = var.vm_image_id
      size     = var.vm_size
    }
  }

  network_interface {
    subnet_id = var.subnet_id
    nat       = true
  }

  metadata = {
    user-data = file(var.cloud_init_file)
  }
}
