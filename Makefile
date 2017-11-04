deps:
	brew install pipenv
	pipenv update
db:
	redis-cli < events.redis
	pipenv run flushall.py
	pipenv run refresh.py
production:
	git fetch
	git reset --hard origin/master
	pipenv run supervisorctl reload
