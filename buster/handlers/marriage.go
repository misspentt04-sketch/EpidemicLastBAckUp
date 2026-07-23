package handlers

import (
	"buster/models"
	"database/sql"
)

func GetTopMarriageExp(db *sql.DB, chatID int) ([]models.MarriageInfoExp, error) {
	query := `
  SELECT MAX(m.husband_id) AS max_husband_id, MAX(m.wife_id) AS max_wife_id,
         MIN(u1.full_name) AS full_name1, MIN(u2.full_name) AS full_name2,
         MIN(b1.bio_experience) AS bio_experience1, MIN(b2.bio_experience) AS bio_experience2
  FROM Marriages m
  JOIN Lab b1 ON m.husband_id = b1.lab_id
  JOIN Lab b2 ON m.wife_id = b2.lab_id
  JOIN Users u1 ON u1.id = m.husband_id
  JOIN Users u2 ON u2.id = m.wife_id
  WHERE m.chat_id=?
  GROUP BY b1.bio_experience + b2.bio_experience
  ORDER BY b1.bio_experience + b2.bio_experience DESC;
 `

	rows, err := db.Query(query, chatID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []models.MarriageInfoExp
	for rows.Next() {
		var info models.MarriageInfoExp
		err := rows.Scan(&info.MaxHusbandID, &info.MaxWifeID, &info.FullName1, &info.FullName2, &info.BioExperience1, &info.BioExperience2)
		if err != nil {
			return nil, err
		}
		results = append(results, info)
	}

	return results, nil
}

func GetTopMarriageExpSMS(db *sql.DB, chatID int) ([]models.MarriageInfoSms, error) {
	query := `
	SELECT u1.full_name AS full_name1, u2.full_name AS full_name2, m.husband_id, m.wife_id, sms_in_marriage 
	FROM Marriages m
	INNER JOIN Users u1 ON u1.id = m.husband_id
	INNER JOIN Users u2 ON u2.id = m.wife_id 
	WHERE chat_id = ? 
	ORDER BY sms_in_marriage DESC;`

	rows, err := db.Query(query, chatID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var results []models.MarriageInfoSms
	for rows.Next() {
		var info models.MarriageInfoSms
		err := rows.Scan(&info.FullName1, &info.FullName2, &info.MaxHusbandID, &info.MaxWifeID, &info.MarriageSms)
		if err != nil {
			return nil, err
		}
		results = append(results, info)
	}

	if err = rows.Err(); err != nil {
		return nil, err
	}

	return results, nil
}
