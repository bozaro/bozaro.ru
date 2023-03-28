package bar

import "github.com/bozaro/example/foo"

func Bar() int {
	var f foo.Foo
	return f.Bar()
}
