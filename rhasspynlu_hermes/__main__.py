"""Hermes MQTT service for rhasspynlu"""
import argparse
import asyncio
import logging
import typing
from pathlib import Path

import paho.mqtt.client as mqtt
import rhasspyhermes.cli as hermes_cli

from . import NluHermesMqtt
from .utils import load_converters

_LOGGER = logging.getLogger("rhasspynlu_hermes")

# -----------------------------------------------------------------------------


def main():
    """Main method."""
    parser = argparse.ArgumentParser(prog="rhasspy-nlu-hermes")
    parser.add_argument("--intent-graph", help="Path to intent graph (gzipped pickle)")
    parser.add_argument(
        "--casing",
        choices=["upper", "lower", "ignore"],
        default="ignore",
        help="Case transformation for input text (default: ignore)",
    )
    parser.add_argument(
        "--no-fuzzy", action="store_true", help="Disable fuzzy matching in graph search"
    )
    parser.add_argument(
        "--replace-numbers",
        action="store_true",
        help="Replace digits with words in queries (75 -> seventy five)",
    )
    parser.add_argument(
        "--language", help="Language/locale used for number replacement (default: en)"
    )
    parser.add_argument(
        "--converters-dir",
        help="Path to custom converter directory with executable scripts",
    )

    hermes_cli.add_hermes_args(parser)

    args = parser.parse_args()

    hermes_cli.setup_logging(args)
    _LOGGER.debug(args)

    # Convert to Paths
    if args.intent_graph:
        args.intent_graph = Path(args.intent_graph)

    extra_converters = None
    if args.converters_dir:
        args.converters_dir = Path(args.converters_dir)
        extra_converters = load_converters(args.converters_dir)

    # Listen for messages
    client = mqtt.Client()
    hermes = NluHermesMqtt(
        client,
        graph_path=args.intent_graph,
        word_transform=get_word_transform(args.casing),
        replace_numbers=args.replace_numbers,
        language=args.language,
        fuzzy=(not args.no_fuzzy),
        extra_converters=extra_converters,
        site_ids=args.site_id,
    )

    _LOGGER.debug("Connecting to %s:%s", args.host, args.port)
    hermes_cli.connect(client, args)
    client.loop_start()

    try:
        # Run event loop
        asyncio.run(hermes.handle_messages_async())
    except KeyboardInterrupt:
        pass
    finally:
        _LOGGER.debug("Shutting down")
        client.loop_stop()


# -----------------------------------------------------------------------------


def get_word_transform(name: str) -> typing.Callable[[str], str]:
    """Gets a word transformation function by name."""
    if name == "upper":
        return str.upper

    if name == "lower":
        return str.lower

    return lambda s: s


# -----------------------------------------------------------------------------

if __name__ == "__main__":
    main()
