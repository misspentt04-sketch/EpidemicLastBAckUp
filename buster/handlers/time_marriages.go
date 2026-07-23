package handlers

import (
	"buster/funcs"
	"buster/models"
	"database/sql"
	"fmt"
	"time"
)

func GetTopMarriageTime(db *sql.DB, chatID int) ([]models.MarriageInfoTime, error) {
	query := `
  SELECT u1.full_name AS full_name1, u2.full_name AS full_name2, m.husband_id, m.wife_id, time_created 
  FROM Marriages m
  INNER JOIN Users u1 ON u1.id = m.husband_id
  INNER JOIN Users u2 ON u2.id = m.wife_id 
  WHERE chat_id = ? 
  ORDER BY time_created ASC; `

	rows, err := db.Query(query, chatID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []models.MarriageInfoTime
	for rows.Next() {
		var info models.MarriageInfoTime
		var timeCreatedUnix int64
		err := rows.Scan(&info.FullName1, &info.FullName2, &info.MaxHusbandID, &info.MaxWifeID, &timeCreatedUnix)
		if err != nil {
			return nil, err
		}

		timeCreated := time.Unix(timeCreatedUnix, 0)

		info.CurrentAnniversary, info.NextAnniversary, info.DaysLeft, info.DurationFormatted = funcs.CalculateAnniversary(timeCreated)
		info.TimeCreatedFormatted = timeCreated.Format("02.01.2006")

		results = append(results, info)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return results, nil
}

func UserMarriageTime(db *sql.DB, chatID int, UserID int) ([]models.UserMarriageInfoTime, error) {
	query :=
		`SELECT u1.full_name AS full_name1, u2.full_name AS full_name2, 
         m.husband_id, m.wife_id, time_created, description, sms_in_marriage, marry_sticker 
    FROM Marriages m
    INNER JOIN Users u1 ON u1.id = m.husband_id
    INNER JOIN Users u2 ON u2.id = m.wife_id
    WHERE chat_id = ? AND (m.husband_id = ? OR m.wife_id = ?)`

	rows, err := db.Query(query, chatID, UserID, UserID)
	if err != nil {
		return nil, fmt.Errorf("error executing query: %w", err)
	}
	defer rows.Close()

	var marriages []models.UserMarriageInfoTime
	for rows.Next() {
		var marriage models.UserMarriageInfoTime
		var timeCreatedUnix int64
		var description sql.NullString

		err := rows.Scan(&marriage.FullName1, &marriage.FullName2, &marriage.MaxHusbandID, &marriage.MaxWifeID, &timeCreatedUnix, &description, &marriage.SmsInMarriage, &marriage.MarrySticker)
		if err != nil {
			return nil, fmt.Errorf("error scanning row: %w", err)
		}

		timeCreated := time.Unix(timeCreatedUnix, 0)
		marriage.TimeCreatedFormatted = timeCreated.Format("02.01.2006")
		marriage.TimeCreated = timeCreatedUnix

		marriage.CurrentAnniversary, marriage.NextAnniversary, marriage.DaysLeft, marriage.DurationFormatted = funcs.CalculateAnniversary(timeCreated)
		marriage.Description = description.String

		marriages = append(marriages, marriage)
	}

	if err = rows.Err(); err != nil {
		return nil, fmt.Errorf("error with rows: %w", err)
	}

	return marriages, nil
}
