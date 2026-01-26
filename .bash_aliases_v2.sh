alias poetry_run_pylint_recursive='poetry run pylint --rcfile .pylintrc --recursive=y .'

alias cursor_helper='echo "
# anthropic harness agents share context through:
- git logs
- README.md
- docs/PRD.md
- docs/architecture_design.md
- docs/adr/<adr-num>-<adr-name>.md
- docs/epics.md
- docs/current_epic/epic_requirements.md (temporary)
- docs/current_epic/dev_notes.md         (temporary)
- docs/current_epic/user_stories.json    (temporary)

# greenfield anthropic harness agents #
           /discuss_prd
              Creates the Product Requirements Document through a long chat and 
                saves it to docs/PRD.md
(optional) /discuss_architecture
              Creates the Architecture Design Document (ADD) through a long chat and 
                saves it to docs/architecture_design.md
          /harness_scaffold_project
              Agent reads README.md, docs/PRD.md, docs/architecture_design.md
              Creates docs/adr/ (and adds a note and link to it in project 
                root README.md)
              Adds section to README.md explaining required format of an entry 
                in /docs/adr/
              Creates the scaffold of project folders based on the decisions in 
                docs/PRD.md and docs/architecture_design.md
              Populates README.md
              If it made any technical decisions, agent adds an ADR(s) 
                to /docs/adr/<adr-num>-<adr-name>.md
              Does a git commit
            <now proceed to "brownfield anthropic harness agents">

