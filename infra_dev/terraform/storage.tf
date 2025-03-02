resource "kubernetes_storage_class" "local" {
  metadata {
    name = "local-storage"
  }
  storage_provisioner = "docker.io/hostpath"
  reclaim_policy     = "Retain"
}

resource "kubernetes_persistent_volume" "postgres" {
  metadata {
    name = "postgres-pv"
  }
  spec {
    storage_class_name = kubernetes_storage_class.local.metadata[0].name
    capacity = {
      storage = var.postgres_storage
    }
    access_modes = ["ReadWriteOnce"]
    persistent_volume_reclaim_policy = "Retain"
    persistent_volume_source {
      host_path {
        path = "${var.project_root}/.postgres-data"
        type = "DirectoryOrCreate"
      }
    }
  }
}

resource "kubernetes_persistent_volume_claim" "postgres" {
  metadata {
    name      = "postgres-pvc"
    namespace = kubernetes_namespace.amoneyplan.metadata[0].name
  }
  spec {
    storage_class_name = kubernetes_storage_class.local.metadata[0].name
    access_modes       = ["ReadWriteOnce"]
    resources {
      requests = {
        storage = var.postgres_storage
      }
    }
  }
}