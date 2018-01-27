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
	curl \
		-X DELETE "https://api.cloudflare.com/client/v4/zones/${CLOUDFLARE_ZONE}/purge_cache" \
	 	-H "X-Auth-Email: ${CLOUDFLARE_EMAIL}" \
		-H "X-Auth-Key: ${CLOUDFLARE_APIKEY}" \
		-H "Content-Type: application/json" \
		--data '{"purge_everything":true}'

