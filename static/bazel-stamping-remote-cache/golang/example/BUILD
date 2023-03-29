load("@io_bazel_rules_go//go:def.bzl", "go_binary", "go_library")

go_binary(
    name = "example",
    srcs = ["main.go"],
    out = "example",
    pure = "on",
    visibility = ["//visibility:public"],
    x_defs = {
        "gitCommit": "{GIT_COMMIT}",
        "buildTimestamp": "{BUILD_TIMESTAMP}",
        "runtime.modinfo": "\n".join([
            "                ",
            "build\tvcs.revision={GIT_COMMIT}",
            "build\tvcs.time=2023-01-01T00:00:00Z",
            "                ",
        ]),
    },
)
