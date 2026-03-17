=============================
Pure python QR Code generator
=============================

Generate QR codes.

A standard install uses pypng_ to generate PNG files and can also render QR
codes directly to the console. A standard install is just::

    pip install qrcode

For more image functionality, install qrcode with the ``pil`` dependency so
that pillow_ is installed and can be used for generating images::

    pip install "qrcode[pil]"

.. _pypng: https://pypi.python.org/pypi/pypng
.. _pillow: https://pypi.python.org/pypi/Pillow


What is a QR Code?
==================

A Quick Response code is a two-dimensional pictographic code used for its fast
readability and comparatively large storage capacity. The code consists of
black modules arranged in a square pattern on a white background. The
information encoded can be made up of any kind of data (e.g., binary,
alphanumeric, or Kanji symbols)

Usage
=====

Command line
------------

Use the installed ``qr`` script to generate a QR code from a string or stdin::

    qr "Some text" > test.png
    qr --output=test.png "Some text"
    qr -o test.png "Some text"

**Options:**

``--output=FILE`` / ``-o FILE``
    Write image to FILE instead of stdout. If the filename ends with ``.svg``
    and you use ``--style`` (a1, a1c, a1p, a2, a2c, or sp1), the output is
    vector SVG; otherwise PNG. C2 does not support SVG. Examples::

        qr --style=a1c "https://example.com" -o qr_a1c.svg
        qr --style=a2 "https://example.com" -o qr_a2.svg
        qr --style=sp1 "https://example.com" -o qr_sp1.svg

``--factory=FACTORY``
    Image factory. Shortcuts: ``pil``, ``png``, ``svg``, ``svg-fragment``,
    ``svg-path``. Default is ``pil`` when Pillow is installed, else ``png``.

``--style=STYLE``
    Qrbtf-style QR code (requires PIL). Choices: ``a1``, ``a1c``, ``a1p``,
    ``a2``, ``a2c``, ``sp1``, ``c2``. Each is a preset; override with ``--opt``.
    Examples::

        qr --style=a1 "https://example.com" -o qr_a1.png
        qr --style=a1c "https://example.com" -o qr_a1c.png
        qr --style=a1c "https://example.com" -o qr_a1c.svg
        qr --style=a2 "https://example.com" -o qr_a2.png
        qr --style=sp1 "https://example.com" -o qr_sp1.png
        qr --style=c2 "https://example.com" -o qr_c2.png

``--opt KEY=VALUE`` / ``-O KEY=VALUE``
    Qrbtf option; repeat to set multiple. Overrides the style preset.
    Numeric values are parsed as int/float. Examples::

        qr --style=a1 --opt content_point_scale=0.5 --opt content_point_type=circle -o qr.png "https://example.com"
        qr --style=a2 -O content_line_type=horizontal -O content_point_scale=0.8 -o qr.png "https://example.com"
        qr --style=a1 -O positioning_point_type=rounded -O content_point_color=#0000ff -o qr.png "https://example.com"

    Common options: ``positioning_point_type`` (square|circle|planet|rounded),
    ``content_point_type`` (square|circle), ``content_point_scale`` (0–1),
    ``content_point_color`` / ``positioning_point_color`` (hex),
    ``content_line_type`` (horizontal|vertical|interlock|radial|tl-br|tr-bl|cross),
    ``content_stroke_width``, ``positioning_point_type`` (dsj|square for SP1),
    ``contrast``, ``brightness``, ``background_path`` (C2). See
    ``qrcode/image/qrbtf/README.md`` for full lists.

    **Background image:** C2 (PNG only) draws the QR on a photo with dithering.
    For SVG (A1, A2, SP1), use ``-O background_path=...`` to embed an image
    behind the QR, ``-O logo_path=...`` for a **center logo**, or ``-O text=...``
    for optional **side text** (top, bottom, left, right). Examples::

        qr --style=c2 -O background_path=/path/to/photo.jpg -O contrast=0.2 -o qr.png "https://example.com"
        qr --style=a1 -O background_path=/path/to/photo.jpg -o qr.svg "https://example.com"
        qr --style=a1 -O logo_path=logo.png -O logo_size=8 -o qr.svg "https://example.com"
        qr --style=a1 -o qr.svg -O "text=Scan me" -O text_position=bottom "https://example.com"

