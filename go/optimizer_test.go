package optimizer

import "testing"
import "fmt"
import "optimizer"

func TestOptimizeOnePersonConference(t *testing.T) {
	fmt.Println("Testing!");
	conference := optimizer.Conference{
		Occasions: []optimizer.Occasion{optimizer.Occasion{
			Participants: []uint64{1, 2, 3}, 
			FixIndicators: []uint64{0, 1, 0},
			GroupSizes: []uint64{3, 4, 5}}},
		Weights: []int64{6, 6, 6},
		ExecutionTime: 0.0};

	optimizer.Optimize(&conference);
}
