Examples from Go by Example (awesome stuff)

https://gobyexample.com/

Interesting example of `WaitGroup` + Semaphore in Weaviate `generative-search` modules (Channel with `maximumNumberOfGoroutines` capacity)

```golang
func (p *GenerateProvider) generatePerSearchResult(ctx context.Context, in []search.Result, prompt string, cfg moduletools.ClassConfig) ([]search.Result, error) {
	var wg sync.WaitGroup
	sem := make(chan struct{}, p.maximumNumberOfGoroutines)
	for i, result := range in {
		wg.Add(1) // Inidicates that there is one more operation that needs to be completed
		textProperties := p.getTextProperties(result, nil)
		go func(result search.Result, textProperties map[string]string, i int) {
			sem <- struct{}{}
			defer wg.Done() // decrements WaitGroup counter by 1.
			defer func() { <-sem }()
			generateResult, err := p.client.GenerateSingleResult(ctx, textProperties, prompt, cfg)
			p.setIndividualResult(in, i, generateResult, err)
		}(result, textProperties, i)
	}
	wg.Wait() // ensures that the concurrent operations finish before proceeding
	return in, nil
}
```

Analysis of above:
In Golang, semaphores are not provided as a built-in construct, but they can be implemented using channels. Channels are used for communication between goroutines by creating a channel with a capacity, you create a semaphore. The semaphore limits the number of **concurrent goroutines**. When you try to send an element to a buffered channel that is already full, the operation will "block" - this means that the goroutine which is attempting to send the element will pause and wait. It won't continue executing until there's space available in the channel.
