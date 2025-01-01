import argparse

import podsync
from podsync.config import BaseConfig, Config, PartialConfig


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + podsync.__version__
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="Increase verbosity", required=False
    )
    parser.add_argument(
        "-s", "--speedup", type=int, help="Speed up the download", required=False
    )
    parser.add_argument(
        "-c", "--config", help="Path to the TOML configuration file", default=None
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create the "download" subparser
    dl_parser = subparsers.add_parser("download", help="Download a podcast")
    dl_parser.add_argument("url", help="URL of the mp3 file")
    dl_parser.add_argument(
        "-p", "--path", help="Path to store the new file", required=False
    )

    # Parse and execute
    try:
        args = parser.parse_args()
    except Exception as e:
        print(f"Error: {e}. Exiting.")
        exit(1)

    # Load the configuration
    config = Config(
        PartialConfig(
            download_path=args.path, verbose=args.verbose, speedup=args.speedup
        ),
        args.config,
    )

    try:
        args = parser.parse_args()
        if args.command == "download":
            podsync.download(config, args.url)
    except Exception as e:
        print(f"Error: {e}. Exiting.")
        exit(1)


if __name__ == "__main__":
    main()