# brownfield anthropic harness agents #
(optional) /harness_scaffold_project
              Same as in "greenfield anthropic harness agents" but user can choose 
                to omit steps
              This only needs to be run in a brownfield codebase (i.e. not 
                coming straight from a run of "greenfield anthropic harness agents")
           /harness_discuss_epic
              Agent reads all context docs:
                - README.md
                - docs/PRD.md
                - docs/architecture_design.md
                - docs/adr/*.md
              Creates folder docs/current_epic/ (clears it out if it already exists)
              Adds docs/current_epic/ to .gitignore (if its not already there)
              Adds docs/current_epic/dev_notes.md
              Creates docs/current_epic/task_requirements.md through a brief chat 
                through the required task
(optional) /harness_research_epic
                Agent explores the codebase and suggests different approaches to 
                  approaching the epic (or a specific piece of it)
                A final approach is decided upon and this information is added into 
                  docs/current_epic/epic_requirements.md
           /harness_plan_epic
              Agent reads all context docs:
                - README.md
                - docs/PRD.md
                - docs/architecture_design.md
                - docs/adr/*.md
                - docs/current_epic/epic_requirements.md
              Agent explores the codebase. 
              Agent partitions the epic into self-contained user stories (units 
                of dev work) and writes these to 
                docs/current_epic/user_stories.json in a standardised format.
           /harness_code_next_user_story
              Agent asks what the user would like coded (default is next user 
                story marked as NOT_STARTED in 
                docs/current_epic/user_stories.json)
              Agent reads all context docs:
                - README.md
                - docs/PRD.md
                - docs/architecture_design.md
                - docs/adr/*.md
                - docs/epics.md
                - docs/current_epic/epic_requirements.md
                - docs/current_epic/user_stories.json
                - other docs which look useful (asks user permission first)
              Agent explores the codebase. 
              If it can, agent runs the application and full test suite (to 
                see that we are starting off with a working app)
              Agent writes the code
              Agent marks the feature as COMPLETED in docs/current_epic/user_stories.json
              Agent can update README.md, docs/adr/, docs/current_epic/dev_notes.md
              Agent does a git commit
(optional) /harness_code_review
              Same as /harness_code_next_user_story agent except that the agent reviews 
                the feature most recently marked as COMPLETED (or something
                else that the user requests)
              Agent applies fixes using TDD
              Agent can update README.md, docs/adr/, docs/current_epic/dev_notes.md
              Agent does a git commit
(optional)  /harness_clean_up
              Move /docs/current_epic/ to /docs/past_epics/{{ epic_num }}_{{ epic_name }}/

# greenfield dexter horthy workflow #
TODO

# brownfield dexter horthy workflow #
TODO
"'

alias docker_helper='echo "
  # Build image using definition from file named \`Dockerfile\` in current folder #
  docker build --tag my_image_name .

  # Run image \`my_image_name\` interactively (i.e. enter the running container and give me a bash terminal) #
  docker run -it --name my_container_name my_image_name bash

  # Stop the container \`my_container_name\` (running image \`my_image_name\`) #
  # (stops container but state persists i.e. created files will still be there when the container is started again) #
  docker stop my_container_name

  # Start the stopped container again #
  docker start my_container_name 

  # List all running containers #
  docker ps

  # Go into the running container again #
  # (NOTE: there is also \`docker exec\` - go read about the differences) #
  docker attach my_container_name

  # Delete the container \`my_container_name\` #
  # i.e. free up resources by erasing the container completely #
  docker rm my_container_name
"'

# docling #
alias docling_helper='echo "
  # with explicit settings (defaults explicitly shown) #
  uv run docling \\
    --verbose \\
    --to md \\
    --image-export-mode placeholder \\
    --pipeline standard \\
    --ocr \\
    --no-force-ocr \\
    --ocr-engine easyocr \\
    --pdf-backend pypdfium2 \\
    --abort-on-error \\
    --verbose \\
    --num-threads 4 \\
    --device auto \\
  'example_input_docs/Act_135_of_1998_Insider_Trading_Act.pdf' 
"'

# file system #
alias file_sizes='du -ah . | sort -hr'

findfile() {
	# find files using an interactive file picker with fuzzy find #
	#   Example usage:
	#     $ findfile        # just lists selected filepaths (can pipe to something else)
	#     $ findfile ~/nvim-linux64/bin/nvim   # open selected files with neovim

	local open_command="$1"
	local filepaths=()

	readarray -t filepaths < <(fd --type f | fzf --multi --preview 'bat --style=numbers --color=always {}') || return

	# exit if no files selected #
	[[ ${#filepaths[@]} -eq 0 ]] && return

	if [[ -n "$open_command" ]]; then
		"$open_command" "${filepaths[@]}"
	else
		printf '%s\n' "${filepaths[@]}"
	fi
}

alias find_helper='echo "
  # find file or directory using substring of its name #
  # \".\" is current directory. 
  # \"*\" is wildcard meaning \"match any number of characters of anything\"
  find . -name \"*substring_here*\" 

  # find only files #
  find . -type f -name \"*substring_here*\"

  # find only directories #
  find . -type d -name \"*substring_here*\"

  # ignore a directory #
  find . -path ./.venv -prune -o -type f -name \"*.json\"   # find all json files but dont look in .venv
"'
alias folder_size='du --human-readable --summarize'

alias grep_helper='echo "
  # search all files recursively for specified substring #
  # -r means recursive (not only current directory, but also subdirectories)
  # \".\" is current directory. 
  # --include is a pattern match on the filenames (default is no filter)
  # default grep (same as -e) is not regex, but interprets {[(|+ etc. symbols literally
  grep -r --include=\"*.py\" --exclude-dir={.venv,__pycache__,.ruff_cache} \"[my-substring\)\" .

  # -P treats the search pattern as proper Perl-compatible regex #
  # i.e. interprets {[(|+ etc. in the regex way
  grep -rP --include=\"*.py\" \"\d+\" .

  # only return names of matching files #
  grep -rPl --include=\"*.py\" \"\d+\" . 
"'

jq_helper() {
	cat <<EOF

  # basic JSONL usage #
  jq . myfile.jsonl         # or 'cat myfile.jsonl | jq .'

  # filter out records #
  jq 'select(.request.chat_id == 69420)' llm_logs.jsonl      # for a string, must use "" e.g. 'select(.request.chat_id == "a-string")'

  # random sample of records #
  shuf -n 3 logs.jsonl | jq .

  # select only specific fields #
  # (I'm building good-looking JSON here) #
  jq '{usage_description: .request.usage_description, token_usage: .response.API_response.usage}' llm_logs.jsonl

  # show JSONL entries where request.metadata.doc_name contains 'qlink' (case insensitive) #
  jq 'select(.request.metadata.doc_name | test("QLink"; "i"))' myfile.jsonl

  # same as above but with scrolling and nice terminal colours #
  jq -C 'select(.request.metadata.doc_name | test("QLink"; "i"))' myfile.jsonl | less -R

  # get correct colours when using \`less\` #
  jq -C . myfile.jsonl | less -R

  # everything flat with \n characters rendered #
  # (so can read values in the JSON with a lot of newlines in them) #
  jq -r 'paths(scalars) as \$p | "\(\$p | join(".")): \(getpath(\$p))"' myfile.jsonl | less
  # same as above but alternative syntax #
  cat myfile.jsonl | jq -r 'paths(scalars) as \$p | "\(\$p | join(".")): \(getpath(\$p))"' | less

  # group by and sum #
  jq -s '
    group_by(.request.usage_description) |
    map({
      usage_description: .[0].request.usage_description,
      total_prompt_tokens: (map(.response.API_response.usage.prompt_tokens) | add),
      total_completion_tokens: (map(.response.API_response.usage.completion_tokens) | add)
    })
  ' llm_logs.jsonl

EOF
}

alias l1='ls -a1'
alias ll='ls -lah'
alias lls="ls -lahS"
alias lsd="ls -d */" # list only directories
pwdc() {
	if uname -r | grep -q "WSL"; then
		pwd | clip.exe
	else
		echo "platform not supported"
	fi
}

