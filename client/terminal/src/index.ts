import { Command } from 'commander';
import axios from 'axios';
import chalk from 'chalk';
import { format } from 'date-fns';

interface Task {
  id: number;
  date: string;
  title: string;
  description: string;
  priority: number;
  estimate_minutes: number;
  created_at: string;
  updated_at: string;
}

const API_URL = 'http://localhost:8080';

const program = new Command();

program
  .name('tasks-cli')
  .description('CLI for managing tasks')
  .version('1.0.0');

program
  .command('list')
  .description('List tasks for a specific date')
  .argument('<date>', 'date in YYYY-MM-DD format')
  .action(async (date: string) => {
    try {
      const response = await axios.get<Task[]>(`${API_URL}/tasks`, {
        params: { date }
      });

      if (response.data.length === 0) {
        console.log(chalk.yellow(`No tasks found for ${date}`));
        return;
      }

      console.log(chalk.blue(`\nTasks for ${date}:`));
      console.log(chalk.gray('─'.repeat(80)));

      response.data.forEach((task) => {
        const priorityColor = task.priority === 0 ? chalk.red :
                            task.priority === 1 ? chalk.yellow :
                            task.priority === 2 ? chalk.blue :
                            chalk.green;

        console.log(chalk.bold(`[${task.id}] ${task.title}`));
        console.log(`Priority: ${priorityColor(`P${task.priority}`)}`);
        console.log(`Estimate: ${task.estimate_minutes} minutes`);
        if (task.description) {
          console.log(`Description: ${task.description}`);
        }
        console.log(chalk.gray('─'.repeat(80)));
      });

    } catch (error) {
      if (axios.isAxiosError(error)) {
        console.error(chalk.red('Error:'), error.response?.data || error.message);
      } else {
        console.error(chalk.red('Error:'), error);
      }
      process.exit(1);
    }
  });

program.parse(); 