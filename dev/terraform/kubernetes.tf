resource "kubernetes_deployment" "postgres" {
  depends_on = [
    kubernetes_namespace.amoneyplan,
    kubernetes_persistent_volume.postgres,
    kubernetes_persistent_volume_claim.postgres
  ]

  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.amoneyplan.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "postgres"
      }
    }

    template {
      metadata {
        labels = {
          app = "postgres"
        }
      }

      spec {
        container {
          name  = "postgres"
          image = "postgres:14-alpine"

          port {
            container_port = 5432
          }

          env_from {
            config_map_ref {
              name = kubernetes_config_map.postgres.metadata[0].name
            }
          }

          volume_mount {
            mount_path = "/var/lib/postgresql/data"
            name       = "postgres-data"
          }
        }

        volume {
          name = "postgres-data"
          persistent_volume_claim {
            claim_name = kubernetes_persistent_volume_claim.postgres.metadata[0].name
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "postgres" {
  depends_on = [kubernetes_deployment.postgres]

  metadata {
    name      = "postgres"
    namespace = kubernetes_namespace.amoneyplan.metadata[0].name
  }

  spec {
    selector = {
      app = "postgres"
    }

    port {
      port        = 5432
      target_port = 5432
      node_port   = 30432
    }

    type = "NodePort"
  }
}

resource "kubernetes_deployment" "backend" {
  depends_on = [
    kubernetes_namespace.amoneyplan,
    kubernetes_deployment.postgres,
    null_resource.load_image
  ]

  metadata {
    name      = "backend"
    namespace = kubernetes_namespace.amoneyplan.metadata[0].name
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "backend"
      }
    }

    template {
      metadata {
        labels = {
          app = "backend"
        }
      }

      spec {
        container {
          name  = "backend"
          image = "amoneyplan-backend:latest"

          port {
            container_port = 8000
          }

          env {
            name  = "DJANGO_SETTINGS_MODULE"
            value = "amoneyplan.settings"
          }

          env {
            name = "DB_NAME"
            value_from {
              config_map_key_ref {
                name = kubernetes_config_map.postgres.metadata[0].name
                key  = "POSTGRES_DB"
              }
            }
          }

          env {
            name = "DB_USER"
            value_from {
              config_map_key_ref {
                name = kubernetes_config_map.postgres.metadata[0].name
                key  = "POSTGRES_USER"
              }
            }
          }

          env {
            name = "DB_PASSWORD"
            value_from {
              config_map_key_ref {
                name = kubernetes_config_map.postgres.metadata[0].name
                key  = "POSTGRES_PASSWORD"
              }
            }
          }

          env {
            name  = "DB_HOST"
            value = kubernetes_service.postgres.metadata[0].name
          }

          env {
            name  = "DB_PORT"
            value = "5432"
          }

          # Add Python unbuffered mode for better log output
          env {
            name  = "PYTHONUNBUFFERED"
            value = "1"
          }

          # Add debug mode for development
          env {
            name  = "DEBUG"
            value = "True"
          }

          command = ["/bin/bash", "-c"]
          args    = [<<-EOT
            python manage.py migrate &&
            python manage.py init_db --sample &&
            python manage.py runserver 0.0.0.0:8000
          EOT
          ]

          volume_mount {
            name       = "backend-code"
            mount_path = "/app"
          }
        }

        volume {
          name = "backend-code"
          host_path {
            path = "${path.root}/../../backend"
            type = "Directory"
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "backend" {
  depends_on = [kubernetes_deployment.backend]

  metadata {
    name      = "backend"
    namespace = kubernetes_namespace.amoneyplan.metadata[0].name
  }

  spec {
    selector = {
      app = "backend"
    }

    port {
      port        = 8000
      target_port = 8000
      node_port   = 30080
    }

    type = "NodePort"
  }
}