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

# file system #
alias find_helper='echo "
  # find file or directory using substring of its name #
  # \".\" is current directory. 
  # \"*\" is wildcard meaning \"match any number of characters of anything\"
  find . -name \"*substring_here*\" 

  # find only files #
  find . -type f -name \"*substring_here*\"

  # find only directories #
  find . -type d -name \"*substring_here*\"
"'
alias folder_size='du --human-readable --summarize'
alias grep_helper='echo "
  # search all files recursively for specified substring #
  # -r means recursive (not only current directory, but also subdirectories)
  # \".\" is current directory. 
  # --include is a pattern match on the filenames (default is no filter)
  # default grep (same as -e) is not regex, but interprets {[(|+ etc. symbols literally
  grep -r --include=\"*.py\" \"[my-substring\)\" .

  # -P treats the search pattern as proper Perl-compatible regex #
  # i.e. interprets {[(|+ etc. in the regex way
  grep -rP --include=\"*.py\" \"\d+\" .

  # only return names of matching files #
  grep -rPl --include=\"*.py\" \"\d+\" . 
"'
#alias ll='ls -lah'
alias lls="ls -lahS"
alias lsd="ls -d */" # list only directories
pwdc() {
    if uname -r | grep -q "WSL"; then
        pwd | clip.exe
    else
        echo "platform not supported"
    fi
}

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
  git pull -X theirs origin/main

  # authenticate to github using a token #
  git remote remove origin
  git remote add origin https://[YOUR-TOKEN]@github.com/[REPO-OWNER]/[REPO-NAME] # i.e. just the repo URL, but with the token in it
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

# python #
alias pri='poetry run ipython'
uvrn() {
	# e.g. uvrn 3.13 python -m venv .venv
	uv run --no-project --python "${1}" "${@:2}"
}
alias urrf='uv run ruff format'


# screen management #
alias cl='clear'
alias cll="clear && ls -lah"
alias clct='clear && tree -a -I .git -I .mypy_cache -I .pytest_cache -I .ruff_cache -I .venv -I __pycache__ -I node_modules -I target -I venv'