zip_helper() {
	cat <<EOF
  # add files to zip file #
  zip my_archive.zip file1 file2 file3

  # add entire folder (and subfolders) to zip file #
  zip -r my_archive.zip folder_name

  # unzip #
  unzip my_archive.zip -d /path/to/destination # omit -d part for unzip to current dir
EOF
}

# paste from clipboard after removing windows carriage returns #
alias wslpaste='powershell.exe Get-Clipboard | sed "s/\r$//" | xargs -0 printf "%s"'

savepath() {
	# save current directory path to memory (under provided name)
	if [ -z "$1" ]; then
		echo "Usage: savepath <name>"
		return 1
	fi
	local savename="SAVEDPATH_${1}"
	echo "saving path $(pwd) to environment variable ${savename}"
	export $savename=$(pwd)
}
listpath() {
	echo 'listing saved paths (i.e. variables in ENV with prefix SAVEDPATH_)'
	env | grep 'SAVEDPATH_' | cut -c 11-
}
getpath() {
	if [ -z "$1" ]; then
		echo "Usage: getpath <name>"
		return 1
	fi
	local savedpath=$(env | grep "SAVEDPATH_$1=" | sed "s:^.*=::")
	echo "navigating to ${savedpath}"
	cd $(echo $savedpath)
}
delpath() {
	if [ -z "$1" ]; then
		echo "Usage: delpath <name>"
		return 1
	fi
	echo "Removing saved path $1"
	unset SAVEDPATH_$1
}

rmaf() {
	# delete all instances of file with this name (also looks in all subdirectories)
	find . -type f -name "${1}" -exec rm -f '{}' +
}
rmad() {
	# delete all instances of directory with this name (also looks in all subdirectories)
	find . -type d -name "${1}" -exec rm -rf {} \;
}

