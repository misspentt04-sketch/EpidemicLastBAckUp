package funcs

import (
	"fmt"
	"strings"
	"time"
)

func CalculateAnniversary(timeCreated time.Time) (currentAnniversary, nextAnniversary string, daysLeft int, durationFormatted string) {
	now := time.Now()
	marriageDuration := now.Sub(timeCreated)
	monthsTotal := int(marriageDuration.Hours() / 24 / 30)

	currentAnniversary = "молодожёны"
	nextAnniversary = ""
	daysLeft = 0

	for months, name := range WeddingAnniversaries {
		if months <= monthsTotal {
			currentAnniversary = name
		}
		if months > monthsTotal && (nextAnniversary == "" || months < daysLeft) {
			nextAnniversary = name
			daysLeft = months - monthsTotal
		}
	}

	durationFormatted = FormatDuration(marriageDuration)

	return currentAnniversary, nextAnniversary, daysLeft * 30, durationFormatted
}

func Pluralize(value int, singular string, plural []string) string {

	if value%100 >= 11 && value%100 <= 14 {
		return fmt.Sprintf("%d %s", value, plural[1])
	}

	switch value % 10 {
	case 1:
		return fmt.Sprintf("%d %s", value, singular)
	case 2, 3, 4:
		return fmt.Sprintf("%d %s", value, plural[0])
	default:
		return fmt.Sprintf("%d %s", value, plural[1])
	}
}

func FormatDuration(duration time.Duration) string {
	years := int(duration.Hours() / 24 / 365)
	months := int((duration.Hours() / 24 / 30) - float64(years*12))
	days := int(duration.Hours()/24) - years*365 - months*30
	hours := int(duration.Hours()) % 24
	minutes := int(duration.Minutes()) % 60
	seconds := int(duration.Seconds()) % 60

	var sb strings.Builder
	if years > 0 {
		sb.WriteString(Pluralize(years, "год", []string{"года", "лет"}))
		if months > 0 {
			sb.WriteString(", ")
			sb.WriteString(Pluralize(months, "месяц", []string{"месяца", "месяцев"}))
		}
	} else if months > 0 {
		sb.WriteString(Pluralize(months, "месяц", []string{"месяца", "месяцев"}))
		if days > 0 {
			sb.WriteString(", ")
			sb.WriteString(Pluralize(days, "день", []string{"дня", "дней"}))
		}
	} else if days > 0 {
		sb.WriteString(Pluralize(days, "день", []string{"дня", "дней"}))
		if hours > 0 {
			sb.WriteString(", ")
			sb.WriteString(Pluralize(hours, "час", []string{"часа", "часов"}))
		}
	} else if hours > 0 {
		sb.WriteString(Pluralize(hours, "час", []string{"часа", "часов"}))
		if minutes > 0 {
			sb.WriteString(", ")
			sb.WriteString(Pluralize(minutes, "минута", []string{"минуты", "минут"}))
		}
	} else if minutes > 0 {
		sb.WriteString(Pluralize(minutes, "минута", []string{"минуты", "минут"}))
		if seconds > 0 {
			sb.WriteString(", ")
			sb.WriteString(Pluralize(seconds, "секунда", []string{"секунды", "секунд"}))
		}
	} else if seconds > 0 {
		sb.WriteString(Pluralize(seconds, "секунда", []string{"секунды", "секунд"}))
	} else {
		return "0 секунд"
	}

	return sb.String()
}

var WeddingAnniversaries = map[int]string{
	1:  "бумажная свадьба",
	2:  "кожаная свадьба",
	3:  "льняная свадьба",
	4:  "деревянная свадьба",
	5:  "чугунная свадьба",
	6:  "медная свадьба",
	7:  "жестяная свадьба",
	8:  "фаянсовая свадьба",
	9:  "оловянная (янтарная) свадьба",
	10: "стальная свадьба",
	11: "никелевая свадьба",
	12: "кружевная (шерстяная) свадьба",
	13: "агатовая свадьба",
	14: "стеклянная свадьба",
	15: "фарфоровая свадьба",
	16: "серебряная свадьба",
	17: "жемчужная свадьба",
	18: "полотняная (льняная, коралловая) свадьба",
	19: "рубиновая свадьба",
	20: "сапфировая свадьба",
	21: "золотая свадьба",
	22: "изумрудная свадьба",
	23: "бриллиантовая (платиновая) свадьба",
	24: "железная свадьба",
	25: "благодатная свадьба",
	26: "коронная свадьба",
	27: "бедроковая свадьба",
}
