#!/usr/bin/env python3
import json
import argparse
import logging

import paho.mqtt.client as mqtt
from rhasspynlu import json_to_graph

from . import NluHermesMqtt

_LOGGER = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(prog="rhasspynlu_hermes")
    parser.add_argument(
        "--graph", required=True, help="Path to rhasspy graph JSON file"
    )
    parser.add_argument(
        "--host", default="localhost", help="MQTT host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=1883, help="MQTT port (default: 1883)"
    )
    parser.add_argument(
        "--siteId", default="default", help="Hermes siteId of this server"
    )
    parser.add_argument(
        "--debug", action="store_true", help="Print DEBUG messages to the console"
    )
    args, other_args = parser.parse_known_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    _LOGGER.debug(args)

    try:
        # Load graph
        _LOGGER.debug("Loading graph from %s", args.graph)
        with open(args.graph, "r") as graph_file:
            graph = json_to_graph(json.load(graph_file))

        # Listen for messages
        client = mqtt.Client()
        hermes = NluHermesMqtt(client, graph, siteId=args.siteId)

        def on_disconnect(client, userdata, flags, rc):
            try:
                # Automatically reconnect
                _LOGGER.info("Disconnected. Trying to reconnect...")
                client.reconnect()
            except Exception as e:
                logging.exception("on_disconnect")

        # Connect
        client.on_connect = hermes.on_connect
        client.on_message = hermes.on_message

        _LOGGER.debug("Connecting to %s:%s", args.host, args.port)
        client.connect(args.host, args.port)

        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _LOGGER.debug("Shutting down")


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