# git #
alias czc='cz commit'
alias ga="git add"
alias ga.="git add ."
alias gb="git branch"
alias gch="git checkout"
alias gd="git diff"
alias gdn="git diff --name-only"
alias git_verbose='GIT_CURL_VERBOSE=1 GIT_TRACE=1' # e.g. git_verbose git status
alias gp="git push"
alias gpom="git pull origin main --no-rebase"
alias grs="git restore --staged"
alias grs.="git restore --staged ."
alias gst="git status"
git_helper() {
	# examples of useful git workflows #
	cat <<EOF
  
  # show all changes between 2 different branches (including committed) #
  git diff other-branch-name # compare current branch to other branch
  git diff other-branch-name -- path/to/specific/folder/or/file # limit to changes in specific folder/files(s)
  git diff --stat other-branch-name # changed file names only (not changed file contents)
  # all of the above also work specifying both branch names
  #   example: git diff --stat main..feature-branch-name
  git diff --shortstat other-branch-name # just count of line changes

  # I just did a git pull origin main and I wish that I hadn't #
  git merge --abort

  # get latest state of main, resolving merge conflicts in favour of main #
  git pull -X theirs origin main

  # see a file state in a specific commit
  git log   # to see the commit history
  git show 1aCOMMITHASHHERE0j:path/to/file.txt   # for a specific commit hash
  git show HEAD~2:path/to/file.txt    # 2 commits ago

  # see a file state on a different branch #
  git show branch_name:path/to/file.ini

  # I committed and I want to "uncommit" and unstage #
  #   (e.g. I committed on the wrong branch)
  git reset --soft HEAD~1
  git checkout -b my-feature-branch-name  # can now go commit on this other branch or whatever

  # authenticate to github using a token #
  git remote remove origin
  git remote add origin https://[YOUR-TOKEN]@github.com/[REPO-OWNER]/[REPO-NAME] # i.e. just the repo URL, but with the token in it

  # discard local changes to a (tracked) file
  git restore --staged path/to/file   # if file is staged
  git restore path/to/file            # discard
  git restore .                       # get state of all tracked files at last commit
EOF
}

git_worktree_helper() {
	cat <<EOF
  # for a more thorough example, see: https://github.com/J-sephB-lt-n/Git-worktree-example
  
  # update all local views of remote (or git fetch origin <branch name>) 
  git fetch origin 

  # assuming I'm in the root of my git repo /myrepo/
  git worktree add \    # make a copy of my repo
    -b quick-fix \      # check out in the copy to a new branch called 'quick-fix'
    ../myrepo_git_worktrees/a-quick-fix \ # save the copy outside of my repo folder (1 level up) with folders named whatever I like
    origin/main         # make the copy contents match remote main branch (can choose other branch)

  git worktree list     # see that it's been created

  # navigate to the worktree (repo copy)
  cd ../myrepo_git_worktrees/a-quick-fix
  <make whatever changes you want>
  git add .
  git commit -m "..."
  git push            # can now PR my changes into main

  # I can now just delete the (temporary) 'quick-fix' worktree:
  cd ../../myrepo     # go back to my main repo
  git worktree list   # get the path of the worktree I want to delete
  git worktree remove <absolute path to worktree to delete>

EOF
}

google_search() {
	if [ "$#" -ne 2 ]; then
		echo "Usage: google_search <URL> <format>"
		echo 'Examples:'
		echo ' $ google_search "my query" html'
		echo ' $ google_search "my query" lynx-browser-view'
		echo ' $ google_search "my query" python-bs4'
		return 1
	fi
	local search_query=$(printf '%s' "$1" | jq -sRr @uri)
	local output_format=$2
	local url="https://www.google.com/search?q=${search_query}"
	if [ "$output_format" == "html" ]; then
		lynx -dump -source $url
	elif [ "$output_format" == "lynx-browser-view" ]; then
		lynx -dump $url
	elif [ "$output_format" == "python-bs4" ]; then
		lynx -dump -source $url | python3 -c '
import json
import sys
from urllib.parse import urlparse

import bs4

soup = bs4.BeautifulSoup(sys.stdin.read(), "html.parser")

urls_already_seen: set[str] = set()
search_results: list[dict] = []
for div in soup.find_all("div"):
    a_tags = div.find_all("a")
    if len(a_tags)==0 or not all(hasattr(a_tag, "href") for a_tag in a_tags):
        continue
    non_google_a_tags = [a_tag for a_tag in a_tags if "google.com" not in a_tag["href"]]
    clean_non_google_urls: list[str] = [
        a_tag["href"].replace("/url?q=", "").split("&")[0] for a_tag in non_google_a_tags
    ]
    clean_non_google_urls = [url for url in clean_non_google_urls if url[:4]=="http"]
    url_domains: list[str] = [urlparse(url).netloc for url in clean_non_google_urls]
    if not len(set(url_domains)) == 1:
        continue
    clean_url: str = clean_non_google_urls[0] 
    if clean_url not in urls_already_seen:
        urls_already_seen.add(clean_url)
        search_results.append(
            {
                "url": clean_url,
                "preview_text": "  ".join(div.stripped_strings),
            }
        )

print(
  json.dumps(
    search_results, 
    indent=4
  )
)'
	else
		echo "output format '$output_format' not supported"
	fi
}

