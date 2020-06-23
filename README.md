# Rhasspy NLU Hermes

[![Continous Integration](https://github.com/rhasspy/rhasspy-nlu-hermes/workflows/Tests/badge.svg)](https://github.com/rhasspy/rhasspy-nlu-hermes/actions)
[![Release Version](https://images.microbadger.com/badges/version/rhasspy/rhasspy-nlu-hermes.svg)](https://hub.docker.com/r/rhasspy/rhasspy-nlu-hermes)
[![GitHub license](https://img.shields.io/github/license/rhasspy/rhasspy-nlu-hermes.svg)](https://github.com/rhasspy/rhasspy-nlu-hermes/blob/master/LICENSE)

Implements `hermes/nlu` functionality from [Hermes protocol](https://docs.snips.ai/reference/hermes) using [rhasspy-nlu](https://github.com/rhasspy/rhasspy-nlu).

## Requirements

* Python 3.7

## Installation

```bash
$ git clone https://github.com/rhasspy/rhasspy-nlu-hermes
$ cd rhasspy-nlu-hermes
$ ./configure --enable-in-place
$ make
$ make install
```

## Running

```bash
$ bin/rhasspy-nlu-hermes <ARGS>-hermes
```

## Command-Line Options

```
usage: rhasspy-nlu-hermes [-h] [--intent-graph INTENT_GRAPH]
                          [--casing {upper,lower,ignore}] [--no-fuzzy]
                          [--replace-numbers] [--language LANGUAGE]
                          [--host HOST] [--port PORT] [--username USERNAME]
                          [--password PASSWORD] [--tls]
                          [--tls-ca-certs TLS_CA_CERTS]
                          [--tls-certfile TLS_CERTFILE]
                          [--tls-keyfile TLS_KEYFILE]
                          [--tls-cert-reqs {CERT_REQUIRED,CERT_OPTIONAL,CERT_NONE}]
                          [--tls-version TLS_VERSION]
                          [--tls-ciphers TLS_CIPHERS] [--site-id SITE_ID]
                          [--debug] [--log-format LOG_FORMAT]

optional arguments:
  -h, --help            show this help message and exit
  --intent-graph INTENT_GRAPH
                        Path to intent graph (gzipped pickle)
  --casing {upper,lower,ignore}
                        Case transformation for input text (default: ignore)
  --no-fuzzy            Disable fuzzy matching in graph search
  --replace-numbers     Replace digits with words in queries (75 -> seventy
                        five)
  --language LANGUAGE   Language/locale used for number replacement (default:
                        en)
  --host HOST           MQTT host (default: localhost)
  --port PORT           MQTT port (default: 1883)
  --username USERNAME   MQTT username
  --password PASSWORD   MQTT password
  --tls                 Enable MQTT TLS
  --tls-ca-certs TLS_CA_CERTS
                        MQTT TLS Certificate Authority certificate files
  --tls-certfile TLS_CERTFILE
                        MQTT TLS certificate file (PEM)
  --tls-keyfile TLS_KEYFILE
                        MQTT TLS key file (PEM)
  --tls-cert-reqs {CERT_REQUIRED,CERT_OPTIONAL,CERT_NONE}
                        MQTT TLS certificate requirements (default:
                        CERT_REQUIRED)
  --tls-version TLS_VERSION
                        MQTT TLS version (default: highest)
  --tls-ciphers TLS_CIPHERS
                        MQTT TLS ciphers to use
  --site-id SITE_ID     Hermes site id(s) to listen for (default: all)
  --debug               Print DEBUG messages to the console
  --log-format LOG_FORMAT
                        Python logger format
```
