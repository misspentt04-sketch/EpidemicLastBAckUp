package models

type MarriageInfoExp struct {
	MaxHusbandID   int    `json:"husband_id"`
	MaxWifeID      int    `json:"wife_id"`
	FullName1      string `json:"full_name1"`
	FullName2      string `json:"full_name2"`
	BioExperience1 int    `json:"bio_experience1"`
	BioExperience2 int    `json:"bio_experience2"`
}

type MarriageInfoSms struct {
	MaxHusbandID int    `json:"husband_id"`
	MaxWifeID    int    `json:"wife_id"`
	FullName1    string `json:"full_name1"`
	FullName2    string `json:"full_name2"`
	MarriageSms  string `json:"marriage_sms"`
}

type MarriageInfoTime struct {
	MaxHusbandID         int    `json:"husband_id"`
	MaxWifeID            int    `json:"wife_id"`
	FullName1            string `json:"full_name1"`
	FullName2            string `json:"full_name2"`
	CurrentAnniversary   string `json:"current_anniversary"`
	NextAnniversary      string `json:"next_anniversary"`
	DaysLeft             int    `json:"days_left"`
	DurationFormatted    string `json:"duration_formatted"`
	TimeCreatedFormatted string `json:"time_created_formatted"`
}

type UserMarriageInfoTime struct {
	MaxHusbandID         int    `json:"husband_id"`
	MaxWifeID            int    `json:"wife_id"`
	FullName1            string `json:"full_name1"`
	FullName2            string `json:"full_name2"`
	CurrentAnniversary   string `json:"current_anniversary"`
	NextAnniversary      string `json:"next_anniversary"`
	DaysLeft             int    `json:"days_left"`
	DurationFormatted    string `json:"duration_formatted"`
	TimeCreatedFormatted string `json:"time_created_formatted"`
	TimeCreated          int64  `json:"time_created"`
	Description          string `json:"description"`
	SmsInMarriage        int    `json:"sms_in_marriage"`
	MarrySticker         string `json:"marry_sticker"`
}