# misc #
timer() {
	# example usage: timer && sleep 5 && timer
	if [[ -z "${TIMER_START}" ]]; then
		export TIMER_START=$EPOCHREALTIME
	else
		local seconds_elapsed=$(echo "$EPOCHREALTIME - $TIMER_START" | bc)
		local minutes_elapsed=$(echo "scale=2; $seconds_elapsed / 60" | bc)
		echo "total time elapsed in minutes: $minutes_elapsed"
		echo "total time elapsed in seconds: $seconds_elapsed"
		unset TIMER_START
	fi
}

# navigation #
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'
alias .....='cd ../../../..'
alias ......='cd ../../../../..'

# networking
checkcert() {
	# e.g. checkcert www.google.com
	# this function from: https://stackoverflow.com/questions/21181231/server-certificate-verification-failed-cafile-etc-ssl-certs-ca-certificates-c/67698986#67698986
	echo -n |
		openssl s_client -showcerts -servername $1 \
			-connect $1:443 2>/dev/null |
		tac |
		awk '/-END CERTIFICATE-/{f=1} f;/-BEGIN CERTIFICATE-/{exit}' |
		tac |
		openssl x509 -noout -subject -issuer
}

# PDF files #
pdf_helper() {
	cat <<EOF

  sudo apt install pdftk
  
  # Get a subset of pages of a PDF (this discards the Table of Contents) #
  pdftk input.pdf cat 2-5 output output.pdf
  pdftk input.pdf cat 1 3-9 15 18-19 output output.pdf
  
  # extract PDF text (using poppler-utils) #
  pdftotext -enc UTF-8 -eol unix -nopgbrk -layout input.pdf output.txt

  # Get a subset of pages of a PDF                                #
  # (this keeps the full Table of Contents - even deleted pages)  #
  qpdf input.pdf --pages . 2-5 -- output.pdf

EOF
}

# python #
alias pri='poetry run ipython'
alias uri='uv run ipython'
uvrn() {
	# e.g. uvrn 3.13 python -m venv .venv
	uv run --no-project --python "${1}" "${@:2}"
}
alias urrf='uv run ruff format'

# screen management #
alias cl='clear'
alias cll="clear && ls -lah"
alias clct='clear && tree -C -a -I .git -I .mypy_cache -I .pytest_cache -I .ruff_cache -I .venv -I __pycache__ -I node_modules -I target -I venv'

