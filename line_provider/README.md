### Шаблон сервиса line-provider

```
docker build . -t line_provider_image:latest
docker run -p 8080:8080 --name line_provider_container line_provider_image:latest
```

Then visit http://localhost:8080/docs
