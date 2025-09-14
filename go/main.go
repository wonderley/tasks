package main

import (
	_ "embed"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"database/sql"

	"github.com/gorilla/mux"
	_ "github.com/jackc/pgx/v5/stdlib" // Import for pgx driver
)

//go:embed model/schema.sql
var schemaSQL string

type Task struct {
	Id              int       `json:"id"`
	Date            time.Time `json:"date"`
	Title           string    `json:"title"`
	Description     string    `json:"description"`
	Priority        int       `json:"priority"`
	EstimateMinutes int       `json:"estimate_minutes"`
	CreatedAt       time.Time `json:"created_at"`
	UpdatedAt       time.Time `json:"updated_at"`
}

var db *sql.DB

func main() {
	// Initialize database connection
	var err error
	// Allow override via env var
	dsn := os.Getenv("DATABASE_URL")
	if dsn == "" {
		dsn = "postgres://user:secret@localhost:5433/taskdb?sslmode=disable"
	}

	db, err = sql.Open("pgx", dsn)
	if err != nil {
		log.Fatalf("open: %v", err)
	}
	defer db.Close()

	// Test the connection
	err = db.Ping()
	if err != nil {
		log.Fatal(err)
	}

	// Apply schema migrations contained in schema.sql
	if _, err := db.Exec(schemaSQL); err != nil {
		log.Fatalf("schema apply failed: %v", err)
	}

	// Initialize router
	r := mux.NewRouter()

	// Define routes
	r.HandleFunc("/tasks", getTasksByDate).Methods("GET")

	// Start server
	port := os.Getenv("PORT")
	if port == "" {
		port = "7070"
	}
	addr := ":" + port
	log.Println("Server starting on", addr)
	log.Fatal(http.ListenAndServe(addr, r))
}

func getTasksByDate(w http.ResponseWriter, r *http.Request) {
	dateStr := r.URL.Query().Get("date")
	if dateStr == "" {
		http.Error(w, "date parameter is required", http.StatusBadRequest)
		return
	}

	date, err := time.Parse("2006-01-02", dateStr)
	if err != nil {
		http.Error(w, "invalid date format. Use YYYY-MM-DD", http.StatusBadRequest)
		return
	}

	rows, err := db.Query(`
		SELECT id, date, title, description, priority, estimate_minutes, created_at, updated_at
		FROM tasks
		WHERE date = $1
		ORDER BY priority, created_at`, date)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var tasks []Task
	for rows.Next() {
		var task Task
		err := rows.Scan(
			&task.Id,
			&task.Date,
			&task.Title,
			&task.Description,
			&task.Priority,
			&task.EstimateMinutes,
			&task.CreatedAt,
			&task.UpdatedAt,
		)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		tasks = append(tasks, task)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(tasks)
}
