import argparse
import html.parser
import urllib.request

url = "http://dev.overpass-api.de/releases/"



class VersionFinder(html.parser.HTMLParser):
    def error(self, message):
        raise RuntimeError(message)

    def __init__(self):
        super().__init__()
        self.versions = []

    def handle_starttag(self, tag, attrs):
        if attrs:
            href = dict(attrs).get('href')
            if tag == 'a' and href and href.startswith('osm-3s'):
                version = href[len('osm-3s_v'):-len('.tar.gz')]
                self.versions.append(version)


def fetch_versions():
    parser = VersionFinder()
    response = urllib.request.urlopen(url)
    data = response.read().decode(response.headers.get_content_charset())
    parser.feed(data)
    versions = []
    for ver in parser.versions:
        if any((ver.startswith(x) for x in ('0.6', 'eta', '0.7.1', '0.7.2', '0.7.3', '0.7.4', '0.7.50', '0.7.52',
                                            '0.7.54.11',  # invalid CRC in archive
                                            '0.7.51',  # no autoconf
                                            ))) or \
                ver == '0.7':
            # ignore old releases
            continue
        try:
            key = tuple(int(x) for x in ver.split('.'))
        except ValueError:
            continue
        versions.append((key, ver))
    return [ver for _, ver in sorted(versions)]


def main():
    arg_parser = argparse.ArgumentParser(
        description="Generate Dockerfiles from a template for overpass-api releases."
    )
    arg_parser.add_argument(
        "template",
        help="Path to the Dockerfile template file.",
    )
    arg_parser.add_argument(
        "--version",
        required=True,
        help="Version to generate for, or 'latest' to use the latest release.",
    )
    arg_parser.add_argument(
        "--output",
        default="Dockerfile",
        help="Output path for the generated Dockerfile (default: Dockerfile).",
    )
    arg_parser.add_argument(
        "--param",
        metavar="KEY=VALUE",
        action="append",
        default=[],
        help="Additional template parameters as KEY=VALUE pairs. May be specified multiple times.",
    )
    args = arg_parser.parse_args()

    extra_params = {}
    for item in args.param:
        if "=" not in item:
            arg_parser.error(f"--param must be in KEY=VALUE format, got: {item!r}")
        key, _, value = item.partition("=")
        extra_params[key] = value

    ver = fetch_versions()[-1] if args.version == "latest" else args.version

    with open(args.template) as f:
        template = f.read()

    with open(args.output, "w+") as f:
        f.write(template.format(version=ver, **extra_params))


if __name__ == '__main__':
    main()
