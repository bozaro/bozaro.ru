def _stamping_impl(ctx):
    args = ctx.actions.args()
    args.add("--template", ctx.file.src)
    args.add("--output", ctx.outputs.out)
    inputs = [ctx.file.src]
    if ctx.attr.private_stamp_detect:
        args.add("--stamp", ctx.version_file)  # volatile-status.txt
        args.add("--stamp", ctx.info_file)  # stable-status.txt
        inputs += [
            ctx.version_file,
            ctx.info_file,
        ]
    ctx.actions.run(
        mnemonic = "Example",
        inputs = depset(inputs),
        outputs = [ctx.outputs.out],
        executable = ctx.executable._stamping_py,
        arguments = [args],
    )
    return [
        DefaultInfo(
            files = depset([ctx.outputs.out]),
        ),
    ]

stamping_impl = rule(
    implementation = _stamping_impl,
    doc = "Stamping rule example",
    attrs = {
        "src": attr.label(mandatory = True, allow_single_file = True),
        "out": attr.output(mandatory = True),
        # Is --stamp set on the command line?
        "private_stamp_detect": attr.bool(default = False),
        "_stamping_py": attr.label(
            default = Label("//example:stamping"),
            cfg = "exec",
            executable = True,
            allow_files = True,
        ),
    },
)

def stamping(name, **kwargs):
    stamping_impl(
        name = name,
        private_stamp_detect = select({
            "//example:stamp_detect": True,
            "//conditions:default": False,
        }),
        **kwargs
    )
