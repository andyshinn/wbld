terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "2.8.0"
    }

    nomad = {
      source  = "hashicorp/nomad"
      version = "1.4.11"
    }
  }
}

variable "commit" {
  default = "0000000000000000000000000000000000000000"
}

variable "image" {
  default = "ghcr.io/andyshinn/wbld:latest"
}

variable "github_token" {
  description = "GitHub token for GHCR auth"
  sensitive   = true
}

variable "discord_token" {
  description = "Discord auth token"
  sensitive   = true
}

variable "sentry_dsn" {
  description = "Sentry DSN URL"
  sensitive   = true
}

variable "ping_url" {
  description = "Health check ping URL"
  sensitive   = true
}

provider "nomad" {
  address = "http://127.0.0.1:4646"
}

provider "docker" {
  host = "tcp://127.0.0.1:2375"

  registry_auth {
    address  = "ghcr.io"
    username = "andyshinn"
    password = var.github_token
  }
}

resource "docker_volume" "wbld_buildcache" {
  name = "wbld_buildcache"
}

resource "docker_volume" "wbld_platformio" {
  name = "wbld_platformio"
}

resource "nomad_job" "wbld" {
  depends_on = [docker_volume.wbld_buildcache, docker_volume.wbld_platformio]
  jobspec = templatefile(
    "job.hcl.tpl",
    { github_token  = var.github_token,
      discord_token = var.discord_token,
      sentry_dsn    = var.sentry_dsn,
      image         = var.image,
      ping_url      = var.ping_url,
      commit        = var.commit
    }
  )
}
