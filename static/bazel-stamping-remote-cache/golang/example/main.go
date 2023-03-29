package main

import (
	"fmt"
	"runtime/debug"
	"strconv"
	"time"
)

var gitCommit string
var buildTimestamp string

func main() {
	fmt.Println("Stamping example")
	if buildInfo, ok := debug.ReadBuildInfo(); ok {
		fmt.Println("=== Begin build info ===")
		fmt.Println(buildInfo)
		fmt.Println("=== End build info ===")
		for _, setting := range buildInfo.Settings {
			if setting.Key == "vcs.revision" {
				fmt.Println("Found go build revision:", setting.Value)
			}
			if setting.Key == "vcs.time" {
				fmt.Println("Found go build timestamp:", setting.Value)
			}
		}
	}
	if gitCommit != "" {
		fmt.Println("Found x_defs revision:", gitCommit)
	}
	if buildTimestamp != "" {
		ts, _ := strconv.ParseInt(buildTimestamp, 10, 64)
		fmt.Println("Found x_defs build timestamp:", time.Unix(ts, 0).UTC().Format(time.RFC3339Nano))
	}
}
