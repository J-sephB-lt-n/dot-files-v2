checkcert() {
	# e.g. checkcert www.github.com
	# this function from: https://stackoverflow.com/questions/21181231/server-certificate-verification-failed-cafile-etc-ssl-certs-ca-certificates-c/67698986#67698986
	echo -n |
		openssl s_client -showcerts -servername www.github.com \
			-connect www.github.com:443 2>/dev/null |
		tac |
		awk '/-END CERTIFICATE-/{f=1} f;/-BEGIN CERTIFICATE-/{exit}' |
		tac |
		openssl x509 -noout -subject -issuer
}
