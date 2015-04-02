package optimizer

import "fmt"

type Occasion struct {
	Participants []uint64
	FixIndicators []uint64
	GroupSizes []uint64
}


type Conference struct {
	Occasions []Occasion 
	Weights []int64
	ExecutionTime float64
}


func main() {
	fmt.Println("Hello!")
}

//func CreateConference() {
	// participants per occasion, one int per occasion
	// table sizes per occasion, one int per table per occasion
		
//}

func Optimize(conference *Conference) float64 {
	conference2 := Conference{
		Occasions: []Occasion{},
		Weights: []int64{},
		ExecutionTime: 0.0};


	return conference2.ExecutionTime;
}
