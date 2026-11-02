variable "zone" {
  type = string
}

variable "subnet_id" {
  type = string
}

variable "vm_cores" {
  type    = number
  default = 2
}

variable "vm_memory" {
  type    = number
  default = 2
}

variable "vm_image_id" {
  type    = string
  default = "fd82sqrj4uk9j7vlki3q"
}

variable "vm_size" {
  type    = number
  default = 20
}

variable "vm_name" {
  type    = string
  default = "cloud-init-vm"
}

variable "platform_id" {
  type    = string
  default = "standard-v3"
}

variable "cloud_init_file" {
  type    = string
  default = "cloud-init.yaml"
}
