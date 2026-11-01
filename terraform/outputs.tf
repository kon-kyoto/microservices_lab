output "master_external_ip" {
  value = module.master.vm_external_ip
}

output "worker_external_ips" {
  value = [
    module.worker_1.vm_external_ip,
    module.worker_2.vm_external_ip,
  ]
}

output "all_external_ips" {
  value = {
    master   = module.master.vm_external_ip
    worker_1 = module.worker_1.vm_external_ip
    worker_2 = module.worker_2.vm_external_ip
  }
}
