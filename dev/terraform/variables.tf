variable "kubernetes_version" {
  description = "Kubernetes version to use for the kind cluster"
  type        = string
  default     = "v1.29.0"
}

variable "postgres_version" {
  description = "PostgreSQL version to use"
  type        = string
  default     = "14-alpine"
}

variable "postgres_storage" {
  description = "Storage size for PostgreSQL PVC"
  type        = string
  default     = "1Gi"
}

variable "backend_replicas" {
  description = "Number of backend replicas"
  type        = number
  default     = 1
}

variable "backend_port" {
  description = "Port for the backend service"
  type        = number
  default     = 8000
}

variable "postgres_port" {
  description = "Port for the PostgreSQL service"
  type        = number
  default     = 5432
}

variable "project_root" {
  description = "Root directory of the project"
  type        = string
}
