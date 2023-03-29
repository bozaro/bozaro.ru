load("@io_bazel_rules_go//go:def.bzl", "go_library", "go_test")

# Tested package
go_library(
    name = "foo",
    srcs = ["foo.go"],
    importpath = "github.com/bozaro/foo",
    visibility = ["//visibility:public"],
)

# Original tests
# Long build time, but `foo_test_test.go` can use symbols from `foo_test.go`
#go_test(
#    name = "foo_test",
#    srcs = [
#        "foo_test.go", # package foo
#        "foo_test_test.go", # package foo_test
#    ],
#    embed = [":foo"],
#    importpath = "github.com/bozaro/foo",
#    deps = ["//bar"],
#)

# Internal tests (`foo_test`) package
go_test(
    name = "foo_interal_test",
    srcs = ["foo_test.go"],  # package foo
    embed = [":foo"],
    importpath = "github.com/bozaro/foo",
)

# External tests (`foo_test`) package
# Fast build time, but `foo_test_test.go` can't use symbols from `foo_test.go`
go_test(
    name = "foo_external_test",
    srcs = ["foo_test_test.go"],  # package foo_test
    importpath = "github.com/bozaro/foo_test",
    deps = [
        ":foo",
        "//bar",
    ],
)
