from pathlib import Path


class Document:
    filepath: Path
    content: str

    def __init__(self, contents: str, filepath: Path):
        self.filepath = filepath
        self.content = contents

    def persist(self):
        # Ensure the parent directory exists
        self.filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write the content to the file
        with open(self.filepath, "w") as f:
            f.write(self.content)
