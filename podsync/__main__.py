import argparse

import podsync


def main():
    # Create the top-level parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version", action="version", version="%(prog)s " + podsync.__version__
    )
    parser.add_argument(
        "-v", "--verbose", action="count", help="Increase verbosity", default=0
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create the "download" subparser
    dl_parser = subparsers.add_parser("download", help="Download a podcast")
    dl_parser.add_argument("url", help="URL of the mp3 file")
    dl_parser.add_argument("path", help="Path to store the new file")

    # Parse and execute
    try:
        args = parser.parse_args()
        if args.command == "download":
            podsync.download(args.url, args.path, verbose=args.verbose)
    except Exception as e:
        print(f"Error: {e}. Exiting.")
        exit(1)


if __name__ == "__main__":
    main()
