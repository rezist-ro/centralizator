deps:
	pipenv update
	npm install
db:
	redis-cli < events.redis
	pipenv run python flushall.py
	pipenv run python refresh.py
production:
	git fetch
	git reset --hard origin/master
	make deps
	pipenv run supervisorctl reread
	pipenv run supervisorctl restart all
