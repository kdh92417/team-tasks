## 백엔드 어플리케이션 실행

```commandline
docker-compose up
```

## 테스트 실행

```sh
# 도커 컴포즈 실행 후
docker exec -it backend /bin/bash
python manage.py test app.tests.test_task
```


## Swagger API Docs

- Swagger API Docs : /docs
![](https://github.com/kdh92417/team-tasks/assets/58774316/ece9487f-620a-40fd-afd2-2a5fbf93bc7d)
