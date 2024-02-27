# Возможности

Можно использовать только для регистрации/логина LinkedIn и регистрации ботов для OK и Twitter

___

# Использование

## Скачивание библиотек

В случае если проект только склонирован и виртуальное окружение уже настроенно введите данную команду: 

```commandline
pip install -r requirements.txt
```
<br />

## Регистрация и логин LinkedIn

Для регистрации ботов необходимо использовать данный код в `main`:
```pycon
client = APIClient(configs.access_token_payload)

dynamic_proxies = client.get_proxies(params=configs.dynamic_proxy_params)

for proxy in dynamic_proxies:
    email = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8)) + '@1secmail.com'

    if not proxy:
        dynamic_proxies = client.get_proxies(params=configs.dynamic_proxy_params)
        continue

    bot = LinkedInBot(client, proxy=proxy)
    bot.create_new_token(email)
```

Для логина используем данный код:
```pycon
client = APIClient(configs.access_token_payload)

tokens = client.get_tokens(configs.linkedin_tokens_params)
static_proxies = client.get_proxies(configs.us_proxy_params)

for token, proxy in itertools.zip_longest(tokens, static_proxies):
    bot = LinkedInBot(client, token, proxy)
    bot.update_token_to_active()
```

## Внимание

- Код не закончен поэтому возможны ошибки в работе! К примеру, при прохождении CAPTCHA в консоли будет спрашиваться нажать `Enter`, чтобы продолжить регистрацию, <b>НАЖАТЬ НУЖНО ТОЛЬКО ОДИН РАЗ</b>, при нескольких нажатиях следующая регистрация не будет ждать прохождения.
- Не все ситуации учтены при логине пользователя, а именно, при возникновении данного окна, необходимо <b>НЕЗАМЕДЛИТЕЛЬНО НАЖАТЬ</b> `Я буду следовать правилам`, или кнопку с подобной написью, далее она автоматически продолжит работу.
![example](./img/example.jpeg)
- Недавно было выявлена данная проблема (ниже скришотом), при регистрации возникает данная ошибка. На момент написания этой документации точные причины и решения не найдены. В случае ее возникновления возможно написать в консоли `skip`, в этом случае начнется следующая регистрация, или же иногда помогает перезагрузка страницы и введения данных до CAPTCHA, и повторная попытка ее прохождения.
![error](./img/error.jpeg)
- В случае если при регистрации запрашивается номер телефона, ничего не необходимо делать, скрипт самостоятельно начнет новую регистрацию.
- При возникновлении ошибки или если скприт завис на долгое время необходимо самостоятельно закончить регистрацию/логин и добавить/обновить токен в <i>Avatar</i>.
- В любых других ситуациях необходима перезагрузка скрипта

# Контакт
В случае возникновления вопрос:
* Telegram - @Ecl1ps0
