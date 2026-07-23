package database

import (
	"database/sql"
	"fmt"
	"os"

	_ "github.com/go-sql-driver/mysql"
)

type DBConfig struct {
	Host     string
	User     string
	Password string
	DBName   string
}

func envOrDefault(key, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}

func Connect() (*sql.DB, error) {
	config := DBConfig{
            Host:     envOrDefault("MYSQL_HOST", "localhost"),
            User:     envOrDefault("MYSQL_USER", "epic"),
            Password: envOrDefault("MYSQL_PASSWORD", "change_me"),
            DBName:   envOrDefault("MYSQL_DATABASE", "epidemic"),
        }

	dsn := fmt.Sprintf("%s:%s@tcp(%s)/%s?parseTime=true", config.User, config.Password, config.Host, config.DBName)
	db, err := sql.Open("mysql", dsn)
	if err != nil {
		return nil, err
	}
	return db, nil
}

func Query(db *sql.DB, query string, args ...interface{}) (*sql.Rows, error) {
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	return rows, nil
}
