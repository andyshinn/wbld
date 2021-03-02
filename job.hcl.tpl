job "wbld" {
  datacenters = ["sheraton"]

  update {
    max_parallel = 0
  }

  group "server" {
    meta {
      commit = "${commit}"
    }

    network {
      port "http" {
        static = 8092
        to     = 8090
      }
    }

    task "bot" {
      driver = "docker"

      config {
        image      = "${image}"
        command    = "python3"
        force_pull = true
        args       = ["-m", "wbld.bot"]

        auth {
          username       = "andyshinn"
          password       = "${github_token}"
          server_address = "ghcr.io"
        }

        mounts = [
          {
            type   = "volume"
            target = "/root/.platformio"
            source = "wbld_platformio"
          },
          {
            type   = "volume"
            target = "/root/.buildcache"
            source = "wbld_buildcache"
          },
          {
            type   = "volume"
            target = "/root/wbld"
            source = "wbld_data"
          }
        ]
      }

      resources {
        cpu    = 1000
        memory = 1024
      }

      env {
        DISCORD_TOKEN = "${discord_token}"
        SENTRY_DSN = "${sentry_dsn}"
        PING_URL      = "${ping_url}"
        STORAGE_DIR   = "/root/wbld"
      }
    }

    task "web" {
      driver = "docker"

      config {
        image      = "${image}"
        command    = "python3"
        force_pull = true
        args       = ["-m", "wbld.web"]

        auth {
          username       = "andyshinn"
          password       = "${github_token}"
          server_address = "ghcr.io"
        }

        mounts = [
          {
            type   = "volume"
            target = "/root/wbld"
            source = "wbld_data"
          }
        ]

        ports = ["http"]
      }

      resources {
        cpu    = 1000
        memory = 1024
      }

      env {
        SENTRY_DSN = "${sentry_dsn}"
        STORAGE_DIR = "/root/wbld"
      }
    }
  }
}
