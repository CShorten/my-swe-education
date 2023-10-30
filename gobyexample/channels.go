package main

import "fmt"

func main() {
  messages := make(chan string)
  go func() { message <- "ping" }()
  msg := <- messages
  fmt.Println(msg)
}

/*
Channels are the pipes that connect concurrent goroutines.
You can send values into channels from one goroutine and receive those values into another goroutine.

The <-channel syntax receives a value from the channel.

By default sends and receives block until both the sender and receiver are ready.
This property allowed us to wait at the end of our program for the "ping" without having to use any other synchronization.
*/
