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

# file system #
alias find_helper='echo "
  # find anything using substring of the name #
  # \".\" is current directory. 
  # \"*\" is wildcard meaning \"match anything\"
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