``--error-correction=LEVEL``
    Error correction: ``L`` (7%), ``M`` (15%, default), ``Q`` (25%), ``H`` (30%).

``--box-size=N``
    Module size in pixels (default: 10).

``--border=N``
    Border width in modules (default: 4).

``--optimize=N``
    Optimize encoding for chunks of at least N characters; use 0 to disable.

``--ascii``
    Print ASCII art to stdout even when piping.

``--factory-drawer=DRAWER``
    Use an alternate module drawer (for ``pil`` / styled factories; see help).

Python
------

Or in Python, use the ``make`` shortcut function:

.. code:: python

    import qrcode
    img = qrcode.make('Some data here')
    type(img)  # qrcode.image.pil.PilImage
    img.save("some_file.png")

Advanced Usage
--------------

For more control, use the ``QRCode`` class. For example:

.. code:: python

    import qrcode
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

The ``version`` parameter is an integer from 1 to 40 that controls the size of
the QR Code (the smallest, version 1, is a 21x21 matrix).
Set to ``None`` and use the ``fit`` parameter when making the code to determine
this automatically.

``fill_color`` and ``back_color`` can change the background and the painting
color of the QR, when using the default image factory. Both parameters accept
RGB color tuples.

.. code:: python


    img = qr.make_image(back_color=(255, 195, 235), fill_color=(55, 95, 35))

The ``error_correction`` parameter controls the error correction used for the
QR Code. The following four constants are made available on the ``qrcode``
package:

``ERROR_CORRECT_L``
    About 7% or less errors can be corrected.
``ERROR_CORRECT_M`` (default)
    About 15% or less errors can be corrected.
``ERROR_CORRECT_Q``
    About 25% or less errors can be corrected.
``ERROR_CORRECT_H``.
    About 30% or less errors can be corrected.

The ``box_size`` parameter controls how many pixels each "box" of the QR code
is.

The ``border`` parameter controls how many boxes thick the border should be
(the default is 4, which is the minimum according to the specs).

Qrbtf-style QR codes
--------------------

The ``qrcode.image.qrbtf`` package provides the same visual styles as the
qrbtf frontend: A1 (square/circle/rounded finders and modules), A2 (line-based
content), C2 (image background with contrast/brightness), and SP1 (DSJ finder,
bars, X-marks).

From the command line (requires ``qrcode[pil]``)::

    qr --style=a1 "https://example.com" -o qr_a1.png
    qr --style=a1c "https://example.com" -o qr_a1c.png
    qr --style=a2 "https://example.com" -o qr_a2.png
    qr --style=sp1 "https://example.com" -o qr_sp1.png
    qr --style=c2 "https://example.com" -o qr_c2.png
    qr --style=a1 --error-correction=H -O content_point_scale=0.8 -O content_point_type=rounded -O positioning_point_type=rounded -O content_point_color=#000000 -O positioning_point_color=#000000 -O logo_path=audio1.png -O logo_size=10 "https://demo.example.com/qr/subpath/NW94BVCJELRI" -o qr.svg


In Python, use the ``make_qrbtf_*`` helpers or pass the style image
factories to ``QRCode``::

    from qrcode.image.qrbtf import make_qrbtf_a1, make_qrbtf_a2, make_qrbtf_sp1

    img = make_qrbtf_a1("https://example.com", preset="a1c")
    img.save("qr_a1c.png")

    img = make_qrbtf_a2("https://example.com", preset="a2")
    img.save("qr_a2.png")

    img = make_qrbtf_sp1("https://example.com", preset="sp1")
    img.save("qr_sp1.png")

See ``qrcode/image/qrbtf/README.md`` for options and presets.

Other image factories
=====================

You can encode as SVG, or use a new pure Python image processor to encode to
PNG images.

The Python examples below use the ``make`` shortcut. The same ``image_factory``
keyword argument is a valid option for the ``QRCode`` class for more advanced
usage.

SVG
---

You can create the entire SVG or an SVG fragment. When building an entire SVG
image, you can use the factory that combines as a path (recommended, and
default for the script) or a factory that creates a simple set of rectangles.

From your command line::

    qr --factory=svg-path "Some text" > test.svg
    qr --factory=svg "Some text" > test.svg
    qr --factory=svg-fragment "Some text" > test.svg

Or in Python:

