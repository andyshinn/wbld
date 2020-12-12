job "wbld" {
  datacenters = ["sheraton"]

  update {
    max_parallel = 0
  }

  task "server" {
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
        }
      ]
    }

    env {
      DISCORD_TOKEN = "${discord_token}"
      PING_URL      = "${ping_url}"
    }
  }
}
