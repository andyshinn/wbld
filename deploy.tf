terraform {
  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "2.8.0"
    }
  }
}

variable "image" {
  default = "ghcr.io/andyshinn/wbld:latest"
}

variable "github_token" {
  description = "GitHub token for GHCR auth"
}

variable "discord_token" {
  description = "Discord auth token"
}

provider "docker" {
  host = "tcp://localhost:2375"

  registry_auth {
    address  = "ghcr.io"
    username = "andyshinn"
    password = var.registry_password
  }
}

resource "docker_container" "wbld" {
  name    = "wbld"
  image   = docker_image.wbld.latest
  command = ["python3", "-m", "wbld.bot"]
  env     = ["DISCORD_TOKEN=${var.discord_token}"]
}

data "docker_registry_image" "wbld" {
  name = var.image
}

resource "docker_image" "wbld" {
  name          = data.docker_registry_image.wbld.name
  pull_triggers = [data.docker_registry_image.wbld.sha256_digest]
}