.. code:: python


    import qrcode
    import qrcode.image.svg
    
    method = input("What method? (basic, fragment, path): ")
    
    if method == 'basic':
        # Simple factory, just a set of rects.
        factory = qrcode.image.svg.SvgImage
    elif method == 'fragment':
        # Fragment factory (no standalone header)
        factory = qrcode.image.svg.SvgFragmentImage
    else:
        # Combined path factory, fixes white space that may occur when zooming
        factory = qrcode.image.svg.SvgPathImage
    
    img = qrcode.make('Some data here', image_factory=factory)
    
    img.save('some_file.svg')

Two other related factories are available that work the same, but also fill the
background of the SVG with white::

    qrcode.image.svg.SvgFillImage
    qrcode.image.svg.SvgPathFillImage

The ``QRCode.make_image()`` method forwards additional keyword arguments to the
underlying ElementTree XML library. This helps to fine tune the root element of
the resulting SVG:

.. code:: python

    import qrcode
    qr = qrcode.QRCode(image_factory=qrcode.image.svg.SvgPathImage)
    qr.add_data('Some data')
    qr.make(fit=True)

    img = qr.make_image(attrib={'class': 'some-css-class'})

You can convert the SVG image into strings using the ``to_string()`` method.
Additional keyword arguments are forwarded to ElementTrees ``tostring()``:

.. code:: python

    img.to_string(encoding='unicode')


Pure Python PNG
---------------

If Pillow is not installed, the default image factory will be a pure Python PNG
encoder that uses `pypng`.

You can use the factory explicitly from your command line::

    qr --factory=png "Some text" > test.png

Or in Python:

.. code:: python

    import qrcode
    from qrcode.image.pure import PyPNGImage
    img = qrcode.make('Some data here', image_factory=PyPNGImage)


Styled Image
------------

Works only with versions_ >=7.2 (SVG styled images require 7.4).

.. _versions: https://github.com/lincolnloop/python-qrcode/blob/master/CHANGES.rst#72-19-july-2021

To apply styles to the QRCode, use the ``StyledPilImage`` or one of the
standard SVG_ image factories. These accept an optional ``module_drawer``
parameter to control the shape of the QR Code.

These QR Codes are not guaranteed to work with all readers, so do some
experimentation and set the error correction to high (especially if embedding
an image).

Other PIL module drawers:

    .. image:: doc/module_drawers.png

For SVGs, use ``SvgSquareDrawer``, ``SvgCircleDrawer``,
``SvgPathSquareDrawer``, or ``SvgPathCircleDrawer``.

These all accept a ``size_ratio`` argument which allows for "gapped" squares or
circles by reducing this less than the default of ``Decimal(1)``.


The ``StyledPilImage`` additionally accepts an optional ``color_mask``
parameter to change the colors of the QR Code, and an optional
``embedded_image_path`` to embed an image in the center of the code.

Other color masks:

    .. image:: doc/color_masks.png

Here is a code example to draw a QR code with rounded corners, radial gradient
and an embedded image:

.. code:: python

    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer
    from qrcode.image.styles.colormasks import RadialGradiantColorMask

    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data('Some data')

    img_1 = qr.make_image(image_factory=StyledPilImage, module_drawer=RoundedModuleDrawer())
    img_2 = qr.make_image(image_factory=StyledPilImage, color_mask=RadialGradiantColorMask())
    img_3 = qr.make_image(image_factory=StyledPilImage, embedded_image_path="/path/to/image.png")

Examples
========

Get the text content from `print_ascii`:

.. code:: python

    import io
    import qrcode
    qr = qrcode.QRCode()
    qr.add_data("Some text")
    f = io.StringIO()
    qr.print_ascii(out=f)
    f.seek(0)
    print(f.read())

The `add_data` method will append data to the current QR object. To add new data by replacing previous content in the same object, first use clear method:

.. code:: python

    import qrcode
    qr = qrcode.QRCode()
    qr.add_data('Some data')
    img = qr.make_image()
    qr.clear()
    qr.add_data('New data')
    other_img = qr.make_image()

Pipe ascii output to text file in command line::

    qr --ascii "Some data" > "test.txt"
    cat test.txt

Alternative to piping output to file to avoid PowerShell issues::

    # qr "Some data" > test.png
    qr --output=test.png "Some data"
