# code linting #
alias poetry_run_pylint_recursive='poetry run pylint --rcfile .pylintrc --recursive=y .'

# docker #
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

  # select only specific fields #
  # (I'm building good-looking JSON here) #
  jq '{usage_description: .request.usage_description, token_usage: .response.API_response.usage}' myfile.jsonl

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
  
  # Get a subset of pages of a PDF #
  pdftk input.pdf cat 2-5 output output.pdf
  pdftk input.pdf cat 1 3-9 15 18-19 output output.pdf
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
alias clct='clear && tree -a -I .git -I .mypy_cache -I .pytest_cache -I .ruff_cache -I .venv -I __pycache__ -I node_modules -I target -I venv'

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
	if [[ -z "$OPENAI_API_BASE" ]]; then
		echo "Error: OPENAI_API_BASE environment variable is not set." >&2
		return 1
	fi

	# Strip trailing slash
	local base_url="${OPENAI_API_BASE%/}"

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

	: "${OPENAI_API_BASE:?Error: OPENAI_API_BASE environment variable is not set}"
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
	curl -sN "${OPENAI_API_BASE}/v1/chat/completions" \
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
