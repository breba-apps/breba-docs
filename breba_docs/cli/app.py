import logging
import sys

from cleo.application import Application
from breba_docs.cli.commands.new_command import NewCommand
from breba_docs.cli.commands.run_command import RunCommand
from breba_docs.cli import __version__


# Configure logging
def setup_logging(debug=False):
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',

        # We start out with a stdout handler, but later when project_root is know we will add a file handler
        handlers=[
            logging.StreamHandler(sys.stdout),
        ]
    )


def run():
    setup_logging(debug=False)

    app = Application('breba-docs', __version__)

    # Optionally, you can register a --version option here if Cleo doesn't provide it by default.
    app.add(NewCommand())
    app.add(RunCommand())

    try:
        app.run()
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        sys.exit(1)


if __name__ == '__main__':
    run()
