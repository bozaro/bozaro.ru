go_repository(
    importpath = "github.com/google/tink/go",
    patch_cmds = ["find . -name BUILD.bazel -delete"],
    # ...
)
