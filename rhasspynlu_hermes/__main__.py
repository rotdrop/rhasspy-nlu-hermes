#!/usr/bin/env python3
"""Hermes MQTT service for rhasspynlu"""
import argparse
import json
import logging
import os
import threading
import time

import paho.mqtt.client as mqtt
from rhasspynlu import json_to_graph

from . import NluHermesMqtt

_LOGGER = logging.getLogger(__name__)


def main():
    """Main method."""
    parser = argparse.ArgumentParser(prog="rhasspynlu_hermes")
    parser.add_argument(
        "--graph", required=True, help="Path to rhasspy graph JSON file"
    )
    parser.add_argument(
        "--reload",
        type=float,
        default=None,
        help="Poll graph JSON file for given number of seconds and automatically reload when changed",
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
    args = parser.parse_args()

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

        if args.reload:
            # Start polling thread
            threading.Thread(
                target=poll_graph, args=(args.reload, args.graph, hermes), daemon=True
            ).start()

        def on_disconnect(client, userdata, flags, rc):
            try:
                # Automatically reconnect
                _LOGGER.info("Disconnected. Trying to reconnect...")
                client.reconnect()
            except Exception:
                logging.exception("on_disconnect")

        # Connect
        client.on_connect = hermes.on_connect
        client.on_disconnect = on_disconnect
        client.on_message = hermes.on_message

        _LOGGER.debug("Connecting to %s:%s", args.host, args.port)
        client.connect(args.host, args.port)

        client.loop_forever()
    except KeyboardInterrupt:
        pass
    finally:
        _LOGGER.debug("Shutting down")


# -----------------------------------------------------------------------------


def poll_graph(seconds: float, graph_path: str, hermes: NluHermesMqtt):
    """Watch graph file for changes and reload."""
    last_timestamp: int = 0

    while True:
        time.sleep(seconds)
        try:
            timestamp = os.stat(graph_path).st_mtime_ns
            if timestamp != last_timestamp:
                # Reload graph
                _LOGGER.debug("Re-loading graph from %s", graph_path)
                with open(graph_path, "r") as graph_file:
                    # Set in Hermes object
                    hermes.graph = json_to_graph(json.load(graph_file))

                last_timestamp = timestamp
        except Exception:
            _LOGGER.exception("poll_graph")


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
