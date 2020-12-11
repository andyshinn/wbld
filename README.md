# WBLD

WBLD is a Discord bot that builds [WLED](https://github.com/Aircoookie/WLED) firmware. The scope of the bot is simple: Build WLED firmware based on builtin environments or custom configurations and give the binary file via Discord.

You can use the bot in the #bot channel of the WLED Disord server: https://discord.gg/KuqP7NE

## Commands

There are two primary commands. If `version` is not specified it defaults to the current `master` branch:

### `./build builtin <environment> [version]`

The `builtin` command builds a firmware based on existing environments defined in `platformio.ini`. For example, the following will build a `d1_mini` firmware based on version 0.10.2:

```
./build builtin d1_mini v0.10.2
```

### `./build custom [version]`

The `custom` command builds a PlatformIO configuration snippet. This can help build firmware with specific supported usermods, custom pins, or other settings defined in macros. For example, the following will build a firmware for the QuinLED-Dig-Uno with temperature sensor usermod based the `master` branch:

```
./build custom
```

Then paste the following configuration:

```
[env:quinled_dig_uno]
extends = env:d1_mini
build_flags = ${common.build_flags_esp8266}
  -D USERMOD_DALLASTEMPERATURE
  -D USERMOD_DALLASTEMPERATURE_CELSIUS
lib_deps = ${env.lib_deps}
  milesburton/DallasTemperature@^3.9.0
  OneWire@~2.3.5
```
