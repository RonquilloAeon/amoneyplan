terraform {
  required_providers {
    kind = {
      source  = "tehcyx/kind"
      version = "0.2.1"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "2.27.0"
    }
    docker = {
      source  = "kreuzwerker/docker"
      version = "3.0.2"
    }
    time = {
      source  = "hashicorp/time"
      version = "0.10.0"
    }
  }
}

provider "kind" {}

provider "kubernetes" {
  host                   = kind_cluster.amoneyplan.endpoint
  cluster_ca_certificate = kind_cluster.amoneyplan.cluster_ca_certificate
  client_certificate     = kind_cluster.amoneyplan.client_certificate
  client_key             = kind_cluster.amoneyplan.client_key
}

provider "docker" {
  host = "unix://${pathexpand("~")}/.docker/run/docker.sock"
}

resource "kind_cluster" "amoneyplan" {
  name       = "amoneyplan"
  node_image = "kindest/node:v1.29.0"
  kind_config {
    kind        = "Cluster"
    api_version = "kind.x-k8s.io/v1alpha4"

    node {
      role = "control-plane"

      extra_port_mappings {
        container_port = 30080
        host_port      = 8001
        protocol       = "TCP"
      }

      extra_port_mappings {
        container_port = 30432
        host_port      = 5432
        protocol       = "TCP"
      }

      # Add source code mounting for hot reload
      extra_mounts {
        host_path      = "${path.root}/../../backend/src"
        container_path = "/src"
      }

      labels = {
        "com.docker.prune.keep" = "true"
      }
    }
  }

  # Add this to ensure cluster isn't recreated if it exists
  lifecycle {
    ignore_changes = all
  }
}

# Wait for the cluster to be fully ready
resource "time_sleep" "wait_for_cluster" {
  depends_on      = [kind_cluster.amoneyplan]
  create_duration = "30s"
}

resource "docker_image" "backend" {
  name = "amoneyplan-backend:latest"
  build {
    context  = "${path.root}/../../backend"
    tag      = ["amoneyplan-backend:latest"]
    no_cache = true

    label = {
      "com.docker.prune.keep" = "true"
    }
  }
  triggers = {
    dir_sha1 = sha1(join("", [for f in fileset("${path.root}/../../backend", "**") : filesha1("${path.root}/../../backend/${f}")]))
  }
}

resource "null_resource" "load_image" {
  depends_on = [kind_cluster.amoneyplan, docker_image.backend]

  provisioner "local-exec" {
    command = "kind load docker-image amoneyplan-backend:latest --name amoneyplan"
  }

  triggers = {
    image_id = docker_image.backend.id
  }
}

resource "kubernetes_namespace" "amoneyplan" {
  depends_on = [time_sleep.wait_for_cluster]

  metadata {
    name = "amoneyplan"
  }
}

resource "kubernetes_config_map" "postgres" {
  depends_on = [kubernetes_namespace.amoneyplan]

  metadata {
    name      = "postgres-config"
    namespace = kubernetes_namespace.amoneyplan.metadata[0].name
  }

  data = {
    POSTGRES_DB       = "amoneyplan"
    POSTGRES_USER     = "postgres"
    POSTGRES_PASSWORD = "postgres"
  }
}
