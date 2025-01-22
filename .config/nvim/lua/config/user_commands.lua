local function init_python_logger()
  local lines = {
    "import logging",
    "",
    'logger = logging.getLogger(__name__)',
    'logger.setLevel(logging.DEBUG)',
    'log_formatter = logging.Formatter(',
        '\tfmt="%(asctime)s : %(name)s : %(levelname)s : %(message)s",',
        '\tdatefmt="%H:%M:%S",',
    ')',
    'stream_handler = logging.StreamHandler()',
    'stream_handler.setLevel(logging.INFO)',
    'stream_handler.setFormatter(log_formatter)',
    'logger.addHandler(stream_handler)',
    'file_handler = logging.FileHandler("app.log")',
    'file_handler.setLevel(logging.DEBUG)',
    'file_handler.setFormatter(log_formatter)',
    'logger.addHandler(file_handler)',
  }
  local buf = vim.api.nvim_get_current_buf()
  local row, col = unpack(vim.api.nvim_win_get_cursor(0))
  vim.api.nvim_buf_set_lines(buf, row, row, false, lines)
end
vim.api.nvim_create_user_command("InitPythonLogger", init_python_logger, {})

local function python_native_csv_reader()
  local lines = {
    "import csv",
    'with open("temp.csv", "r", encoding="utf-8") as file:',
    "\tcsv_reader = csv.DictReader(file)",
    "\ttype_map = {",
    '\t\t"dataset": str,',
    '\t\t"time": int,',
    '\t\t"group": str,',
    '\t\t"amount": int,',
    "\t}",
    "\tdata = [",
    "\t\t{colname: type_map[colname](value) for colname, value in row.items()}",
    "\t\tfor row in csv_reader",
    "\t]",
  }
  local buf = vim.api.nvim_get_current_buf()
  local row, col = unpack(vim.api.nvim_win_get_cursor(0))
  vim.api.nvim_buf_set_lines(buf, row, row, false, lines)
end
vim.api.nvim_create_user_command("InitPythonCsvReader", python_native_csv_reader, {})

local function python_native_csv_writer()
  local lines = {
    "import csv",
    'with open("temp.csv", mode="w", encoding="utf-8") as file:',
    "\tcsv_writer = csv.DictWriter(",
    "\t\tfile,",
    '\t\tfieldnames=["name", "surname"],',
    '\t\tdelimiter=",",',
    "\t\tquotechar='\"',",
    "\t\tquoting=csv.QUOTE_MINIMAL,",
    "\t)",
    "\tcsv_writer.writeheader()",
    '\tcsv_writer.writerow({"name": "abraham", "surname": "lincoln"})',
    '\tcsv_writer.writerow({"name": "oscar", "surname": "peterson"})',
  }
  local buf = vim.api.nvim_get_current_buf()
  local row, col = unpack(vim.api.nvim_win_get_cursor(0))
  vim.api.nvim_buf_set_lines(buf, row, row, false, lines)
  -- local row, col = unpack(vim.api.nvim_win_get_cursor(0))
  -- vim.api.nvim_buf_set_lines(0, row - 1, row - 1, true, lines)
end
vim.api.nvim_create_user_command("InitPythonCsvWriter", python_native_csv_writer, {})
