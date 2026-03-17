#!/usr/bin/env python
"""
qr - Convert stdin (or the first argument) to a QR Code.

When stdout is a tty the QR Code is printed to the terminal and when stdout is
a pipe to a file an image is written. The default image format is PNG.
"""

from __future__ import annotations

import optparse
import os
import sys
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

import qrcode

if TYPE_CHECKING:
    from collections.abc import Iterable

    from qrcode.image.base import BaseImage, DrawerAliases

# The next block is added to get the terminal to display properly on MS platforms
if sys.platform.startswith(("win", "cygwin")):  # pragma: no cover
    import colorama

    colorama.init()

default_factories = {
    "pil": "qrcode.image.pil.PilImage",
    "png": "qrcode.image.pure.PyPNGImage",
    "svg": "qrcode.image.svg.SvgImage",
    "svg-fragment": "qrcode.image.svg.SvgFragmentImage",
    "svg-path": "qrcode.image.svg.SvgPathImage",
    # Keeping for backwards compatibility:
    "pymaging": "qrcode.image.pure.PymagingImage",
}

error_correction = {
    "L": qrcode.ERROR_CORRECT_L,
    "M": qrcode.ERROR_CORRECT_M,
    "Q": qrcode.ERROR_CORRECT_Q,
    "H": qrcode.ERROR_CORRECT_H,
    "low": qrcode.ERROR_CORRECT_L,
    "medium": qrcode.ERROR_CORRECT_M,
    "quartile": qrcode.ERROR_CORRECT_Q,
    "high": qrcode.ERROR_CORRECT_H,
}


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    version = metadata.version("qrcode")
    parser = optparse.OptionParser(usage=(__doc__ or "").strip(), version=version)

    # Wrap parser.error in a typed NoReturn method for better typing.
    def raise_error(msg: str) -> NoReturn:
        parser.error(msg)
        raise  # pragma: no cover # noqa: PLE0704

    parser.add_option(
        "--factory",
        help="Full python path to the image factory class to "
        "create the image with. You can use the following shortcuts to the "
        f"built-in image factory classes: {commas(default_factories)}.",
    )
    parser.add_option(
        "--factory-drawer",
        help=f"Use an alternate drawer. {get_drawer_help()}.",
    )
    parser.add_option(
        "--optimize",
        type=int,
        help="Optimize the data by looking for chunks "
        "of at least this many characters that could use a more efficient "
        "encoding method. Use 0 to turn off chunk optimization.",
    )
    parser.add_option(
        "--error-correction",
        type="choice",
        choices=sorted(error_correction.keys()),
        default="M",
        help="The error correction level to use. Choices are L (7%), "
        "M (15%, default), Q (25%), and H (30%).",
    )
    parser.add_option(
        "--ascii", help="Print as ascii even if stdout is piped.", action="store_true"
    )
    parser.add_option(
        "--output",
        "-o",
        help="The output file. If not specified, the image is sent to "
        "the standard output.",
    )
    parser.add_option(
        "--style",
        choices=["a1", "a1c", "a1p", "a2", "a2c", "sp1", "c2"],
        help="Qrbtf style: a1, a1c, a1p, a2, a2c, sp1, or c2. Requires PIL. "
        "Overrides --factory when set.",
    )
    parser.add_option(
        "--box-size",
        type=int,
        default=10,
        help="Size of each module in pixels (default: 10).",
    )
    parser.add_option(
        "--border",
        type=int,
        default=4,
        help="Border size in modules (default: 4).",
    )
    parser.add_option(
        "--opt",
        "-O",
        action="append",
        dest="qrbtf_opts",
        metavar="KEY=VALUE",
        help="Qrbtf option (repeatable). Overrides preset. E.g. "
        "--opt content_point_scale=0.5 --opt positioning_point_type=circle. "
        "Numeric values are parsed as float.",
    )

    opts, args = parser.parse_args(args)

    if opts.style:
        # Qrbtf-style path: use make_qrbtf_* and save (SVG when output is .svg)
        output_is_svg = opts.output and opts.output.lower().endswith(".svg")
        if output_is_svg and opts.style == "c2":
            raise_error("C2 style is image-based; SVG output is not supported. Use PNG.")
        use_svg = output_is_svg and opts.style != "c2"
        if use_svg:
            try:
                from qrcode.image.qrbtf.styles import (
                    make_qrbtf_a1_svg,
                    make_qrbtf_a2_svg,
                    make_qrbtf_sp1_svg,
                )
            except ImportError as e:
                raise_error("Qrbtf SVG output failed: " + str(e))
            svg_makers = {
                "a1": make_qrbtf_a1_svg,
                "a1c": make_qrbtf_a1_svg,
                "a1p": make_qrbtf_a1_svg,
                "a2": make_qrbtf_a2_svg,
                "a2c": make_qrbtf_a2_svg,
                "sp1": make_qrbtf_sp1_svg,
            }
            make_fn = svg_makers.get(opts.style)
        else:
            try:
                from qrcode.image.qrbtf import (
                    make_qrbtf_a1,
                    make_qrbtf_a2,
                    make_qrbtf_c2,
                    make_qrbtf_sp1,
                )
            except ImportError as e:
                raise_error(
                    "Qrbtf styles require PIL: pip install 'qrcode[pil]'. " + str(e)
                )
            makers = {
                "a1": make_qrbtf_a1,
                "a1c": make_qrbtf_a1,
                "a1p": make_qrbtf_a1,
                "a2": make_qrbtf_a2,
                "a2c": make_qrbtf_a2,
                "sp1": make_qrbtf_sp1,
                "c2": make_qrbtf_c2,
            }
            make_fn = makers[opts.style]
        if args:
            data = args[0]
            if isinstance(data, bytes):
                data = data.decode(errors="surrogateescape")
        else:
            data = sys.stdin.buffer.read().decode(errors="surrogateescape")
        kwargs = {
            "box_size": opts.box_size,
            "border": opts.border,
            "correct_level": error_correction[opts.error_correction],
        }
        # Parse --opt KEY=VALUE into kwargs (override preset defaults)
        # Normalize key: hyphens -> underscores so positioning-point-type works
        for s in opts.qrbtf_opts or []:
            if "=" not in s:
                raise_error(f"Invalid --opt (expected KEY=VALUE): {s!r}")
            key, value = s.split("=", 1)
            key = key.strip().replace("-", "_")
            value = value.strip()
            if key == "correct_level":
                val_lower = value.lower()
                if val_lower in error_correction:
                    kwargs["correct_level"] = error_correction[val_lower]
                else:
                    kwargs[key] = value
            elif value.lower() in ("true", "yes", "1"):
                kwargs[key] = True
            elif value.lower() in ("false", "no", "0"):
                kwargs[key] = False
            else:
                try:
                    if "." in value or "e" in value.lower():
                        kwargs[key] = float(value)
                    else:
                        kwargs[key] = int(value)
                except ValueError:
                    kwargs[key] = value
        if opts.style in ("a1", "a1c", "a1p"):
            img = make_fn(data, preset=opts.style, **kwargs)
        elif opts.style in ("a2", "a2c"):
            img = make_fn(data, preset=opts.style, **kwargs)
        elif opts.style == "sp1":
            img = make_fn(data, preset="sp1", **kwargs)
        else:
            img = make_fn(data, **kwargs)
        if opts.output:
            with Path(opts.output).open("wb") as out:
                img.save(out)
        else:
            sys.stdout.flush()
            img.save(sys.stdout.buffer)
        return

    if opts.factory:
        module = default_factories.get(opts.factory, opts.factory)
        try:
            image_factory = get_factory(module)
        except ValueError as e:
            raise_error(str(e))
    else:
        image_factory = None

    qr = qrcode.QRCode(
        error_correction=error_correction[opts.error_correction],
        image_factory=image_factory,
    )

    if args:
        data = args[0]
        data = data.encode(errors="surrogateescape")
    else:
        data = sys.stdin.buffer.read()
    if opts.optimize is None:
        qr.add_data(data)
    else:
        qr.add_data(data, optimize=opts.optimize)

    if opts.output:
        img = qr.make_image()
        with Path(opts.output).open("wb") as out:
            img.save(out)
    else:
        if image_factory is None and (os.isatty(sys.stdout.fileno()) or opts.ascii):
            qr.print_ascii(tty=not opts.ascii)
            return

        kwargs = {}
        aliases: DrawerAliases | None = getattr(
            qr.image_factory, "drawer_aliases", None
        )
        if opts.factory_drawer:
            if not aliases:
                raise_error("The selected factory has no drawer aliases.")
            if opts.factory_drawer not in aliases:
                raise_error(
                    f"{opts.factory_drawer} factory drawer not found."
                    f" Expected {commas(aliases)}"
                )
            drawer_cls, drawer_kwargs = aliases[opts.factory_drawer]
            kwargs["module_drawer"] = drawer_cls(**drawer_kwargs)
        img = qr.make_image(**kwargs)

        sys.stdout.flush()
        img.save(sys.stdout.buffer)


def get_factory(module: str) -> type[BaseImage]:
    if "." not in module:
        raise ValueError("The image factory is not a full python path")
    module, name = module.rsplit(".", 1)
    imp = __import__(module, {}, {}, [name])
    return getattr(imp, name)


def get_drawer_help() -> str:
    help: dict[str, set] = {}

    for alias, module in default_factories.items():
        try:
            image = get_factory(module)
        except ImportError:  # pragma: no cover
            continue
        aliases: DrawerAliases | None = getattr(image, "drawer_aliases", None)
        if not aliases:
            continue
        factories = help.setdefault(commas(aliases), set())
        factories.add(alias)

    return ". ".join(
        f"For {commas(factories, 'and')}, use: {aliases}"
        for aliases, factories in help.items()
    )


def commas(items: Iterable[str], joiner="or") -> str:
    items = tuple(items)
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return f"{', '.join(items[:-1])} {joiner} {items[-1]}"


if __name__ == "__main__":  # pragma: no cover
    main()