# task warrior #
task_warrior_helper() {
	cat <<EOF
  task add Task Description Here
  task ID done

  # project #
  task ID modify project:Project-Name-Here
  task add project:Project-Name-Here
  
  # due date #
  task ID modify due:2069-04-20
  task ID modify due:tomorrow
  task ID modify due:next Monday
  task ID modify due:3days
  task ID modify due:2weeks
  task ID modify due:2069-04-20T17:00Z  # 5pm UTC (omit Z for local time)

  # mark active/inactive #
  task ID start   # set active
  task ID stop    # set inactive

  # priority #
  task ID modify priority:M    # by default, values are L, M, H

  # tags #
  task ID modify +tag1 +tag2

  # dependencies #
  task ID modify depends:OTHER_ID   # i.e. task OTHER_ID is blocking task ID

  # reports #
  task active # Started tasks
  task all # Pending, completed and deleted tasks
  task blocked # Tasks that are blocked by other tasks
  task blocking # Tasks that block other tasks
  task completed # Tasks that have been completed
  task list # Pending tasks
  task long # Pending tasks, long form
  task ls # Pending tasks, short form
  task minimal # Pending tasks, minimal form
  task newest # Most recent pending tasks
  task next # Most urgent tasks
  task oldest # Oldest pending tasks
  task overdue # Overdue tasks
  task ready # Pending, unblocked, scheduled tasks
  task recurring # Pending recurring tasks
  task unblocked # Tasks that are not blocked
  task waiting # Hidden, waiting tasks
EOF
}

function list_llms() {
	# list all models using /v1/models endpoint of an openai-compatible API
	if [[ -z "$OPENAI_BASE_URL" ]]; then
		echo "Error: OPENAI_BASE_URL environment variable is not set." >&2
		return 1
	fi

	# Strip trailing slash
	local base_url="${OPENAI_BASE_URL%/}"

	if [[ -z "$OPENAI_API_KEY" ]]; then
		echo "Error: OPENAI_API_KEY environment variable is not set." >&2
		return 1
	fi

	local response
	if ! response=$(curl -s -w "%{http_code}" \
		-H "Authorization: Bearer $OPENAI_API_KEY" \
		"$base_url/v1/models"); then
		echo "Error: Failed to connect to $base_url/v1/models" >&2
		return 1
	fi

	local http_code="${response: -3}"
	local body="${response%???}"

	if [[ "$http_code" -ne 200 ]]; then
		echo "Error: HTTP $http_code" >&2
		echo "$body" >&2
		return 1
	fi

	# Parse and print each model ID
	echo "$body" | jq -r '.data[].id' | sort
}

llm_chat_completion_helper() {
	cat <<EOT
  # Example usage of llm_chat_completion() function #

  llm_chat_completion "Tell me something interesting"

  # Question answering for a single text file #
  echo "<doc>\$(cat myfile.txt)</doc> Please summarise the contents of doc" | llm_chat_completion

  # Question answering over multiple text files #
  #   (use cat or less instead of llm_chat_completion to see the prompt)
  llm_chat_completion <<EOF
    Please summarise what these scripts are doing:
    <scripts>
    \$(findfile | file_contents_to_md)
    </scripts>
    EOF
EOT
}

