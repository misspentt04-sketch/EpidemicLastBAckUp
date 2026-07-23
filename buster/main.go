package main

import (
	"encoding/json"
	"log"
	"os"

	"buster/handlers"

	"buster/database"
)

type InputData struct {
	Type   string `json:"type"`
	ChatID int    `json:"chat_id"`
	UserID int    `json:"user_id,omitempty"`
}

func main() {

	var input InputData
	err := json.NewDecoder(os.Stdin).Decode(&input)
	if err != nil {
		log.Fatalf("Error decoding input: %v", err)
	}

	db, err := database.Connect()
	if err != nil {
		log.Fatalf("Error connecting to database: %v", err)
	}
	defer db.Close()

	var result interface{}
	switch input.Type {

	case "top_exp":
		result, err = handlers.GetTopMarriageExp(db, input.ChatID)
	case "top_sms":
		result, err = handlers.GetTopMarriageExpSMS(db, input.ChatID)
	case "top_marriage":
		result, err = handlers.GetTopMarriageTime(db, input.ChatID)
	case "user_marriage":
		result, err = handlers.UserMarriageTime(db, input.ChatID, input.UserID)

	default:
		log.Fatalf("Unknown type: %s", input.Type)
	}

	if err != nil {
		log.Fatalf("Error executing query: %v", err)
	}

	json.NewEncoder(os.Stdout).Encode(result)
}
