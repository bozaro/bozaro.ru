package main

import (
	"fmt"
	"net"
	"os"
	"time"
)

const timeFormat = "15:04:05.999"

func main() {
	address := os.Args[1]
	last := ""
	ticker := time.NewTicker(time.Millisecond * 100)
	t := time.Now()
	fmt.Printf("%s: === %s\n", t.Format(timeFormat), address)
	for {
		conn, err := net.DialTimeout("tcp", address, time.Millisecond*100)
		var msg string
		if conn != nil {
			msg = fmt.Sprintf("connected (%s)", conn.RemoteAddr())
			_ = conn.Close()
		}
		if err != nil {
			msg = err.Error()
		}
		if last != msg {
			now := time.Now()
			if last != "" {
				fmt.Printf("%s: --- %s: %v\n", now.Format(timeFormat), last, now.Sub(t))
			}
			last = msg
			fmt.Printf("%s: +++ %s\n", now.Format(timeFormat), last)
			t = now
		}
		<-ticker.C
	}
}
