# For Docker and OSX development
up:
	curl -o /usr/local/bin/docker-osx-dev https://raw.githubusercontent.com/brikis98/docker-osx-dev/master/src/docker-osx-dev
	chmod +x /usr/local/bin/docker-osx-dev
	docker-osx-dev install
	docker-osx-dev -m default -s ./ --ignore-file '.rsync-ignore'
