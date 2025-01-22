# code linting #
alias poetry_run_pylint_recursive='poetry run pylint --rcfile .pylintrc --recursive=y .'

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
#alias ll='ls -lah'
alias lls="ls -lahS"
alias lsd="ls -d */" # list only directories

# quick folder navigation using explicit path cache #
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

# navigation #
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# screen management #
alias cl='clear'
alias cll="clear && ls -lah"
alias clct='clear && tree -a -I .git -I .mypy_cache -I .pytest_cache -I .ruff_cache -I .venv -I __pycache__ -I node_modules -I target -I venv'

# python uv #
uvrn() {
	# e.g. uvrn 3.13 python -m venv .venv
	uv run --no-project --python "${1}" "${@:2}"
}
alias urrf='uv run ruff format'

rmaf() {
	# delete all instances of file with this name (also looks in all subdirectories)
	find . -type f -name "${1}" -exec rm -f '{}' +
}
rmad() {
	# delete all instances of directory with this name (also looks in all subdirectories)
	find . -type d -name "${1}" -exec rm -rf {} \;
}
