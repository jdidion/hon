from pathlib import Path
import pkg_resources


TEMPLATES = None


class TemplateDir:
    def __init__(self):
        self.templates = {}
        self.subdirs = {}

    def add_template(self, filename: str, template: str):
        self.templates[filename] = template

    def add_subdir(self, dirname: str, subdir: "TemplateDir"):
        self.subdirs[dirname] = subdir

    def create(self, parent_dir: Path, values: dict):
        for filename, template in self.templates.items():
            resolved_filename = filename.format(**values)
            template_str = template.format(**values)
            with open(parent_dir / resolved_filename, "wt") as out:
                out.write(template_str)
        for dirname, template_dir in self.subdirs.items():
            resolved_dirname = dirname.format(**values)
            subdir = Path(parent_dir / resolved_dirname)
            subdir.mkdir(parents=True)
            template_dir.create(subdir, values)


def get_templates() -> TemplateDir:
    """
    Returns a :class:`TemplateDir` mirroring the templates directory structure.
    """
    global TEMPLATES
    if TEMPLATES is None:
        TEMPLATES = TemplateDir()
        _load_templates(TEMPLATES, "templates")
    return TEMPLATES


def _load_templates(template_dir: TemplateDir, path: str):
    entries = pkg_resources.resource_listdir("hon", path)
    for entry in entries:
        entry_path = "/".join((path, entry))
        if pkg_resources.resource_isdir("hon", entry_path):
            subdir = TemplateDir()
            template_dir.add_subdir(entry, subdir)
            _load_templates(subdir, entry_path)
        else:
            filename = entry
            # python templates end with .py_ to prevent the from being compiled
            if filename.endswith(".py_"):
                filename = filename[:-1]
            template = pkg_resources.resource_string("hon", entry_path).decode("utf-8")
            template_dir.add_template(filename, template)
