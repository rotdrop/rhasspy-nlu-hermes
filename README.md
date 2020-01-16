# Rhasspy NLU Hermes
[![Continous Integration](https://github.com/rhasspy/rhasspy-nlu-hermes/workflows/Test%20Python%20package/badge.svg)](https://github.com/rhasspy/rhasspy-nlu-hermes/actions)

Implements `hermes/nlu` functionality from [Hermes protocol](https://docs.snips.ai/reference/hermes) using [rhasspy-nlu](https://github.com/synesthesiam/rhasspy-nlu).

## Running With Docker

```bash
docker run -it rhasspy/rhasspy-nlu-hermes:<VERSION> <ARGS>
```

## Building From Source

Clone the repository and create the virtual environment:

```bash
git clone https://github.com/rhasspy/rhasspy-nlu-hermes.git
cd rhasspy-nlu-hermes
make venv
```

Run the `bin/rhasspy-nlu-hermes` script to access the command-line interface:

```bash
bin/rhasspy-nlu-hermes --help
```

## Building the Debian Package

Follow the instructions to build from source, then run:

```bash
source .venv/bin/activate
make debian
```

If successful, you'll find a `.deb` file in the `dist` directory that can be installed with `apt`.

## Building the Docker Image

Follow the instructions to build from source, then run:

```bash
source .venv/bin/activate
make docker
```

This will create a Docker image tagged `rhasspy/rhasspy-nlu-hermes:<VERSION>` where `VERSION` comes from the file of the same name in the source root directory.

NOTE: If you add things to the Docker image, make sure to whitelist them in `.dockerignore`.

## Command-Line Options

```
usage: rhasspy-nlu-hermes [-h] --graph GRAPH [--reload RELOAD] [--host HOST]
                          [--port PORT] [--siteId SITEID] [--debug]

optional arguments:
  -h, --help       show this help message and exit
  --graph GRAPH    Path to rhasspy graph JSON file
  --reload RELOAD  Poll graph JSON file for given number of seconds and
                   automatically reload when changed
  --host HOST      MQTT host (default: localhost)
  --port PORT      MQTT port (default: 1883)
  --siteId SITEID  Hermes siteId(s) to listen for (default: all)
  --debug          Print DEBUG messages to the console
```
