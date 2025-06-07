package main

import (
	"encoding/json"
	"log"
	"net/http"
	"time"

	"database/sql"

	"github.com/gorilla/mux"
	_ "github.com/lib/pq"
)

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
	db, err = sql.Open("postgres", "postgres://user:secret@localhost:5433/taskdb?sslmode=disable")
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	// Test the connection
	err = db.Ping()
	if err != nil {
		log.Fatal(err)
	}

	// Initialize router
	r := mux.NewRouter()

	// Define routes
	r.HandleFunc("/tasks", getTasksByDate).Methods("GET")

	// Start server
	log.Println("Server starting on :8080")
	log.Fatal(http.ListenAndServe(":8080", r))
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
