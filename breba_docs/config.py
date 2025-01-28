# Default configuration values
debug_server = False
project_path = "."

def initialize(args):
    global debug_server, project_path
    debug_server = args.debug_server
    project_path = args.project