llm_chat_completion() {
	# Example usage:
	#   llm_chat_completion "Tell me something interesting"
	#   echo "<doc>$(cat myfile.txt)</doc> Please summarise the contents of doc" | llm_chat_completion
	#   for more examples, run `llm_chat_completion_helper`

	: "${OPENAI_BASE_URL:?Error: OPENAI_BASE_URL environment variable is not set}"
	: "${OPENAI_API_KEY:?Error: OPENAI_API_KEY environment variable is not set}"
	: "${OPENAI_DEFAULT_MODEL:?Error: OPENAI_DEFAULT_MODEL environment variable is not set}"

	echo "using model [${OPENAI_DEFAULT_MODEL}]"

	local prompt line

	if [ $# -gt 0 ]; then
		prompt="$*"
	else
		prompt="$(cat)"
	fi

	# OpenAI-compatible streaming request
	curl -sN "${OPENAI_BASE_URL}/v1/chat/completions" \
		-H "Authorization: Bearer ${OPENAI_API_KEY}" \
		-H "Content-Type: application/json" \
		-d "$(jq -n \
			--arg model "$OPENAI_DEFAULT_MODEL" \
			--arg content "$prompt" \
			'{model:$model,messages:[{role:"user",content:$content}],stream:true}')" |
		sed 's/^data: //' |
		while IFS= read -r line; do
			[[ $line == "[DONE]" ]] && break # skip sentinel
			jq -rj '.choices[0].delta.content // empty' <<<"$line"
		done
	printf '\n'
}

file_contents_to_md() {
	# accepts a list of filepaths and dumps file contents into a single markdown string
	# Example usage:
	#   findfile | file_contents_to_md | less    # or cat
	local file
	while IFS= read -r file; do
		# Skip empty lines
		[[ -z "$file" ]] && continue

		# If the file doesn't exist or isn't readable, warn and skip
		if [[ ! -r "$file" ]]; then
			echo "# $file" >&2
			echo "⚠️ Cannot read file: $file" >&2
			continue
		fi

		# Print the header, code fence, contents, and closing fence
		printf '# %s\n' "$file"
		printf '```\n'
		cat "$file"
		printf '```\n\n'
	done
}

postgres_helper() {
	# useful CLI commands related to postgreSQL #
	cat <<EOF

  # postgres+pgvector ephemeral local container #
  docker run \\
      -d \\                  # run detached
      --name ephemeral_pgvector \\
      -e POSTGRES_USER=postgres \\  
      -e POSTGRES_PASSWORD=password \\
      -e POSTGRES_DB=pg_db \\
      -p 11636:5432 \\
      pgvector/pgvector:pg17

    psql -h localhost -U postgres -d pg_db --port 11636  # shell for running queries in
    # run \`\\x auto\` in psql shell to make output readable for wide tables

    uv tool install harlequin[postgres]
    uvx harlequin --adapter postgres postgresql://postgres:password@localhost:11636/pg_db
  
EOF
}

prompt_format() {
	# example structure for a LLM prompt #
	cat <<EOF

  Task: describe what is required.
  Input: what are the inputs to the task (e.g. multiple CSV files, all same columns)
  Constraints: describe the limits
  Output: describe required output format
  Verify: describe how to verify that the proposed solution works
  
EOF
}

# TASK TIMER #
# timer state is stored in /var/tmp/task_timers/
if [[ ! -e /var/tmp/task_timers/ ]]; then
	echo "creating directory /var/tmp/task_timers/"
	mkdir /var/tmp/task_timers/
fi
seconds_to_human_readable() {
	# from https://unix.stackexchange.com/questions/27013/displaying-seconds-as-days-hours-mins-seconds
	local T=$(awk -v num=$1 'BEGIN {printf "%.0f", num}')
	local D=$((T / 60 / 60 / 24))
	local H=$((T / 60 / 60 % 24))
	local M=$((T / 60 % 60))
	local S=$((T % 60))
	(($D > 0)) && printf '%d days ' $D
	(($H > 0)) && printf '%d hours ' $H
	(($M > 0)) && printf '%d minutes ' $M
	(($D > 0 || $H > 0 || $M > 0))
	printf '%d seconds\n' $S
}
tmr_go() { # start specific timer
	# e.g. tmr_go task1
	local timer_description=$2
	if [[ $timer_description == *"|"* ]]; then
		echo "ERROR: timer description may not contain pipe symbol"
		return 0
	fi
	if [[ -z "${timer_description}" ]]; then
		local timer_description="no_description"
	fi
	if [[ ! -f /var/tmp/task_timers/$1.tmr ]]; then
		echo -n "${timer_description}|${EPOCHREALTIME}" >/var/tmp/task_timers/$1.tmr
		echo "started timer [$1]"
	else
		local latest_entry=$(tail -n 1 /var/tmp/task_timers/$1.tmr)
		local n_entries=$(echo $latest_entry | awk -F '|' '{print NF}')
		#n_entries=$(awk "{print NF}" <<< "$latest_entry")
		if [[ n_entries -eq 2 ]]; then
			echo "timer [$1] is already running"
		else
			echo -n "${timer_description}|${EPOCHREALTIME}" >>/var/tmp/task_timers/$1.tmr
			echo "started timer [$1]"
		fi
	fi
}
tmr_stop() { # stop specific timer
	# e.g. tmr_stop task1
	if [[ ! -f /var/tmp/task_timers/$1.tmr ]]; then
		echo "timer [$1] does not exist"
	else
		local latest_entry=$(tail -n 1 /var/tmp/task_timers/$1.tmr)
		local n_entries=$(echo $latest_entry | awk -F '|' '{print NF}')
		if [[ $n_entries -eq 2 ]]; then
			echo "|${EPOCHREALTIME}" >>/var/tmp/task_timers/$1.tmr
			echo "stopped timer [$1]"
		else
			echo "timer [$1] is already stopped"
		fi
	fi
}
tmr_view() { # view specific timer
	# e.g. tmr_view task1
	if [[ ! -f /var/tmp/task_timers/$1.tmr ]]; then
		echo "timer [$1] does not exist"
	else
		echo ""
		echo "--Summary of Timer [$1]--"
		echo ""
		local total_n_seconds=0
		while read line || [[ -n $line ]]; do
			n_entries=$(echo $line | awk -F '|' '{print NF}')
			if [[ $n_entries -eq 3 ]]; then
				timer_description=$(echo $line | cut -d "|" -f 1)
				start_utc=$(echo $line | cut -d "|" -f 2)
				end_utc=$(echo $line | cut -d "|" -f 3)
				echo -n "* ["$(perl -le 'print scalar localtime $ARGV[0]' $start_utc)"]"
				echo -n " --> "
				echo "["$(perl -le 'print scalar localtime $ARGV[0]' $end_utc)"]"
				if [[ $timer_description != "no_description" ]]; then
					echo "       \"${timer_description}\""
				else
					echo "       <no timer description>"
				fi
				n_seconds=$(echo "($end_utc - $start_utc)/1" | bc)
				total_n_seconds=$(echo "$total_n_seconds + $n_seconds" | bc)
				echo -n "       ("
				echo -n $(seconds_to_human_readable ${n_seconds})
				echo ")"
			else
				timer_description=$(echo $line | cut -d "|" -f 1)
				start_utc=$(echo $line | cut -d "|" -f 2)
				end_utc=$EPOCHREALTIME
				echo -n "* ["$(perl -le 'print scalar localtime $ARGV[0]' $start_utc)"]"
				echo -n " --> "
				echo "<currently running>"
				if [[ $timer_description != "no_description" ]]; then
					echo "       \"${timer_description}\""
				else
					echo "       <no timer description>"
				fi
				n_seconds=$(echo "($end_utc - $start_utc)/1" | bc)
				total_n_seconds=$(echo "$total_n_seconds + $n_seconds" | bc)
				echo -n "       ("
				echo -n $(seconds_to_human_readable ${n_seconds})
				echo ")"
			fi
		done <<<$(cat /var/tmp/task_timers/$1.tmr)
		echo ""
		echo "TOTAL TIME: "$(seconds_to_human_readable ${total_n_seconds})
	fi
}
tmr_ls() { # list all timers
	echo "--ALL TIMERS--"
	n_timers=$(find /var/tmp/task_timers/ -type f -name "*.tmr" | wc -l)
	if [[ $n_timers -eq 0 ]]; then
		echo "There are no timers"
	else
		for timer_filepath in /var/tmp/task_timers/*.tmr; do
			timer_name=$(echo $timer_filepath | sed "s/\/var\/tmp\/task_timers\/\(.*\).tmr$/\1/")
			latest_entry=$(tail -n 1 $timer_filepath)
			n_entries=$(echo $latest_entry | awk -F '|' '{print NF}')
			if [[ $n_entries -eq 2 ]]; then
				echo "[$timer_name] <currently running>"
			else
				echo "[$timer_name]"
			fi
		done
	fi
}
tmr_delete() {
	# e.g. tmr_delete task1
	if [[ ! -f /var/tmp/task_timers/$1.tmr ]]; then
		echo "timer [$1] does not exist"
	else
		rm /var/tmp/task_timers/$1.tmr
		echo "deleted timer [$1]"
	fi
}
