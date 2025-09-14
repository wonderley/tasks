import { Command } from 'commander';
import axios from 'axios';
import chalk from 'chalk';
import { format } from 'date-fns';
import readline from 'node:readline';

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

const API_URL = 'http://localhost:7070';

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

      if (!response.data?.length) {
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
      // Let caller decide whether to exit; in REPL we don't want to exit the process.
      throw error;
    }
  });

function tokenizeCommand(input: string): string[] {
  const tokens: string[] = [];
  let current = '';
  let inSingle = false;
  let inDouble = false;
  let escape = false;
  for (let i = 0; i < input.length; i++) {
    const ch = input[i];
    if (escape) {
      current += ch;
      escape = false;
      continue;
    }
    if (ch === '\\') {
      escape = true;
      continue;
    }
    if (ch === "'" && !inDouble) {
      inSingle = !inSingle;
      continue;
    }
    if (ch === '"' && !inSingle) {
      inDouble = !inDouble;
      continue;
    }
    if (!inSingle && !inDouble && /\s/.test(ch)) {
      if (current.length > 0) {
        tokens.push(current);
        current = '';
      }
      continue;
    }
    current += ch;
  }
  if (current.length > 0) tokens.push(current);
  return tokens;
}

async function startInteractiveMode(): Promise<void> {
  // Prevent Commander from exiting the process on errors/help during REPL usage
  program.exitOverride();

  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
    prompt: chalk.green('tasks> '),
    historySize: 1000,
    terminal: true,
  });

  console.log(chalk.gray('Interactive mode. Type "help" for usage, "exit" to quit.'));
  rl.prompt();

  rl.on('line', async (line: string) => {
    const trimmed = line.trim();
    if (!trimmed) {
      rl.prompt();
      return;
    }
    if (trimmed === 'exit' || trimmed === 'quit') {
      rl.close();
      return;
    }
    if (trimmed === 'help') {
      console.log(program.helpInformation());
      rl.prompt();
      return;
    }
    const args = tokenizeCommand(trimmed);
    try {
      // Reuse commander command handlers exactly as CLI by parsing user-provided args
      await program.parseAsync(args, { from: 'user' });
    } catch (err) {
      // Commander throws on exitOverride; print message and continue
      if (err && typeof err === 'object' && 'message' in (err as any)) {
        console.error(chalk.red((err as any).message));
      } else {
        console.error(chalk.red(String(err)));
      }
    }
    rl.prompt();
  });

  await new Promise<void>((resolve) => rl.on('close', () => resolve()));
}

async function run(): Promise<void> {
  if (process.argv.length <= 2) {
    await startInteractiveMode();
    return;
  }
  await program.parseAsync(process.argv);
}

run().catch((err) => {
  console.error(chalk.red('Fatal error:'), err);
  process.exit(1);
});